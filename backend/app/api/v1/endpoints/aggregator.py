"""Aggregator integration endpoints for Swiggy, Zomato, etc."""

from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel
from datetime import datetime
import uuid
from app.api.dependencies import get_current_user
from app.infrastructure.database import get_db_session
from app.models import Order
from app.core.config import settings

router = APIRouter()


class AggregatorOrder(BaseModel):
    aggregator: str  # swiggy, zomato, ubereats
    aggregator_order_id: str
    order_type: str = "delivery"
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    delivery_address: Optional[dict] = None
    items: list
    subtotal: float
    tax: float = 0
    delivery_fee: float = 0
    total: float
    special_instructions: Optional[str] = None
    scheduled_at: Optional[str] = None


class AggregatorStatusUpdate(BaseModel):
    status: str  # confirmed, preparing, ready, picked_up, delivered, cancelled


@router.post("/webhook/order")
async def receive_aggregator_order(
    order: AggregatorOrder,
    x_aggregator_key: Optional[str] = Header(None),
    db: Session = Depends(get_db_session)
):
    """Receive new order from aggregator (Swiggy, Zomato, etc.)."""
    # Validate aggregator key
    if x_aggregator_key != settings.SECRET_KEY[:16]:
        raise HTTPException(status_code=401, detail="Invalid aggregator key")

    # Find tenant by aggregator config (simplified: use first active tenant)
    from app.models import Tenant
    tenant = db.query(Tenant).filter(Tenant.is_active == True).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="No active tenant")

    # Find branch
    from app.models import Branch
    branch = db.query(Branch).filter(Branch.tenant_id == tenant.id, Branch.is_active == True).first()

    # Create order items
    order_items = []
    for item in order.items:
        order_items.append({
            "id": str(uuid.uuid4()),
            "menu_item_id": item.get("menu_item_id", str(uuid.uuid4())),
            "item_name": item.get("name", "Unknown"),
            "item_code": item.get("item_code"),
            "quantity": item.get("quantity", 1),
            "unit_price": item.get("unit_price", 0),
            "total": item.get("quantity", 1) * item.get("unit_price", 0),
            "prep_status": "pending"
        })

    # Create order
    today = datetime.utcnow().strftime("%Y%m%d")
    order_count = db.query(Order).filter(Order.tenant_id == tenant.id).count()

    db_order = Order(
        id=str(uuid.uuid4()),
        order_number=f"AGG-{today}-{order_count + 1:04d}",
        tenant_id=tenant.id,
        branch_id=branch.id if branch else None,
        order_type=order.order_type,
        status="confirmed",
        customer_name=order.customer_name,
        customer_phone=order.customer_phone,
        subtotal=order.subtotal,
        tax_amount=order.tax,
        total=order.total,
        source=order.aggregator,
        aggregator_order_id=order.aggregator_order_id,
        delivery_address=order.delivery_address,
        special_instructions=order.special_instructions,
        scheduled_at=datetime.fromisoformat(order.scheduled_at) if order.scheduled_at else None,
        payment_status="paid",  # Aggregator payments are prepaid
        created_at=datetime.utcnow()
    )
    db.add(db_order)

    from app.models import OrderItem
    for item_data in order_items:
        item_data["order_id"] = db_order.id
        db_item = OrderItem(**item_data)
        db.add(db_item)

    db.commit()
    db.refresh(db_order)

    return {
        "order_id": str(db_order.id),
        "order_number": db_order.order_number,
        "status": "confirmed",
        "message": f"Order received from {order.aggregator}"
    }


@router.post("/order/{order_id}/status")
async def update_aggregator_order_status(
    order_id: str,
    body: AggregatorStatusUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Update order status and sync back to aggregator."""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if str(order.tenant_id) != current_user["tenant_id"]:
        raise HTTPException(status_code=403, detail="Access denied")

    valid_transitions = {
        "confirmed": ["preparing", "cancelled"],
        "preparing": ["ready", "cancelled"],
        "ready": ["picked_up"],
        "picked_up": ["delivered"]
    }

    current = order.status
    if body.status not in valid_transitions.get(current, []):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status transition from '{current}' to '{body.status}'"
        )

    order.status = body.status
    if body.status == "ready":
        order.completed_at = datetime.utcnow()
    db.commit()

    # In production, sync status back to aggregator API
    return {
        "order_id": order_id,
        "aggregator": order.source,
        "aggregator_order_id": order.aggregator_order_id,
        "new_status": body.status,
        "synced": False  # Set to True when aggregator sync is implemented
    }


@router.get("/orders")
async def list_aggregator_orders(
    aggregator: Optional[str] = None,
    status: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """List orders from aggregators."""
    query = db.query(Order).filter(
        Order.tenant_id == current_user["tenant_id"],
        Order.source.notin_(["pos", "qr", "online"])
    )
    if aggregator:
        query = query.filter(Order.source == aggregator)
    if status:
        query = query.filter(Order.status == status)

    orders = query.order_by(Order.created_at.desc()).limit(100).all()

    return [
        {
            "id": str(o.id),
            "order_number": o.order_number,
            "aggregator": o.source,
            "aggregator_order_id": o.aggregator_order_id,
            "status": o.status,
            "total": float(o.total),
            "customer_name": o.customer_name,
            "created_at": o.created_at.isoformat() if o.created_at else None
        }
        for o in orders
    ]
