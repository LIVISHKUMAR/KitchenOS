"""Aggregator integration endpoints (Swiggy/Zomato)."""

from fastapi import APIRouter, Depends, HTTPException, Request, Header
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel
from datetime import datetime
import uuid

from app.api.dependencies import get_current_user
from app.infrastructure.database import get_db_session
from app.models import Order, OrderItem, MenuItem, Tenant, Branch
from app.modules.aggregator.swiggy import swiggy, zomato

router = APIRouter()


@router.post("/swiggy/webhook")
async def swiggy_webhook(
    request: Request,
    x_swiggy_signature: Optional[str] = Header(None),
    db: Session = Depends(get_db_session)
):
    """Receive orders from Swiggy."""
    body = await request.body()

    # Verify signature
    if x_swiggy_signature and not swiggy.verify_webhook(body, x_swiggy_signature):
        raise HTTPException(status_code=401, detail="Invalid signature")

    import json
    data = json.loads(body)

    # Normalize order
    order_data = swiggy.normalize_order(data)

    # Find tenant/branch
    tenant = db.query(Tenant).filter(Tenant.is_active == True).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="No active tenant")

    branch = db.query(Branch).filter(
        Branch.tenant_id == tenant.id,
        Branch.is_active == True
    ).first()

    # Create order
    today = datetime.utcnow().strftime("%Y%m%d")
    count = db.query(Order).filter(Order.tenant_id == tenant.id).count()

    order = Order(
        id=str(uuid.uuid4()),
        order_number=f"SWG-{today}-{count + 1:04d}",
        tenant_id=tenant.id,
        branch_id=branch.id if branch else None,
        order_type="delivery",
        status="confirmed",
        customer_name=order_data.get("customer_name"),
        customer_phone=order_data.get("customer_phone"),
        subtotal=order_data.get("subtotal", 0),
        tax_amount=order_data.get("tax", 0),
        total=order_data.get("total", 0),
        source="swiggy",
        aggregator_order_id=order_data.get("aggregator_order_id"),
        delivery_address=order_data.get("delivery_address"),
        special_instructions=order_data.get("special_instructions"),
        payment_status="paid",
        created_at=datetime.utcnow()
    )
    db.add(order)

    for item_data in order_data.get("items", []):
        order_item = OrderItem(
            id=str(uuid.uuid4()),
            order_id=order.id,
            menu_item_id=item_data.get("menu_item_id", str(uuid.uuid4())),
            item_name=item_data.get("item_name", ""),
            quantity=item_data.get("quantity", 1),
            unit_price=item_data.get("unit_price", 0),
            total=item_data.get("quantity", 1) * item_data.get("unit_price", 0),
            modifiers=item_data.get("modifiers", []),
            prep_status="pending",
            created_at=datetime.utcnow()
        )
        db.add(order_item)

    db.commit()

    return {
        "order_id": str(order.id),
        "order_number": order.order_number,
        "status": "confirmed",
        "message": "Order received from Swiggy"
    }


@router.post("/zomato/webhook")
async def zomato_webhook(
    request: Request,
    db: Session = Depends(get_db_session)
):
    """Receive orders from Zomato."""
    import json
    data = await request.json()

    order_data = zomato.normalize_order(data)

    tenant = db.query(Tenant).filter(Tenant.is_active == True).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="No active tenant")

    branch = db.query(Branch).filter(
        Branch.tenant_id == tenant.id,
        Branch.is_active == True
    ).first()

    today = datetime.utcnow().strftime("%Y%m%d")
    count = db.query(Order).filter(Order.tenant_id == tenant.id).count()

    order = Order(
        id=str(uuid.uuid4()),
        order_number=f"ZMT-{today}-{count + 1:04d}",
        tenant_id=tenant.id,
        branch_id=branch.id if branch else None,
        order_type="delivery",
        status="confirmed",
        customer_name=order_data.get("customer_name"),
        customer_phone=order_data.get("customer_phone"),
        subtotal=order_data.get("subtotal", 0),
        tax_amount=order_data.get("tax", 0),
        total=order_data.get("total", 0),
        source="zomato",
        aggregator_order_id=order_data.get("aggregator_order_id"),
        delivery_address=order_data.get("delivery_address"),
        special_instructions=order_data.get("special_instructions"),
        payment_status="paid",
        created_at=datetime.utcnow()
    )
    db.add(order)

    for item_data in order_data.get("items", []):
        order_item = OrderItem(
            id=str(uuid.uuid4()),
            order_id=order.id,
            menu_item_id=item_data.get("menu_item_id", str(uuid.uuid4())),
            item_name=item_data.get("item_name", ""),
            quantity=item_data.get("quantity", 1),
            unit_price=item_data.get("unit_price", 0),
            total=item_data.get("quantity", 1) * item_data.get("unit_price", 0),
            modifiers=item_data.get("modifiers", []),
            prep_status="pending",
            created_at=datetime.utcnow()
        )
        db.add(order_item)

    db.commit()

    return {
        "order_id": str(order.id),
        "order_number": order.order_number,
        "status": "confirmed"
    }


@router.post("/update-status/{order_id}")
async def update_aggregator_status(
    order_id: str,
    new_status: str,
    estimated_time: Optional[int] = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Update order status and sync back to aggregator."""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    order.status = new_status
    db.commit()

    # Sync to aggregator
    result = None
    if order.source == "swiggy":
        result = await swiggy.update_order_status(
            order.aggregator_order_id, new_status, estimated_time
        )
    elif order.source == "zomato":
        result = await zomato.update_order_status(
            order.aggregator_order_id, new_status, estimated_time
        )

    return {
        "order_id": order_id,
        "new_status": new_status,
        "aggregator": order.source,
        "sync_result": result
    }
