from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


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
        from_attributes = True


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
        from_attributes = True


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
        from_attributes = True


class MenuCategoryBase(BaseModel):
    name: str
    description: Optional[str] = None
    display_order: int = 0
    image_url: Optional[str] = None
    is_active: bool = True


class MenuCategoryCreate(MenuCategoryBase):
    pass


class MenuCategoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    display_order: Optional[int] = None
    image_url: Optional[str] = None
    is_active: Optional[bool] = None


class MenuCategoryResponse(MenuCategoryBase):
    id: str
    tenant_id: str
    created_at: datetime

    class Config:
        from_attributes = True


class MenuItemBase(BaseModel):
    name: str
    description: Optional[str] = None
    base_price: float
    tax_rate: float = 18.0
    is_veg: bool = True
    preparation_time_minutes: int = 15
    is_available: bool = True


class MenuItemCreate(MenuItemBase):
    category_id: str


class MenuItemUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    base_price: Optional[float] = None
    tax_rate: Optional[float] = None
    is_available: Optional[bool] = None


class MenuItemResponse(MenuItemBase):
    id: str
    category_id: str
    tenant_id: str
    created_at: datetime

    class Config:
        from_attributes = True
