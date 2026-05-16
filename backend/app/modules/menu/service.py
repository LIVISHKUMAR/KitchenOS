from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.models import MenuCategory, MenuItem
from app.modules.menu.schemas import MenuCategoryCreate, MenuCategoryUpdate, MenuItemCreate, MenuItemUpdate

class MenuService:
    def __init__(self, db: Session):
        self.db = db
    
    # Category methods
    def create_category(self, category_data: MenuCategoryCreate) -> MenuCategory:
        db_category = MenuCategory(**category_data.dict())
        self.db.add(db_category)
        self.db.commit()
        self.db.refresh(db_category)
        return db_category
    
    def get_category(self, category_id: str) -> Optional[MenuCategory]:
        return self.db.query(MenuCategory).filter(MenuCategory.id == category_id).first()
    
    def get_categories(self, tenant_id: str, branch_id: Optional[str] = None, skip: int = 0, limit: int = 100) -> List[MenuCategory]:
        query = self.db.query(MenuCategory).filter(MenuCategory.tenant_id == tenant_id)
        if branch_id is not None:
            query = query.filter(MenuCategory.branch_id == branch_id)
        return query.offset(skip).limit(limit).all()
    
    def update_category(self, category_id: str, category_data: MenuCategoryUpdate) -> Optional[MenuCategory]:
        db_category = self.get_category(category_id)
        if db_category:
            for field, value in category_data.dict(exclude_unset=True).items():
                setattr(db_category, field, value)
            self.db.commit()
            self.db.refresh(db_category)
        return db_category
    
    def delete_category(self, category_id: str) -> bool:
        db_category = self.get_category(category_id)
        if db_category:
            self.db.delete(db_category)
            self.db.commit()
            return True
        return False
    
    # Item methods
    def create_item(self, item_data: MenuItemCreate) -> MenuItem:
        db_item = MenuItem(**item_data.dict())
        self.db.add(db_item)
        self.db.commit()
        self.db.refresh(db_item)
        return db_item
    
    def get_item(self, item_id: str) -> Optional[MenuItem]:
        return self.db.query(MenuItem).filter(MenuItem.id == item_id).first()
    
    def get_items(self, tenant_id: str, branch_id: Optional[str] = None, category_id: Optional[str] = None, 
                  skip: int = 0, limit: int = 100) -> List[MenuItem]:
        query = self.db.query(MenuItem).filter(MenuItem.tenant_id == tenant_id)
        if branch_id is not None:
            query = query.filter(MenuItem.branch_id == branch_id)
        if category_id is not None:
            query = query.filter(MenuItem.category_id == category_id)
        return query.offset(skip).limit(limit).all()
    
    def update_item(self, item_id: str, item_data: MenuItemUpdate) -> Optional[MenuItem]:
        db_item = self.get_item(item_id)
        if db_item:
            for field, value in item_data.dict(exclude_unset=True).items():
                setattr(db_item, field, value)
            self.db.commit()
            self.db.refresh(db_item)
        return db_item
    
    def delete_item(self, item_id: str) -> bool:
        db_item = self.get_item(item_id)
        if db_item:
            self.db.delete(db_item)
            self.db.commit()
            return True
        return False