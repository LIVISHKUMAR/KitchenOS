"""Multi-outlet management dashboard endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from datetime import datetime, timedelta
from pydantic import BaseModel

from app.api.dependencies import get_current_user
from app.infrastructure.database import get_db_session
from app.models import Branch, Order, MenuItem, InventoryItem, Customer, User

router = APIRouter()


class MenuPushRequest(BaseModel):
    source_branch_id: str
    target_branch_ids: list


@router.get("/dashboard")
async def multi_outlet_dashboard(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Centralized multi-outlet dashboard."""
    tenant_id = current_user["tenant_id"]

    branches = db.query(Branch).filter(
        Branch.tenant_id == tenant_id,
        Branch.is_active == True
    ).all()

    outlets = []
    for branch in branches:
        today = datetime.utcnow().date()
        month_ago = datetime.utcnow() - timedelta(days=30)

        # Today's stats
        today_orders = db.query(func.count(Order.id)).filter(
            Order.branch_id == branch.id,
            func.date(Order.created_at) == today,
            Order.status != "cancelled"
        ).scalar() or 0

        today_revenue = db.query(func.sum(Order.total)).filter(
            Order.branch_id == branch.id,
            func.date(Order.created_at) == today,
            Order.status != "cancelled"
        ).scalar() or 0

        # Monthly stats
        month_orders = db.query(func.count(Order.id)).filter(
            Order.branch_id == branch.id,
            Order.created_at >= month_ago,
            Order.status != "cancelled"
        ).scalar() or 0

        month_revenue = db.query(func.sum(Order.total)).filter(
            Order.branch_id == branch.id,
            Order.created_at >= month_ago,
            Order.status != "cancelled"
        ).scalar() or 0

        # Active orders
        active_orders = db.query(func.count(Order.id)).filter(
            Order.branch_id == branch.id,
            Order.status.in_(["pending", "confirmed", "preparing"])
        ).scalar() or 0

        # Staff count
        staff = db.query(func.count(User.id)).filter(
            User.branch_id == branch.id,
            User.is_active == True
        ).scalar() or 0

        # Menu items
        menu_items = db.query(func.count(MenuItem.id)).filter(
            MenuItem.branch_id == branch.id,
            MenuItem.is_available == True
        ).scalar() or 0

        # Low stock
        low_stock = db.query(func.count(InventoryItem.id)).filter(
            InventoryItem.branch_id == branch.id,
            InventoryItem.current_stock <= InventoryItem.minimum_stock,
            InventoryItem.is_active == True
        ).scalar() or 0

        outlets.append({
            "branch_id": str(branch.id),
            "name": branch.name,
            "code": branch.code,
            "city": branch.city,
            "today": {
                "orders": today_orders,
                "revenue": round(float(today_revenue), 2)
            },
            "this_month": {
                "orders": month_orders,
                "revenue": round(float(month_revenue), 2)
            },
            "active_orders": active_orders,
            "staff_count": staff,
            "menu_items": menu_items,
            "low_stock_alerts": low_stock
        })

    return {
        "total_outlets": len(outlets),
        "outlets": outlets,
        "summary": {
            "total_today_orders": sum(o["today"]["orders"] for o in outlets),
            "total_today_revenue": sum(o["today"]["revenue"] for o in outlets),
            "total_month_orders": sum(o["this_month"]["orders"] for o in outlets),
            "total_month_revenue": sum(o["this_month"]["revenue"] for o in outlets),
            "total_active_orders": sum(o["active_orders"] for o in outlets)
        }
    }


@router.get("/comparison")
async def outlet_comparison(
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Compare outlet performance."""
    tenant_id = current_user["tenant_id"]

    branches = db.query(Branch).filter(
        Branch.tenant_id == tenant_id,
        Branch.is_active == True
    ).all()

    comparison = []
    for branch in branches:
        query = db.query(
            func.count(Order.id).label("orders"),
            func.sum(Order.total).label("revenue"),
            func.avg(Order.total).label("avg_order")
        ).filter(
            Order.branch_id == branch.id,
            Order.status != "cancelled"
        )

        if date_from:
            query = query.filter(Order.created_at >= date_from)
        if date_to:
            query = query.filter(Order.created_at <= date_to)

        result = query.first()

        comparison.append({
            "branch_id": str(branch.id),
            "name": branch.name,
            "orders": result.orders or 0,
            "revenue": round(float(result.revenue or 0), 2),
            "avg_order_value": round(float(result.avg_order or 0), 2)
        })

    return sorted(comparison, key=lambda x: x["revenue"], reverse=True)


@router.post("/menu/push")
async def push_menu(
    data: MenuPushRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Push menu from one outlet to others."""
    tenant_id = current_user["tenant_id"]

    source_items = db.query(MenuItem).filter(
        MenuItem.tenant_id == tenant_id,
        MenuItem.branch_id == data.source_branch_id
    ).all()

    pushed = 0
    updated = 0

    for target_id in data.target_branch_ids:
        for item in source_items:
            existing = db.query(MenuItem).filter(
                MenuItem.tenant_id == tenant_id,
                MenuItem.branch_id == target_id,
                MenuItem.item_code == item.item_code
            ).first()

            if existing:
                existing.name = item.name
                existing.description = item.description
                existing.base_price = item.base_price
                existing.tax_rate = item.tax_rate
                existing.is_veg = item.is_veg
                existing.recipe_ingredients = item.recipe_ingredients
                updated += 1
            else:
                new_item = MenuItem(
                    id=str(uuid.uuid4()),
                    tenant_id=tenant_id,
                    branch_id=target_id,
                    name=item.name,
                    description=item.description,
                    item_code=item.item_code,
                    base_price=item.base_price,
                    cost_price=item.cost_price,
                    tax_rate=item.tax_rate,
                    is_veg=item.is_veg,
                    recipe_ingredients=item.recipe_ingredients,
                    category_id=item.category_id,
                    is_available=True
                )
                db.add(new_item)
                pushed += 1

    db.commit()

    return {
        "pushed": pushed,
        "updated": updated,
        "target_branches": len(data.target_branch_ids)
    }


import uuid
