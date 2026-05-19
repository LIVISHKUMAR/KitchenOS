"""Full-text search endpoints."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.api.dependencies import get_current_user
from app.infrastructure.database import get_db_session
from app.models import MenuItem, Order, Customer, InventoryItem

router = APIRouter()


@router.get("/")
async def search(
    q: str = Query(..., min_length=2),
    type: str = Query(default="all"),  # all, menu, orders, customers, inventory
    limit: int = Query(default=20, le=100),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Full-text search across multiple entities."""
    tenant_id = current_user["tenant_id"]
    results = {"menu": [], "orders": [], "customers": [], "inventory": []}
    search_term = f"%{q}%"

    if type in ("all", "menu"):
        menu_items = db.query(MenuItem).filter(
            MenuItem.tenant_id == tenant_id,
            or_(
                MenuItem.name.ilike(search_term),
                MenuItem.description.ilike(search_term),
                MenuItem.item_code.ilike(search_term)
            )
        ).limit(limit).all()

        results["menu"] = [
            {
                "id": str(item.id),
                "name": item.name,
                "description": item.description,
                "base_price": float(item.base_price),
                "is_available": item.is_available
            }
            for item in menu_items
        ]

    if type in ("all", "orders"):
        orders = db.query(Order).filter(
            Order.tenant_id == tenant_id,
            or_(
                Order.order_number.ilike(search_term),
                Order.customer_name.ilike(search_term),
                Order.customer_phone.ilike(search_term)
            )
        ).order_by(Order.created_at.desc()).limit(limit).all()

        results["orders"] = [
            {
                "id": str(order.id),
                "order_number": order.order_number,
                "status": order.status,
                "total": float(order.total),
                "customer_name": order.customer_name,
                "created_at": order.created_at.isoformat() if order.created_at else None
            }
            for order in orders
        ]

    if type in ("all", "customers"):
        customers = db.query(Customer).filter(
            Customer.tenant_id == tenant_id,
            or_(
                Customer.name.ilike(search_term),
                Customer.phone.ilike(search_term),
                Customer.email.ilike(search_term)
            )
        ).limit(limit).all()

        results["customers"] = [
            {
                "id": str(c.id),
                "name": c.name,
                "phone": c.phone,
                "email": c.email,
                "loyalty_points": c.loyalty_points or 0
            }
            for c in customers
        ]

    if type in ("all", "inventory"):
        items = db.query(InventoryItem).filter(
            InventoryItem.tenant_id == tenant_id,
            or_(
                InventoryItem.name.ilike(search_term),
                InventoryItem.item_code.ilike(search_term),
                InventoryItem.bar_code.ilike(search_term)
            )
        ).limit(limit).all()

        results["inventory"] = [
            {
                "id": str(item.id),
                "name": item.name,
                "item_code": item.item_code,
                "current_stock": float(item.current_stock),
                "unit": item.unit
            }
            for item in items
        ]

    # Flatten for "all" type
    if type == "all":
        total = sum(len(v) for v in results.values())
        return {"query": q, "total_results": total, "results": results}

    return {"query": q, "results": results.get(type, [])}
