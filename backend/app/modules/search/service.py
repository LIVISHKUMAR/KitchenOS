"""Advanced search service with ranking."""

from typing import List, Optional, Dict
from sqlalchemy.orm import Session
from sqlalchemy import or_, func, case

from app.models import MenuItem, Order, Customer, InventoryItem, MenuCategory


class SearchService:
    def __init__(self, db: Session):
        self.db = db

    def search(self, tenant_id: str, query: str, entity_type: str = "all",
               limit: int = 20) -> dict:
        """Full-text search with ranking."""
        results = {"menu": [], "orders": [], "customers": [], "inventory": []}

        if entity_type in ("all", "menu"):
            results["menu"] = self._search_menu(tenant_id, query, limit)

        if entity_type in ("all", "orders"):
            results["orders"] = self._search_orders(tenant_id, query, limit)

        if entity_type in ("all", "customers"):
            results["customers"] = self._search_customers(tenant_id, query, limit)

        if entity_type in ("all", "inventory"):
            results["inventory"] = self._search_inventory(tenant_id, query, limit)

        total = sum(len(v) for v in results.values())

        return {"query": query, "total_results": total, "results": results}

    def _search_menu(self, tenant_id: str, query: str, limit: int) -> list:
        """Search menu items with ranking."""
        search_term = f"%{query}%"

        # Rank: exact name match > name contains > description contains > item_code
        items = self.db.query(MenuItem).filter(
            MenuItem.tenant_id == tenant_id,
            MenuItem.is_available == True,
            or_(
                MenuItem.name.ilike(search_term),
                MenuItem.description.ilike(search_term),
                MenuItem.item_code.ilike(search_term)
            )
        ).order_by(
            # Exact match first
            case(
                (MenuItem.name.ilike(query), 0),
                (MenuItem.name.ilike(f"{query}%"), 1),
                (MenuItem.name.ilike(search_term), 2),
                else_=3
            )
        ).limit(limit).all()

        return [
            {
                "id": str(item.id),
                "name": item.name,
                "description": item.description,
                "price": float(item.base_price),
                "is_veg": item.is_veg,
                "item_code": item.item_code,
                "category_id": str(item.category_id) if item.category_id else None
            }
            for item in items
        ]

    def _search_orders(self, tenant_id: str, query: str, limit: int) -> list:
        """Search orders."""
        search_term = f"%{query}%"

        orders = self.db.query(Order).filter(
            Order.tenant_id == tenant_id,
            or_(
                Order.order_number.ilike(search_term),
                Order.customer_name.ilike(search_term),
                Order.customer_phone.ilike(search_term)
            )
        ).order_by(Order.created_at.desc()).limit(limit).all()

        return [
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

    def _search_customers(self, tenant_id: str, query: str, limit: int) -> list:
        """Search customers."""
        search_term = f"%{query}%"

        customers = self.db.query(Customer).filter(
            Customer.tenant_id == tenant_id,
            or_(
                Customer.name.ilike(search_term),
                Customer.phone.ilike(search_term),
                Customer.email.ilike(search_term)
            )
        ).limit(limit).all()

        return [
            {
                "id": str(c.id),
                "name": c.name,
                "phone": c.phone,
                "email": c.email,
                "loyalty_points": c.loyalty_points or 0
            }
            for c in customers
        ]

    def _search_inventory(self, tenant_id: str, query: str, limit: int) -> list:
        """Search inventory items."""
        search_term = f"%{query}%"

        items = self.db.query(InventoryItem).filter(
            InventoryItem.tenant_id == tenant_id,
            or_(
                InventoryItem.name.ilike(search_term),
                InventoryItem.item_code.ilike(search_term),
                InventoryItem.bar_code.ilike(search_term)
            )
        ).limit(limit).all()

        return [
            {
                "id": str(item.id),
                "name": item.name,
                "item_code": item.item_code,
                "current_stock": float(item.current_stock),
                "unit": item.unit
            }
            for item in items
        ]

    def get_suggestions(self, tenant_id: str, query: str, limit: int = 5) -> list:
        """Get search suggestions/autocomplete."""
        if len(query) < 2:
            return []

        search_term = f"{query}%"

        # Get suggestions from menu items
        items = self.db.query(MenuItem.name).filter(
            MenuItem.tenant_id == tenant_id,
            MenuItem.is_available == True,
            MenuItem.name.ilike(search_term)
        ).distinct().limit(limit).all()

        return [item.name for item in items]
