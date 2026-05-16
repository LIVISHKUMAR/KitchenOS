from typing import List, Optional
from sqlalchemy.orm import Session
from app.models import MenuCategory, MenuItem, MenuVariant, MenuModifierGroup, MenuModifier

class MenuRepository:
    def __init__(self, db: Session):
        self.db = db
    
    # Category methods
    def create_category(self, category: MenuCategory) -> MenuCategory:
        self.db.add(category)
        self.db.commit()
        self.db.refresh(category)
        return category
    
    def get_category(self, category_id: str) -> Optional[MenuCategory]:
        return self.db.query(MenuCategory).filter(MenuCategory.id == category_id).first()
    
    def get_categories(self, tenant_id: str, branch_id: Optional[str] = None, skip: int = 0, limit: int = 100) -> List[MenuCategory]:
        query = self.db.query(MenuCategory).filter(MenuCategory.tenant_id == tenant_id)
        if branch_id is not None:
            query = query.filter(MenuCategory.branch_id == branch_id)
        return query.offset(skip).limit(limit).all()
    
    def update_category(self, category_id: str, category: MenuCategory) -> Optional[MenuCategory]:
        db_category = self.get_category(category_id)
        if db_category:
            for field, value in category.dict(exclude_unset=True).items():
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
    def create_item(self, item: MenuItem) -> MenuItem:
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item
    
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
    
    def update_item(self, item_id: str, item: MenuItem) -> Optional[MenuItem]:
        db_item = self.get_item(item_id)
        if db_item:
            for field, value in item.dict(exclude_unset=True).items():
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
    
    # Variant methods
    def create_variant(self, variant: MenuVariant) -> MenuVariant:
        self.db.add(variant)
        self.db.commit()
        self.db.refresh(variant)
        return variant
    
    def get_variant(self, variant_id: str) -> Optional[MenuVariant]:
        return self.db.query(MenuVariant).filter(MenuVariant.id == variant_id).first()
    
    def get_variants(self, tenant_id: str, menu_item_id: Optional[str] = None, skip: int = 0, limit: int = 100) -> List[MenuVariant]:
        query = self.db.query(MenuVariant).join(MenuItem).filter(MenuItem.tenant_id == tenant_id)
        if menu_item_id is not None:
            query = query.filter(MenuVariant.menu_item_id == menu_item_id)
        return query.offset(skip).limit(limit).all()
    
    def update_variant(self, variant_id: str, variant: MenuVariant) -> Optional[MenuVariant]:
        db_variant = self.get_variant(variant_id)
        if db_variant:
            for field, value in variant.dict(exclude_unset=True).items():
                setattr(db_variant, field, value)
            self.db.commit()
            self.db.refresh(db_variant)
        return db_variant
    
    def delete_variant(self, variant_id: str) -> bool:
        db_variant = self.get_variant(variant_id)
        if db_variant:
            self.db.delete(db_variant)
            self.db.commit()
            return True
        return False
    
    # Modifier group methods
    def create_modifier_group(self, modifier_group: MenuModifierGroup) -> MenuModifierGroup:
        self.db.add(modifier_group)
        self.db.commit()
        self.db.refresh(modifier_group)
        return modifier_group
    
    def get_modifier_group(self, group_id: str) -> Optional[MenuModifierGroup]:
        return self.db.query(MenuModifierGroup).filter(MenuModifierGroup.id == group_id).first()
    
    def get_modifier_groups(self, tenant_id: str, menu_item_id: Optional[str] = None, skip: int = 0, limit: int = 100) -> List[MenuModifierGroup]:
        query = self.db.query(MenuModifierGroup).join(MenuItem).filter(MenuItem.tenant_id == tenant_id)
        if menu_item_id is not None:
            query = query.filter(MenuModifierGroup.menu_item_id == menu_item_id)
        return query.offset(skip).limit(limit).all()
    
    def update_modifier_group(self, group_id: str, modifier_group: MenuModifierGroup) -> Optional[MenuModifierGroup]:
        db_modifier_group = self.get_modifier_group(group_id)
        if db_modifier_group:
            for field, value in modifier_group.dict(exclude_unset=True).items():
                setattr(db_modifier_group, field, value)
            self.db.commit()
            self.db.refresh(db_modifier_group)
        return db_modifier_group
    
    def delete_modifier_group(self, group_id: str) -> bool:
        db_modifier_group = self.get_modifier_group(group_id)
        if db_modifier_group:
            self.db.delete(db_modifier_group)
            self.db.commit()
            return True
        return False
    
    # Modifier methods
    def create_modifier(self, modifier: MenuModifier) -> MenuModifier:
        self.db.add(modifier)
        self.db.commit()
        self.db.refresh(modifier)
        return modifier
    
    def get_modifier(self, modifier_id: str) -> Optional[MenuModifier]:
        return self.db.query(MenuModifier).filter(MenuModifier.id == modifier_id).first()
    
    def get_modifiers(self, tenant_id: str, group_id: Optional[str] = None, skip: int = 0, limit: int = 100) -> List[MenuModifier]:
        query = self.db.query(MenuModifier).join(MenuModifierGroup).join(MenuItem).filter(MenuItem.tenant_id == tenant_id)
        if group_id is not None:
            query = query.filter(MenuModifier.group_id == group_id)
        return query.offset(skip).limit(limit).all()
    
    def update_modifier(self, modifier_id: str, modifier: MenuModifier) -> Optional[MenuModifier]:
        db_modifier = self.get_modifier(modifier_id)
        if db_modifier:
            for field, value in modifier.dict(exclude_unset=True).items():
                setattr(db_modifier, field, value)
            self.db.commit()
            self.db.refresh(db_modifier)
        return db_modifier
    
    def delete_modifier(self, modifier_id: str) -> bool:
        db_modifier = self.get_modifier(modifier_id)
        if db_modifier:
            self.db.delete(db_modifier)
            self.db.commit()
            return True
        return False
