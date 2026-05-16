from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

# Menu Variant Schemas
class MenuVariantBase(BaseModel):
    name: str
    price_adjustment: float = 0
    is_default: Optional[bool] = False
    is_active: Optional[bool] = True

class MenuVariantCreate(MenuVariantBase):
    menu_item_id: str

class MenuVariantUpdate(BaseModel):
    name: Optional[str] = None
    price_adjustment: Optional[float] = None
    is_default: Optional[bool] = None
    is_active: Optional[bool] = None

class MenuVariantResponse(MenuVariantBase):
    id: str
    menu_item_id: str
    created_at: datetime

    class Config:
        orm_mode = True

# Menu Modifier Group Schemas
class MenuModifierGroupBase(BaseModel):
    name: str
    min_selections: Optional[int] = 0
    max_selections: Optional[int] = 1
    is_required: Optional[bool] = False
    display_order: Optional[int] = 0
    is_active: Optional[bool] = True

class MenuModifierGroupCreate(MenuModifierGroupBase):
    menu_item_id: str

class MenuModifierGroupUpdate(BaseModel):
    name: Optional[str] = None
    min_selections: Optional[int] = None
    max_selections: Optional[int] = None
    is_required: Optional[bool] = None
    display_order: Optional[int] = None
    is_active: Optional[bool] = None

class MenuModifierGroupResponse(MenuModifierGroupBase):
    id: str
    menu_item_id: str

    class Config:
        orm_mode = True

# Menu Modifier Schemas
class MenuModifierBase(BaseModel):
    name: str
    price: float = 0
    is_default: Optional[bool] = False
    is_active: Optional[bool] = True

class MenuModifierCreate(MenuModifierBase):
    group_id: str

class MenuModifierUpdate(BaseModel):
    name: Optional[str] = None
    price: Optional[float] = None
    is_default: Optional[bool] = None
    is_active: Optional[bool] = None

class MenuModifierResponse(MenuModifierBase):
    id: str
    group_id: str

    class Config:
        orm_mode = True
