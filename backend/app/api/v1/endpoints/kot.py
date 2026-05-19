from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from app.api.dependencies import get_current_user
from app.infrastructure.database import get_db_session
from app.models import Order, OrderItem
from app.modules.order.repository import OrderRepository

router = APIRouter()


class KOTItem(BaseModel):
    id: str
    order_id: str
    order_number: str
    menu_item_id: str
    item_name: str
    quantity: float
    modifiers: Optional[list] = []
    cooking_instructions: Optional[str] = None
    course_type: Optional[str] = None
    prep_status: str
    priority: str
    table_id: Optional[str] = None
    created_at: str


class KOTOrder(BaseModel):
    order_id: str
    order_number: str
    table_id: Optional[str] = None
    order_type: str
    items: List[KOTItem]
    created_at: str


class UpdatePrepStatus(BaseModel):
    prep_status: str  # pending, preparing, ready, served


@router.get("/", response_model=List[KOTOrder])
async def get_kot_orders(
    branch_id: Optional[str] = None,
    course_type: Optional[str] = None,
    status: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Get active KOT orders for kitchen display."""
    query = db.query(Order).filter(
        Order.tenant_id == current_user["tenant_id"],
        Order.status.in_(["confirmed", "preparing"])
    )

    if branch_id:
        query = query.filter(Order.branch_id == branch_id)

    orders = query.order_by(Order.created_at.asc()).all()

    kot_orders = []
    for order in orders:
        item_query = db.query(OrderItem).filter(
            OrderItem.order_id == order.id,
            OrderItem.prep_status.in_(["pending", "preparing"])
        )

        if course_type:
            item_query = item_query.filter(OrderItem.course_type == course_type)
        if status:
            item_query = item_query.filter(OrderItem.prep_status == status)

        items = item_query.order_by(OrderItem.created_at.asc()).all()

        if items:
            kot_orders.append({
                "order_id": str(order.id),
                "order_number": order.order_number,
                "table_id": str(order.table_id) if order.table_id else None,
                "order_type": order.order_type,
                "items": [
                    {
                        "id": str(item.id),
                        "order_id": str(item.order_id),
                        "order_number": order.order_number,
                        "menu_item_id": str(item.menu_item_id),
                        "item_name": item.item_name,
                        "quantity": float(item.quantity),
                        "modifiers": item.modifiers or [],
                        "cooking_instructions": item.cooking_instructions,
                        "course_type": item.course_type,
                        "prep_status": item.prep_status,
                        "priority": item.priority or "normal",
                        "table_id": str(order.table_id) if order.table_id else None,
                        "created_at": item.created_at.isoformat() if item.created_at else ""
                    }
                    for item in items
                ],
                "created_at": order.created_at.isoformat() if order.created_at else ""
            })

    return kot_orders


@router.put("/items/{item_id}/status")
async def update_item_prep_status(
    item_id: str,
    body: UpdatePrepStatus,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Update preparation status of a KOT item."""
    valid_statuses = ["pending", "preparing", "ready", "served"]
    if body.prep_status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of {valid_statuses}")

    item = db.query(OrderItem).filter(OrderItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Order item not found")

    # Verify tenant access via order
    order = db.query(Order).filter(Order.id == item.order_id).first()
    if not order or str(order.tenant_id) != current_user["tenant_id"]:
        raise HTTPException(status_code=403, detail="Access denied")

    item.prep_status = body.prep_status
    if body.prep_status == "preparing":
        item.prep_started_at = datetime.utcnow()
    elif body.prep_status == "ready":
        item.ready_at = datetime.utcnow()
    elif body.prep_status == "served":
        item.served_at = datetime.utcnow()

    db.commit()

    # Check if all items in the order are ready
    if body.prep_status == "ready":
        all_items = db.query(OrderItem).filter(OrderItem.order_id == item.order_id).all()
        all_ready = all(i.prep_status in ("ready", "served") for i in all_items)
        if all_ready:
            order.status = "ready"
            db.commit()

    return {"item_id": item_id, "prep_status": body.prep_status, "message": "Status updated"}


@router.get("/summary")
async def get_kot_summary(
    branch_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Get KOT summary counts for kitchen display."""
    query = db.query(OrderItem).join(Order).filter(
        Order.tenant_id == current_user["tenant_id"],
        Order.status.in_(["confirmed", "preparing"])
    )

    if branch_id:
        query = query.filter(Order.branch_id == branch_id)

    items = query.all()

    summary = {
        "pending": 0,
        "preparing": 0,
        "ready": 0,
        "total_items": len(items)
    }

    for item in items:
        if item.prep_status in summary:
            summary[item.prep_status] += 1

    return summary
