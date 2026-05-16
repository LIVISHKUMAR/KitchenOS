from typing import List, Optional
from sqlalchemy.orm import Session
from app.models import InventoryItem
import uuid
from datetime import datetime

class InventoryService:
    def __init__(self, db: Session):
        self.db = db
    
    def create_inventory_item(self, item_data: dict) -> InventoryItem:
        db_item = InventoryItem(**item_data)
        self.db.add(db_item)
        self.db.commit()
        self.db.refresh(db_item)
        return db_item
    
    def get_inventory_item(self, item_id: str) -> Optional[InventoryItem]:
        return self.db.query(InventoryItem).filter(InventoryItem.id == item_id).first()
    
    def get_inventory_items(self, tenant_id: str, branch_id: Optional[str] = None, skip: int = 0, limit: int = 100) -> List[InventoryItem]:
        query = self.db.query(InventoryItem).filter(InventoryItem.tenant_id == tenant_id)
        if branch_id is not None:
            query = query.filter(InventoryItem.branch_id == branch_id)
        return query.offset(skip).limit(limit).all()
    
    def update_inventory_item(self, item_id: str, item_data: dict) -> Optional[InventoryItem]:
        db_item = self.get_inventory_item(item_id)
        if db_item:
            for key, value in item_data.items():
                setattr(db_item, key, value)
            self.db.commit()
            self.db.refresh(db_item)
        return db_item
    
    def delete_inventory_item(self, item_id: str) -> bool:
        db_item = self.get_inventory_item(item_id)
        if db_item:
            self.db.delete(db_item)
            self.db.commit()
            return True
        return False
    
    def get_low_stock_items(self, tenant_id: str, branch_id: Optional[str] = None) -> List[InventoryItem]:
        query = self.db.query(InventoryItem).filter(
            InventoryItem.tenant_id == tenant_id,
            InventoryItem.current_stock <= InventoryItem.minimum_stock,
            InventoryItem.is_active == True
        )
        if branch_id is not None:
            query = query.filter(InventoryItem.branch_id == branch_id)
        return query.all()