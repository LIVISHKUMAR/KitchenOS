from typing import List, Optional
from sqlalchemy.orm import Session
from app.models import MenuCategory, MenuItem, MenuVariant, MenuModifierGroup, MenuModifier


class MenuRepository:
    def __init__(self, db: Session):
        self.db = db

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

    def update_variant(self, variant_id: str, update_data: dict) -> Optional[MenuVariant]:
        db_variant = self.get_variant(variant_id)
        if db_variant:
            for field, value in update_data.items():
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

    def update_modifier_group(self, group_id: str, update_data: dict) -> Optional[MenuModifierGroup]:
        db_modifier_group = self.get_modifier_group(group_id)
        if db_modifier_group:
            for field, value in update_data.items():
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

    def update_modifier(self, modifier_id: str, update_data: dict) -> Optional[MenuModifier]:
        db_modifier = self.get_modifier(modifier_id)
        if db_modifier:
            for field, value in update_data.items():
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
