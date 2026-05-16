from typing import List, Optional
from sqlalchemy.orm import Session
from app.models import InventoryItem

class InventoryRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, item: InventoryItem) -> InventoryItem:
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item
    
    def get(self, item_id: str) -> Optional[InventoryItem]:
        return self.db.query(InventoryItem).filter(InventoryItem.id == item_id).first()
    
    def get_all(self, tenant_id: str, branch_id: Optional[str] = None, skip: int = 0, limit: int = 100) -> List[InventoryItem]:
        query = self.db.query(InventoryItem).filter(InventoryItem.tenant_id == tenant_id)
        if branch_id is not None:
            query = query.filter(InventoryItem.branch_id == branch_id)
        return query.offset(skip).limit(limit).all()
    
    def update(self, item_id: str, item: InventoryItem) -> Optional[InventoryItem]:
        db_item = self.get(item_id)
        if db_item:
            for key, value in item.dict(exclude_unset=True).items():
                setattr(db_item, key, value)
            self.db.commit()
            self.db.refresh(db_item)
        return db_item
    
    def delete(self, item_id: str) -> bool:
        db_item = self.get(item_id)
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