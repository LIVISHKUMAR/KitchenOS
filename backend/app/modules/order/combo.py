"""Combo/meal pricing logic."""

from typing import List, Optional
from sqlalchemy.orm import Session
from app.models import MenuItem


class ComboService:
    def __init__(self, db: Session):
        self.db = db

    def calculate_combo_price(self, combo_item_id: str, selected_items: List[dict]) -> dict:
        """Calculate price for a combo meal.

        selected_items: [{menu_item_id, variant_id?}]
        """
        combo = self.db.query(MenuItem).filter(MenuItem.id == combo_item_id).first()
        if not combo or not combo.is_combo:
            return {"error": "Not a combo item"}

        combo_details = combo.combo_details or {}
        rules = combo_details.get("rules", [])
        base_price = float(combo.base_price)

        # If combo has a fixed price, use it
        if combo_details.get("pricing_type") == "fixed":
            return {
                "combo_id": str(combo.id),
                "combo_name": combo.name,
                "pricing_type": "fixed",
                "base_price": base_price,
                "final_price": base_price,
                "items": selected_items
            }

        # Dynamic pricing: sum of components with discount
        component_total = 0.0
        items_detail = []

        for selection in selected_items:
            item = self.db.query(MenuItem).filter(
                MenuItem.id == selection.get("menu_item_id")
            ).first()
            if item:
                item_price = float(item.base_price)
                component_total += item_price
                items_detail.append({
                    "id": str(item.id),
                    "name": item.name,
                    "price": item_price
                })

        # Apply combo discount
        discount_type = combo_details.get("discount_type", "percentage")
        discount_value = combo_details.get("discount_value", 0)

        if discount_type == "percentage":
            discount = component_total * (discount_value / 100)
        elif discount_type == "fixed":
            discount = discount_value
        else:
            discount = component_total - base_price

        final_price = max(0, component_total - discount)

        return {
            "combo_id": str(combo.id),
            "combo_name": combo.name,
            "pricing_type": "dynamic",
            "component_total": round(component_total, 2),
            "discount": round(discount, 2),
            "final_price": round(final_price, 2),
            "savings": round(discount, 2),
            "items": items_detail
        }

    def validate_combo_selection(self, combo_item_id: str, selected_items: List[dict]) -> dict:
        """Validate that selected items match combo rules."""
        combo = self.db.query(MenuItem).filter(MenuItem.id == combo_item_id).first()
        if not combo or not combo.is_combo:
            return {"valid": False, "error": "Not a combo item"}

        combo_details = combo.combo_details or {}
        rules = combo_details.get("rules", [])
        errors = []

        for rule in rules:
            category_id = rule.get("category_id")
            required = rule.get("required", 1)
            max_allowed = rule.get("max", required)

            # Count items from this category
            count = 0
            for selection in selected_items:
                item = self.db.query(MenuItem).filter(
                    MenuItem.id == selection.get("menu_item_id")
                ).first()
                if item and str(item.category_id) == str(category_id):
                    count += 1

            if count < required:
                errors.append(f"Need {required} items from category {category_id}, got {count}")
            if count > max_allowed:
                errors.append(f"Max {max_allowed} items from category {category_id}, got {count}")

        return {
            "valid": len(errors) == 0,
            "errors": errors
        }
