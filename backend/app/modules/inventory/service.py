from typing import List, Optional
from sqlalchemy.orm import Session
from app.models import InventoryItem, StockMovement
from app.modules.inventory.repository import InventoryRepository
import uuid
from datetime import datetime


class InventoryService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = InventoryRepository(db)

    def create_inventory_item(self, item_data: dict) -> InventoryItem:
        db_item = InventoryItem(**item_data)
        return self.repository.create(db_item)

    def get_inventory_item(self, item_id: str) -> Optional[InventoryItem]:
        return self.repository.get(item_id)

    def get_inventory_items(self, tenant_id: str, branch_id: Optional[str] = None, skip: int = 0, limit: int = 100) -> List[InventoryItem]:
        return self.repository.get_all(tenant_id=tenant_id, branch_id=branch_id, skip=skip, limit=limit)

    def update_inventory_item(self, item_id: str, item_data: dict) -> Optional[InventoryItem]:
        return self.repository.update(item_id, item_data)

    def delete_inventory_item(self, item_id: str) -> bool:
        return self.repository.delete(item_id)

    def get_low_stock_items(self, tenant_id: str, branch_id: Optional[str] = None) -> List[InventoryItem]:
        return self.repository.get_low_stock_items(tenant_id=tenant_id, branch_id=branch_id)

    def deduct_for_order(self, order_items: list, branch_id: str, user_id: str):
        """Deduct inventory for order items based on recipe mapping.

        For now, deducts 1 unit per order item. In a full implementation,
        this would look up recipe_ingredients table for BOM quantities.
        """
        for order_item in order_items:
            menu_item_id = order_item.get("menu_item_id")
            quantity = float(order_item.get("quantity", 1))

            # Look up inventory item by menu_item_id mapping
            # For now, try to find by item_code match
            item_code = order_item.get("item_code")
            if item_code:
                inv_item = self.db.query(InventoryItem).filter(
                    InventoryItem.item_code == item_code,
                    InventoryItem.branch_id == branch_id,
                    InventoryItem.is_trackable == True,
                    InventoryItem.is_active == True
                ).first()

                if inv_item:
                    deduction = quantity  # In full impl: quantity * recipe_bom_qty
                    inv_item.current_stock = float(inv_item.current_stock) - deduction

                    # Create stock movement record
                    movement = StockMovement(
                        id=str(uuid.uuid4()),
                        inventory_item_id=inv_item.id,
                        branch_id=branch_id,
                        movement_type="sale",
                        quantity=deduction,
                        reference_type="order",
                        reference_id=order_item.get("order_id"),
                        created_by=user_id,
                        created_at=datetime.utcnow()
                    )
                    self.db.add(movement)

        self.db.commit()
