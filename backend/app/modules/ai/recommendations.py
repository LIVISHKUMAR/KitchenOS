"""AI-powered menu recommendations."""

from typing import List, Dict, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.models import Order, OrderItem, MenuItem, Customer


class RecommendationService:
    """AI-powered menu recommendations based on order history."""

    def __init__(self, db: Session):
        self.db = db

    def get_personalized_recommendations(self, customer_id: str, tenant_id: str,
                                          limit: int = 5) -> List[Dict]:
        """Get personalized menu recommendations for a customer.

        Uses collaborative filtering based on order history.
        """
        # Get customer's order history
        customer_items = self.db.query(
            OrderItem.menu_item_id,
            func.count(OrderItem.id).label("order_count")
        ).join(Order).filter(
            Order.customer_id == customer_id,
            Order.tenant_id == tenant_id,
            Order.status != "cancelled"
        ).group_by(
            OrderItem.menu_item_id
        ).order_by(
            desc("order_count")
        ).limit(10).all()

        if not customer_items:
            return self.get_popular_items(tenant_id, limit)

        # Get items frequently ordered together
        customer_item_ids = [str(ci.menu_item_id) for ci in customer_items]

        # Find items ordered by similar customers
        similar_customers = self.db.query(
            Order.customer_id
        ).join(OrderItem).filter(
            OrderItem.menu_item_id.in_(customer_item_ids),
            Order.tenant_id == tenant_id,
            Order.customer_id != customer_id,
            Order.status != "cancelled"
        ).group_by(
            Order.customer_id
        ).having(
            func.count(OrderItem.id) >= 2
        ).limit(50).all()

        if not similar_customers:
            return self.get_popular_items(tenant_id, limit)

        similar_ids = [str(sc.customer_id) for sc in similar_customers]

        # Get items from similar customers that current customer hasn't ordered
        recommended_items = self.db.query(
            OrderItem.menu_item_id,
            func.count(OrderItem.id).label("popularity")
        ).join(Order).filter(
            Order.customer_id.in_(similar_ids),
            Order.tenant_id == tenant_id,
            ~OrderItem.menu_item_id.in_(customer_item_ids),
            Order.status != "cancelled"
        ).group_by(
            OrderItem.menu_item_id
        ).order_by(
            desc("popularity")
        ).limit(limit).all()

        # Get item details
        item_ids = [str(ri.menu_item_id) for ri in recommended_items]
        items = self.db.query(MenuItem).filter(
            MenuItem.id.in_(item_ids),
            MenuItem.is_available == True
        ).all()

        return [
            {
                "id": str(item.id),
                "name": item.name,
                "price": float(item.base_price),
                "is_veg": item.is_veg,
                "reason": "Customers like you also ordered this"
            }
            for item in items
        ]

    def get_popular_items(self, tenant_id: str, limit: int = 10) -> List[Dict]:
        """Get popular menu items."""
        popular = self.db.query(
            OrderItem.menu_item_id,
            func.sum(OrderItem.quantity).label("total_quantity")
        ).join(Order).filter(
            Order.tenant_id == tenant_id,
            Order.status != "cancelled",
            Order.created_at >= datetime.utcnow() - timedelta(days=30)
        ).group_by(
            OrderItem.menu_item_id
        ).order_by(
            desc("total_quantity")
        ).limit(limit).all()

        item_ids = [str(p.menu_item_id) for p in popular]
        items = self.db.query(MenuItem).filter(
            MenuItem.id.in_(item_ids),
            MenuItem.is_available == True
        ).all()

        item_map = {str(item.id): item for item in items}

        return [
            {
                "id": item_id,
                "name": item_map[item_id].name,
                "price": float(item_map[item_id].base_price),
                "is_veg": item_map[item_id].is_veg,
                "reason": "Popular choice"
            }
            for item_id in item_ids
            if item_id in item_map
        ]

    def get_frequently_bought_together(self, item_id: str, tenant_id: str,
                                        limit: int = 3) -> List[Dict]:
        """Get items frequently bought together with a given item."""
        # Find orders containing the item
        orders_with_item = self.db.query(Order.id).join(OrderItem).filter(
            OrderItem.menu_item_id == item_id,
            Order.tenant_id == tenant_id,
            Order.status != "cancelled"
        ).subquery()

        # Find other items in those orders
        co_occurring = self.db.query(
            OrderItem.menu_item_id,
            func.count(OrderItem.id).label("frequency")
        ).filter(
            OrderItem.order_id.in_(orders_with_item),
            OrderItem.menu_item_id != item_id
        ).group_by(
            OrderItem.menu_item_id
        ).order_by(
            desc("frequency")
        ).limit(limit).all()

        item_ids = [str(co.menu_item_id) for co in co_occurring]
        items = self.db.query(MenuItem).filter(
            MenuItem.id.in_(item_ids),
            MenuItem.is_available == True
        ).all()

        return [
            {
                "id": str(item.id),
                "name": item.name,
                "price": float(item.base_price),
                "is_veg": item.is_veg
            }
            for item in items
        ]

    def get_time_based_recommendations(self, tenant_id: str, branch_id: str = None,
                                        limit: int = 5) -> List[Dict]:
        """Get recommendations based on time of day."""
        hour = datetime.utcnow().hour

        # Determine meal period
        if 6 <= hour < 11:
            meal_period = "breakfast"
        elif 11 <= hour < 15:
            meal_period = "lunch"
        elif 15 <= hour < 18:
            meal_period = "snacks"
        else:
            meal_period = "dinner"

        # Get popular items for this time period
        popular = self.db.query(
            OrderItem.menu_item_id,
            func.count(OrderItem.id).label("popularity")
        ).join(Order).filter(
            Order.tenant_id == tenant_id,
            func.extract('hour', Order.created_at).between(
                hour - 2, hour + 2
            ),
            Order.status != "cancelled"
        ).group_by(
            OrderItem.menu_item_id
        ).order_by(
            desc("popularity")
        ).limit(limit).all()

        item_ids = [str(p.menu_item_id) for p in popular]
        items = self.db.query(MenuItem).filter(
            MenuItem.id.in_(item_ids),
            MenuItem.is_available == True
        ).all()

        return [
            {
                "id": str(item.id),
                "name": item.name,
                "price": float(item.base_price),
                "is_veg": item.is_veg,
                "reason": f"Popular for {meal_period}"
            }
            for item in items
        ]
