"""Recipe mapping and food cost calculation."""

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_
import uuid

from app.models import MenuItem, InventoryItem
from app.api.exceptions import NotFoundException, BadRequestException


class RecipeService:
    def __init__(self, db: Session):
        self.db = db

    def add_recipe_ingredient(self, menu_item_id: str, inventory_item_id: str,
                               quantity: float, unit: str, tenant_id: str) -> dict:
        """Add a recipe ingredient mapping. Uses a simple join table approach."""
        menu_item = self.db.query(MenuItem).filter(MenuItem.id == menu_item_id).first()
        if not menu_item:
            raise NotFoundException("Menu item not found")

        inv_item = self.db.query(InventoryItem).filter(InventoryItem.id == inventory_item_id).first()
        if not inv_item:
            raise NotFoundException("Inventory item not found")

        # Store recipe in menu_item's JSON field (recipe_ingredients)
        current_recipe = menu_item.recipe_ingredients or []

        # Check if already exists
        for ing in current_recipe:
            if ing.get("inventory_item_id") == inventory_item_id:
                ing["quantity"] = quantity
                ing["unit"] = unit
                self.db.commit()
                return {"message": "Updated", "ingredient": ing}

        new_ingredient = {
            "id": str(uuid.uuid4()),
            "inventory_item_id": inventory_item_id,
            "inventory_item_name": inv_item.name,
            "quantity": quantity,
            "unit": unit,
            "cost_per_unit": float(inv_item.cost_price) if inv_item.cost_price else 0
        }
        current_recipe.append(new_ingredient)
        menu_item.recipe_ingredients = current_recipe
        self.db.commit()

        return {"message": "Added", "ingredient": new_ingredient}

    def remove_recipe_ingredient(self, menu_item_id: str, ingredient_id: str) -> dict:
        """Remove a recipe ingredient."""
        menu_item = self.db.query(MenuItem).filter(MenuItem.id == menu_item_id).first()
        if not menu_item:
            raise NotFoundException("Menu item not found")

        current_recipe = menu_item.recipe_ingredients or []
        menu_item.recipe_ingredients = [i for i in current_recipe if i.get("id") != ingredient_id]
        self.db.commit()

        return {"message": "Removed"}

    def get_recipe(self, menu_item_id: str) -> dict:
        """Get recipe for a menu item."""
        menu_item = self.db.query(MenuItem).filter(MenuItem.id == menu_item_id).first()
        if not menu_item:
            raise NotFoundException("Menu item not found")

        ingredients = menu_item.recipe_ingredients or []
        total_cost = sum(
            i.get("quantity", 0) * i.get("cost_per_unit", 0)
            for i in ingredients
        )

        return {
            "menu_item_id": str(menu_item.id),
            "menu_item_name": menu_item.name,
            "base_price": float(menu_item.base_price),
            "ingredients": ingredients,
            "total_food_cost": round(total_cost, 2),
            "food_cost_percentage": round((total_cost / float(menu_item.base_price)) * 100, 1) if menu_item.base_price else 0,
            "gross_margin": round(float(menu_item.base_price) - total_cost, 2)
        }

    def calculate_food_cost(self, menu_item_id: str, quantity: float = 1) -> dict:
        """Calculate food cost for a given quantity of a menu item."""
        recipe = self.get_recipe(menu_item_id)

        ingredients_cost = []
        for ing in recipe["ingredients"]:
            cost = ing.get("quantity", 0) * ing.get("cost_per_unit", 0) * quantity
            ingredients_cost.append({
                "name": ing.get("inventory_item_name"),
                "quantity_needed": ing.get("quantity", 0) * quantity,
                "unit": ing.get("unit"),
                "cost": round(cost, 2)
            })

        total_cost = sum(i["cost"] for i in ingredients_cost)
        selling_price = recipe["base_price"] * quantity

        return {
            "menu_item_id": recipe["menu_item_id"],
            "menu_item_name": recipe["menu_item_name"],
            "quantity": quantity,
            "ingredients": ingredients_cost,
            "total_food_cost": round(total_cost, 2),
            "selling_price": selling_price,
            "food_cost_percentage": round((total_cost / selling_price) * 100, 1) if selling_price else 0,
            "gross_profit": round(selling_price - total_cost, 2)
        }

    def get_deductable_items(self, menu_item_id: str, quantity: float) -> List[dict]:
        """Get inventory items that need to be deducted for a menu item."""
        menu_item = self.db.query(MenuItem).filter(MenuItem.id == menu_item_id).first()
        if not menu_item or not menu_item.recipe_ingredients:
            return []

        deductions = []
        for ing in menu_item.recipe_ingredients:
            deductions.append({
                "inventory_item_id": ing.get("inventory_item_id"),
                "quantity": ing.get("quantity", 0) * quantity,
                "unit": ing.get("unit")
            })

        return deductions
