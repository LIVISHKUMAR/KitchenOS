"""Profitability analytics service."""

from typing import Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func, cast, Date

from app.models import Order, OrderItem, MenuItem, MenuCategory


class ProfitabilityService:
    def __init__(self, db: Session):
        self.db = db

    def get_item_profitability(self, tenant_id: str, branch_id: Optional[str] = None,
                                date_from: Optional[str] = None, date_to: Optional[str] = None) -> list:
        """Get profitability per menu item."""
        query = self.db.query(
            MenuItem.id,
            MenuItem.name,
            MenuItem.base_price,
            MenuItem.cost_price,
            func.sum(OrderItem.quantity).label("total_quantity"),
            func.sum(OrderItem.total).label("total_revenue")
        ).join(
            OrderItem, MenuItem.id == OrderItem.menu_item_id
        ).join(
            Order, OrderItem.order_id == Order.id
        ).filter(
            MenuItem.tenant_id == tenant_id,
            Order.status != "cancelled"
        )

        if branch_id:
            query = query.filter(Order.branch_id == branch_id)
        if date_from:
            query = query.filter(cast(Order.created_at, Date) >= date_from)
        if date_to:
            query = query.filter(cast(Order.created_at, Date) <= date_to)

        results = query.group_by(MenuItem.id).all()

        items = []
        for r in results:
            selling_price = float(r.base_price)
            cost_price = float(r.cost_price or 0)
            quantity = float(r.total_quantity or 0)
            revenue = float(r.total_revenue or 0)
            food_cost = cost_price * quantity
            gross_profit = revenue - food_cost
            margin = ((selling_price - cost_price) / selling_price * 100) if selling_price else 0

            items.append({
                "item_id": str(r.id),
                "item_name": r.name,
                "selling_price": selling_price,
                "cost_price": cost_price,
                "quantity_sold": quantity,
                "revenue": round(revenue, 2),
                "food_cost": round(food_cost, 2),
                "gross_profit": round(gross_profit, 2),
                "margin_percentage": round(margin, 1)
            })

        return sorted(items, key=lambda x: x["gross_profit"], reverse=True)

    def get_category_profitability(self, tenant_id: str, branch_id: Optional[str] = None) -> list:
        """Get profitability per category."""
        results = self.db.query(
            MenuCategory.name,
            func.sum(OrderItem.total).label("revenue"),
            func.sum(OrderItem.quantity).label("quantity")
        ).join(
            MenuItem, MenuCategory.id == MenuItem.category_id
        ).join(
            OrderItem, MenuItem.id == OrderItem.menu_item_id
        ).join(
            Order, OrderItem.order_id == Order.id
        ).filter(
            MenuCategory.tenant_id == tenant_id,
            Order.status != "cancelled"
        )

        if branch_id:
            results = results.filter(Order.branch_id == branch_id)

        results = results.group_by(MenuCategory.name).all()

        categories = []
        for r in results:
            # Estimate cost (would need recipe mapping for accuracy)
            revenue = float(r.revenue or 0)
            categories.append({
                "category": r.name,
                "revenue": round(revenue, 2),
                "quantity": float(r.quantity or 0),
                "estimated_margin": round(revenue * 0.65, 2)  # Assume 65% margin
            })

        return sorted(categories, key=lambda x: x["revenue"], reverse=True)

    def get_branch_profitability(self, tenant_id: str) -> list:
        """Get profitability per branch."""
        from app.models import Branch

        branches = self.db.query(Branch).filter(
            Branch.tenant_id == tenant_id,
            Branch.is_active == True
        ).all()

        results = []
        for branch in branches:
            revenue = self.db.query(func.sum(Order.total)).filter(
                Order.branch_id == branch.id,
                Order.status != "cancelled"
            ).scalar() or 0

            orders = self.db.query(func.count(Order.id)).filter(
                Order.branch_id == branch.id,
                Order.status != "cancelled"
            ).scalar() or 0

            results.append({
                "branch_id": str(branch.id),
                "branch_name": branch.name,
                "revenue": float(revenue),
                "orders": orders,
                "avg_order_value": round(float(revenue) / orders, 2) if orders else 0
            })

        return sorted(results, key=lambda x: x["revenue"], reverse=True)
