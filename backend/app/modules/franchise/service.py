"""Franchise management service."""

from typing import Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models import Tenant, Branch, MenuItem, Order, MenuCategory


class FranchiseService:
    def __init__(self, db: Session):
        self.db = db

    def push_menu_to_branches(self, tenant_id: str, source_branch_id: str,
                               target_branch_ids: list) -> dict:
        """Push menu from one branch to others."""
        source_items = self.db.query(MenuItem).filter(
            MenuItem.tenant_id == tenant_id,
            MenuItem.branch_id == source_branch_id
        ).all()

        pushed = 0
        skipped = 0

        for target_id in target_branch_ids:
            for item in source_items:
                existing = self.db.query(MenuItem).filter(
                    MenuItem.tenant_id == tenant_id,
                    MenuItem.branch_id == target_id,
                    MenuItem.item_code == item.item_code
                ).first()

                if existing:
                    # Update existing
                    existing.name = item.name
                    existing.description = item.description
                    existing.base_price = item.base_price
                    existing.tax_rate = item.tax_rate
                    existing.is_veg = item.is_veg
                    existing.is_available = item.is_available
                    existing.category_id = item.category_id
                    existing.recipe_ingredients = item.recipe_ingredients
                    skipped += 1
                else:
                    # Create new
                    new_item = MenuItem(
                        tenant_id=tenant_id,
                        branch_id=target_id,
                        name=item.name,
                        description=item.description,
                        item_code=item.item_code,
                        base_price=item.base_price,
                        cost_price=item.cost_price,
                        tax_rate=item.tax_rate,
                        is_veg=item.is_veg,
                        contains_allergens=item.contains_allergens,
                        preparation_time_minutes=item.preparation_time_minutes,
                        calories=item.calories,
                        is_available=item.is_available,
                        is_combo=item.is_combo,
                        combo_details=item.combo_details,
                        printer_routing=item.printer_routing,
                        recipe_ingredients=item.recipe_ingredients,
                        category_id=item.category_id
                    )
                    self.db.add(new_item)
                    pushed += 1

        self.db.commit()
        return {"pushed": pushed, "updated": skipped, "total": pushed + skipped}

    def get_outlet_comparison(self, tenant_id: str, date_from: str = None,
                              date_to: str = None) -> list:
        """Compare performance across outlets."""
        branches = self.db.query(Branch).filter(
            Branch.tenant_id == tenant_id,
            Branch.is_active == True
        ).all()

        comparison = []
        for branch in branches:
            query = self.db.query(
                func.count(Order.id).label("order_count"),
                func.coalesce(func.sum(Order.total), 0).label("revenue"),
                func.coalesce(func.avg(Order.total), 0).label("avg_order_value")
            ).filter(
                Order.tenant_id == tenant_id,
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
                "branch_name": branch.name,
                "city": branch.city,
                "order_count": result.order_count or 0,
                "revenue": float(result.revenue or 0),
                "avg_order_value": float(result.avg_order_value or 0)
            })

        return sorted(comparison, key=lambda x: x["revenue"], reverse=True)

    def get_centralized_inventory(self, tenant_id: str) -> list:
        """Get inventory across all branches."""
        from app.models import InventoryItem

        items = self.db.query(InventoryItem).filter(
            InventoryItem.tenant_id == tenant_id,
            InventoryItem.is_active == True
        ).all()

        # Group by item name/code
        aggregated = {}
        for item in items:
            key = item.item_code or item.name
            if key not in aggregated:
                aggregated[key] = {
                    "name": item.name,
                    "item_code": item.item_code,
                    "unit": item.unit,
                    "branches": {},
                    "total_stock": 0
                }

            branch = self.db.query(Branch).filter(Branch.id == item.branch_id).first()
            branch_name = branch.name if branch else "Unknown"

            aggregated[key]["branches"][branch_name] = {
                "branch_id": str(item.branch_id),
                "current_stock": float(item.current_stock),
                "minimum_stock": float(item.minimum_stock or 0)
            }
            aggregated[key]["total_stock"] += float(item.current_stock)

        return list(aggregated.values())
