from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, cast, Date
from datetime import datetime, timedelta
from app.models import Order, OrderItem, Payment, MenuItem, MenuCategory


class ReportService:
    def __init__(self, db: Session):
        self.db = db

    def daily_sales(self, tenant_id: str, branch_id: Optional[str] = None, date: Optional[str] = None):
        target_date = datetime.strptime(date, "%Y-%m-%d").date() if date else datetime.utcnow().date()

        query = self.db.query(
            func.count(Order.id).label("order_count"),
            func.coalesce(func.sum(Order.subtotal), 0).label("total_sales"),
            func.coalesce(func.avg(Order.total), 0).label("avg_order_value"),
            func.coalesce(func.sum(Order.tax_amount), 0).label("total_tax"),
            func.coalesce(func.sum(Order.discount_amount), 0).label("total_discount")
        ).filter(
            Order.tenant_id == tenant_id,
            cast(Order.created_at, Date) == target_date,
            Order.status != "cancelled"
        )

        if branch_id:
            query = query.filter(Order.branch_id == branch_id)

        result = query.first()

        # Payment mode breakdown
        payment_query = self.db.query(
            Payment.payment_method,
            func.count(Payment.id).label("count"),
            func.coalesce(func.sum(Payment.amount), 0).label("total")
        ).join(Order, Payment.order_id == Order.id).filter(
            Order.tenant_id == tenant_id,
            cast(Order.created_at, Date) == target_date,
            Payment.status == "completed"
        )

        if branch_id:
            payment_query = payment_query.filter(Order.branch_id == branch_id)

        payments = payment_query.group_by(Payment.payment_method).all()

        return {
            "date": str(target_date),
            "order_count": result.order_count,
            "total_sales": float(result.total_sales),
            "avg_order_value": float(result.avg_order_value),
            "total_tax": float(result.total_tax),
            "total_discount": float(result.total_discount),
            "payment_breakdown": [
                {"method": p.payment_method, "count": p.count, "total": float(p.total)}
                for p in payments
            ]
        }

    def item_wise_sales(self, tenant_id: str, branch_id: Optional[str] = None,
                        date_from: Optional[str] = None, date_to: Optional[str] = None):
        query = self.db.query(
            OrderItem.menu_item_id,
            OrderItem.item_name,
            func.sum(OrderItem.quantity).label("total_quantity"),
            func.sum(OrderItem.total).label("total_revenue"),
            func.count(OrderItem.id).label("order_count")
        ).join(Order, OrderItem.order_id == Order.id).filter(
            Order.tenant_id == tenant_id,
            Order.status != "cancelled"
        )

        if branch_id:
            query = query.filter(Order.branch_id == branch_id)
        if date_from:
            query = query.filter(cast(Order.created_at, Date) >= date_from)
        if date_to:
            query = query.filter(cast(Order.created_at, Date) <= date_to)

        results = query.group_by(
            OrderItem.menu_item_id, OrderItem.item_name
        ).order_by(func.sum(OrderItem.total).desc()).limit(50).all()

        return [
            {
                "menu_item_id": str(r.menu_item_id),
                "item_name": r.item_name,
                "total_quantity": float(r.total_quantity),
                "total_revenue": float(r.total_revenue),
                "order_count": r.order_count
            }
            for r in results
        ]

    def category_wise_sales(self, tenant_id: str, branch_id: Optional[str] = None,
                            date_from: Optional[str] = None, date_to: Optional[str] = None):
        query = self.db.query(
            MenuCategory.name.label("category_name"),
            func.sum(OrderItem.quantity).label("total_quantity"),
            func.sum(OrderItem.total).label("total_revenue"),
            func.count(OrderItem.id).label("order_count")
        ).join(
            MenuItem, OrderItem.menu_item_id == MenuItem.id
        ).join(
            MenuCategory, MenuItem.category_id == MenuCategory.id
        ).join(
            Order, OrderItem.order_id == Order.id
        ).filter(
            Order.tenant_id == tenant_id,
            Order.status != "cancelled"
        )

        if branch_id:
            query = query.filter(Order.branch_id == branch_id)
        if date_from:
            query = query.filter(cast(Order.created_at, Date) >= date_from)
        if date_to:
            query = query.filter(cast(Order.created_at, Date) <= date_to)

        results = query.group_by(
            MenuCategory.name
        ).order_by(func.sum(OrderItem.total).desc()).all()

        return [
            {
                "category_name": r.category_name,
                "total_quantity": float(r.total_quantity),
                "total_revenue": float(r.total_revenue),
                "order_count": r.order_count
            }
            for r in results
        ]

    def hourly_sales(self, tenant_id: str, branch_id: Optional[str] = None, date: Optional[str] = None):
        target_date = datetime.strptime(date, "%Y-%m-%d").date() if date else datetime.utcnow().date()

        query = self.db.query(
            func.strftime('%H', Order.created_at).label("hour"),
            func.count(Order.id).label("order_count"),
            func.coalesce(func.sum(Order.total), 0).label("total_sales")
        ).filter(
            Order.tenant_id == tenant_id,
            cast(Order.created_at, Date) == target_date,
            Order.status != "cancelled"
        )

        if branch_id:
            query = query.filter(Order.branch_id == branch_id)

        results = query.group_by(
            func.strftime('%H', Order.created_at)
        ).order_by(func.strftime('%H', Order.created_at)).all()

        return [
            {
                "hour": int(r.hour),
                "order_count": r.order_count,
                "total_sales": float(r.total_sales)
            }
            for r in results
        ]
