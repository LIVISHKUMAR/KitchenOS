from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import uuid
from app.api.dependencies import get_current_user
from app.infrastructure.database import get_db_session
from app.models import Order, OrderItem, Payment

router = APIRouter()


class SplitRequest(BaseModel):
    order_id: str
    split_type: str  # by_item, equal, custom
    item_splits: Optional[List[dict]] = None  # For by_item: [{item_ids: [], payment_method: ""}]
    num_splits: Optional[int] = None  # For equal split
    custom_amounts: Optional[List[dict]] = None  # For custom: [{amount, payment_method}]


@router.post("/create")
async def create_split(
    data: SplitRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Create split bills for an order."""
    order = db.query(Order).filter(Order.id == data.order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if str(order.tenant_id) != current_user["tenant_id"]:
        raise HTTPException(status_code=403, detail="Access denied")

    items = db.query(OrderItem).filter(OrderItem.order_id == data.order_id).all()

    splits = []

    if data.split_type == "by_item":
        if not data.item_splits:
            raise HTTPException(status_code=400, detail="item_splits required for by_item split")

        for split_group in data.item_splits:
            split_item_ids = split_group.get("item_ids", [])
            split_items = [i for i in items if str(i.id) in split_item_ids]
            split_total = sum(float(i.total) for i in split_items)
            split_tax = sum(float(i.tax_amount) for i in split_items)

            splits.append({
                "id": str(uuid.uuid4()),
                "items": [{"id": str(i.id), "name": i.item_name, "total": float(i.total)} for i in split_items],
                "subtotal": split_total,
                "tax": split_tax,
                "total": split_total + split_tax,
                "payment_method": split_group.get("payment_method", "cash")
            })

    elif data.split_type == "equal":
        num = data.num_splits or 2
        total_per_split = float(order.total) / num

        for i in range(num):
            splits.append({
                "id": str(uuid.uuid4()),
                "items": [{"id": str(it.id), "name": it.item_name, "total": float(it.total)} for it in items],
                "subtotal": float(order.subtotal) / num,
                "tax": float(order.tax_amount) / num,
                "total": round(total_per_split, 2),
                "payment_method": "cash"
            })

    elif data.split_type == "custom":
        if not data.custom_amounts:
            raise HTTPException(status_code=400, detail="custom_amounts required for custom split")

        for custom in data.custom_amounts:
            splits.append({
                "id": str(uuid.uuid4()),
                "items": [],
                "subtotal": custom.get("amount", 0),
                "tax": 0,
                "total": custom.get("amount", 0),
                "payment_method": custom.get("payment_method", "cash")
            })

    else:
        raise HTTPException(status_code=400, detail="Invalid split_type. Must be by_item, equal, or custom")

    # Validate total matches
    split_total = sum(s["total"] for s in splits)
    if abs(split_total - float(order.total)) > 0.01:
        raise HTTPException(
            status_code=400,
            detail=f"Split total ({split_total:.2f}) does not match order total ({float(order.total):.2f})"
        )

    return {
        "order_id": data.order_id,
        "order_total": float(order.total),
        "split_type": data.split_type,
        "num_splits": len(splits),
        "splits": splits
    }


@router.post("/pay-split")
async def pay_split(
    order_id: str,
    split_id: str,
    amount: float,
    payment_method: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Process payment for one split of a split bill."""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if str(order.tenant_id) != current_user["tenant_id"]:
        raise HTTPException(status_code=403, detail="Access denied")

    payment = Payment(
        id=str(uuid.uuid4()),
        order_id=order_id,
        tenant_id=current_user["tenant_id"],
        branch_id=current_user.get("branch_id"),
        amount=amount,
        payment_method=payment_method,
        status="completed",
        idempotency_key=f"split-{split_id}",
        processed_at=datetime.utcnow(),
        created_at=datetime.utcnow()
    )
    db.add(payment)

    # Update order payment status
    existing_payments = db.query(Payment).filter(
        Payment.order_id == order_id,
        Payment.status == "completed"
    ).all()
    total_paid = sum(float(p.amount) for p in existing_payments) + amount

    if total_paid >= float(order.total):
        order.payment_status = "paid"
        order.status = "completed"
    else:
        order.payment_status = "partial"

    db.commit()

    return {
        "payment_id": str(payment.id),
        "amount": amount,
        "payment_method": payment_method,
        "total_paid": total_paid,
        "remaining": max(0, float(order.total) - total_paid),
        "order_payment_status": order.payment_status
    }
