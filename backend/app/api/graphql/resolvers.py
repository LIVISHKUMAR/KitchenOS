"""GraphQL resolvers with database access."""

import strawberry
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.infrastructure.database import SessionLocal
from app.models import MenuItem, MenuCategory, Order, OrderItem, Customer, Payment


class GraphQLContext:
    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id


def get_menu_items(info, category_id: Optional[str] = None) -> list:
    """Resolve menu items."""
    ctx: GraphQLContext = info.context
    query = ctx.db.query(MenuItem).filter(
        MenuItem.tenant_id == ctx.tenant_id,
        MenuItem.is_available == True
    )
    if category_id:
        query = query.filter(MenuItem.category_id == category_id)

    items = query.all()
    return [
        {
            "id": str(item.id),
            "name": item.name,
            "description": item.description,
            "base_price": float(item.base_price),
            "is_veg": item.is_veg,
            "is_available": item.is_available,
            "category_id": str(item.category_id) if item.category_id else None,
            "item_code": item.item_code
        }
        for item in items
    ]


def get_menu_categories(info) -> list:
    """Resolve menu categories."""
    ctx: GraphQLContext = info.context
    categories = ctx.db.query(MenuCategory).filter(
        MenuCategory.tenant_id == ctx.tenant_id,
        MenuCategory.is_active == True
    ).order_by(MenuCategory.display_order).all()

    return [
        {
            "id": str(cat.id),
            "name": cat.name,
            "description": cat.description,
            "display_order": cat.display_order
        }
        for cat in categories
    ]


def get_orders(info, status: Optional[str] = None, limit: int = 50) -> list:
    """Resolve orders."""
    ctx: GraphQLContext = info.context
    query = ctx.db.query(Order).filter(Order.tenant_id == ctx.tenant_id)
    if status:
        query = query.filter(Order.status == status)

    orders = query.order_by(Order.created_at.desc()).limit(limit).all()

    result = []
    for order in orders:
        items = ctx.db.query(OrderItem).filter(OrderItem.order_id == order.id).all()
        result.append({
            "id": str(order.id),
            "order_number": order.order_number,
            "order_type": order.order_type,
            "status": order.status,
            "subtotal": float(order.subtotal or 0),
            "tax_amount": float(order.tax_amount or 0),
            "total": float(order.total or 0),
            "payment_status": order.payment_status,
            "customer_name": order.customer_name,
            "items": [
                {
                    "id": str(item.id),
                    "menu_item_id": str(item.menu_item_id),
                    "item_name": item.item_name,
                    "quantity": float(item.quantity),
                    "unit_price": float(item.unit_price),
                    "total": float(item.total),
                    "prep_status": item.prep_status
                }
                for item in items
            ],
            "created_at": order.created_at.isoformat() if order.created_at else None
        })

    return result


def get_order(info, id: str) -> Optional[dict]:
    """Resolve single order."""
    ctx: GraphQLContext = info.context
    order = ctx.db.query(Order).filter(
        Order.id == id,
        Order.tenant_id == ctx.tenant_id
    ).first()

    if not order:
        return None

    items = ctx.db.query(OrderItem).filter(OrderItem.order_id == order.id).all()

    return {
        "id": str(order.id),
        "order_number": order.order_number,
        "order_type": order.order_type,
        "status": order.status,
        "subtotal": float(order.subtotal or 0),
        "tax_amount": float(order.tax_amount or 0),
        "total": float(order.total or 0),
        "payment_status": order.payment_status,
        "customer_name": order.customer_name,
        "items": [
            {
                "id": str(item.id),
                "menu_item_id": str(item.menu_item_id),
                "item_name": item.item_name,
                "quantity": float(item.quantity),
                "unit_price": float(item.unit_price),
                "total": float(item.total),
                "prep_status": item.prep_status
            }
            for item in items
        ],
        "created_at": order.created_at.isoformat() if order.created_at else None
    }


def get_customers(info, limit: int = 50) -> list:
    """Resolve customers."""
    ctx: GraphQLContext = info.context
    customers = ctx.db.query(Customer).filter(
        Customer.tenant_id == ctx.tenant_id
    ).limit(limit).all()

    return [
        {
            "id": str(c.id),
            "name": c.name,
            "email": c.email,
            "phone": c.phone,
            "loyalty_points": c.loyalty_points or 0,
            "total_orders": c.total_orders or 0,
            "total_spent": float(c.total_spent or 0)
        }
        for c in customers
    ]


def get_daily_sales(info, date: Optional[str] = None) -> Optional[dict]:
    """Resolve daily sales."""
    ctx: GraphQLContext = info.context
    from sqlalchemy import func, cast, Date

    target_date = datetime.strptime(date, "%Y-%m-%d").date() if date else datetime.utcnow().date()

    result = ctx.db.query(
        func.count(Order.id).label("order_count"),
        func.coalesce(func.sum(Order.total), 0).label("total_sales"),
        func.coalesce(func.avg(Order.total), 0).label("avg_order_value")
    ).filter(
        Order.tenant_id == ctx.tenant_id,
        cast(Order.created_at, Date) == target_date,
        Order.status != "cancelled"
    ).first()

    return {
        "date": str(target_date),
        "order_count": result.order_count or 0,
        "total_sales": float(result.total_sales or 0),
        "avg_order_value": float(result.avg_order_value or 0)
    }
