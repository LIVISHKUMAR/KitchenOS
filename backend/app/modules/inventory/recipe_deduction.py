"""Recipe-based inventory deduction engine."""

import uuid
import logging
from typing import List, Dict, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.models import MenuItem, InventoryItem, StockMovement

logger = logging.getLogger("kitchenos.recipe_deduction")


class RecipeDeductionEngine:
    """Precise inventory deduction based on recipe BOM (Bill of Materials)."""

    # Unit conversion rates
    UNIT_CONVERSIONS = {
        ("kg", "g"): 1000,
        ("g", "kg"): 0.001,
        ("l", "ml"): 1000,
        ("ml", "l"): 0.001,
        ("kg", "mg"): 1000000,
        ("l", "cl"): 100,
    }

    def __init__(self, db: Session):
        self.db = db

    def deduct_for_order(self, order_items: List[dict], branch_id: str,
                         user_id: str, order_id: str) -> Dict:
        """Deduct inventory for all items in an order.

        Args:
            order_items: [{menu_item_id, quantity, item_name}]
            branch_id: Branch ID
            user_id: User performing the action
            order_id: Order ID for tracking

        Returns:
            Deduction summary with successful and failed deductions
        """
        results = {
            "total_items": len(order_items),
            "deducted": 0,
            "skipped": 0,
            "failed": 0,
            "low_stock_warnings": [],
            "insufficient_stock": [],
            "deductions": []
        }

        for order_item in order_items:
            menu_item_id = order_item.get("menu_item_id")
            order_quantity = float(order_item.get("quantity", 1))

            # Get menu item with recipe
            menu_item = self.db.query(MenuItem).filter(
                MenuItem.id == menu_item_id
            ).first()

            if not menu_item or not menu_item.recipe_ingredients:
                results["skipped"] += 1
                continue

            # Process each ingredient in the recipe
            for ingredient in menu_item.recipe_ingredients:
                inv_item_id = ingredient.get("inventory_item_id")
                recipe_qty = float(ingredient.get("quantity", 0))
                recipe_unit = ingredient.get("unit", "pcs")

                # Calculate total deduction: order_qty × recipe_qty per serving
                deduction_qty = order_quantity * recipe_qty

                # Get inventory item
                inv_item = self.db.query(InventoryItem).filter(
                    InventoryItem.id == inv_item_id,
                    InventoryItem.branch_id == branch_id,
                    InventoryItem.is_active == True
                ).first()

                if not inv_item:
                    results["failed"] += 1
                    results["insufficient_stock"].append({
                        "item": ingredient.get("inventory_item_name", "Unknown"),
                        "reason": "Not found in inventory"
                    })
                    continue

                # Convert units if needed
                deduction_in_stock_unit = self._convert_unit(
                    deduction_qty, recipe_unit, inv_item.unit
                )

                # Check stock availability
                current_stock = float(inv_item.current_stock)

                if current_stock < deduction_in_stock_unit:
                    results["failed"] += 1
                    results["insufficient_stock"].append({
                        "item": inv_item.name,
                        "required": deduction_in_stock_unit,
                        "available": current_stock,
                        "unit": inv_item.unit
                    })
                    continue

                # Deduct stock
                inv_item.current_stock = current_stock - deduction_in_stock_unit

                # Create stock movement
                movement = StockMovement(
                    id=str(uuid.uuid4()),
                    inventory_item_id=inv_item.id,
                    branch_id=branch_id,
                    movement_type="sale",
                    quantity=deduction_in_stock_unit,
                    reference_type="order",
                    reference_id=order_id,
                    notes=f"Deducted for order item: {order_item.get('item_name', 'Unknown')}",
                    created_by=user_id,
                    created_at=datetime.utcnow()
                )
                self.db.add(movement)

                results["deducted"] += 1
                results["deductions"].append({
                    "inventory_item": inv_item.name,
                    "quantity_deducted": deduction_in_stock_unit,
                    "unit": inv_item.unit,
                    "remaining_stock": inv_item.current_stock
                })

                # Check for low stock warning
                if inv_item.current_stock <= float(inv_item.minimum_stock or 0):
                    results["low_stock_warnings"].append({
                        "item": inv_item.name,
                        "current_stock": inv_item.current_stock,
                        "minimum_stock": float(inv_item.minimum_stock or 0),
                        "unit": inv_item.unit
                    })

        self.db.commit()
        return results

    def check_stock_availability(self, menu_item_id: str, quantity: float,
                                  branch_id: str) -> Dict:
        """Check if enough stock is available for an order item."""
        menu_item = self.db.query(MenuItem).filter(
            MenuItem.id == menu_item_id
        ).first()

        if not menu_item or not menu_item.recipe_ingredients:
            return {"available": True, "message": "No recipe defined"}

        insufficient = []
        for ingredient in menu_item.recipe_ingredients:
            inv_item_id = ingredient.get("inventory_item_id")
            recipe_qty = float(ingredient.get("quantity", 0))
            recipe_unit = ingredient.get("unit", "pcs")

            required = quantity * recipe_qty

            inv_item = self.db.query(InventoryItem).filter(
                InventoryItem.id == inv_item_id,
                InventoryItem.branch_id == branch_id,
                InventoryItem.is_active == True
            ).first()

            if not inv_item:
                insufficient.append({
                    "item": ingredient.get("inventory_item_name", "Unknown"),
                    "reason": "Not in inventory"
                })
                continue

            required_in_unit = self._convert_unit(required, recipe_unit, inv_item.unit)
            if float(inv_item.current_stock) < required_in_unit:
                insufficient.append({
                    "item": inv_item.name,
                    "required": required_in_unit,
                    "available": float(inv_item.current_stock),
                    "unit": inv_item.unit
                })

        return {
            "available": len(insufficient) == 0,
            "insufficient": insufficient
        }

    def _convert_unit(self, quantity: float, from_unit: str, to_unit: str) -> float:
        """Convert between units."""
        if from_unit == to_unit:
            return quantity

        rate = self.UNIT_CONVERSIONS.get((from_unit, to_unit))
        if rate:
            return quantity * rate

        # Try reverse
        rate = self.UNIT_CONVERSIONS.get((to_unit, from_unit))
        if rate:
            return quantity / rate

        # Can't convert, return as-is
        logger.warning(f"Cannot convert {from_unit} to {to_unit}, returning as-is")
        return quantity
