from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class InventoryItemBase(BaseModel):
    name: str
    item_code: Optional[str] = None
    bar_code: Optional[str] = None
    unit: str = 'pcs'  # kg/liter/pcs/pack
    current_stock: float = 0
    minimum_stock: float = 0
    reorder_level: Optional[float] = None
    reorder_quantity: Optional[float] = None
    cost_price: Optional[float] = None
    selling_price: Optional[float] = None
    supplier_id: Optional[str] = None
    is_trackable: bool = True
    expires_on: Optional[datetime] = None
    shelf_location: Optional[str] = None
    is_active: bool = True

class InventoryItemCreate(InventoryItemBase):
    tenant_id: str
    branch_id: Optional[str] = None
    category_id: Optional[str] = None

class InventoryItemUpdate(BaseModel):
    name: Optional[str] = None
    item_code: Optional[str] = None
    bar_code: Optional[str] = None
    unit: Optional[str] = None
    current_stock: Optional[float] = None
    minimum_stock: Optional[float] = None
    reorder_level: Optional[float] = None
    reorder_quantity: Optional[float] = None
    cost_price: Optional[float] = None
    selling_price: Optional[float] = None
    supplier_id: Optional[str] = None
    is_trackable: Optional[bool] = None
    expires_on: Optional[datetime] = None
    shelf_location: Optional[str] = None
    is_active: Optional[bool] = None

class InventoryItemResponse(InventoryItemBase):
    id: str
    tenant_id: str
    branch_id: Optional[str] = None
    category_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class StockMovementBase(BaseModel):
    movement_type: str  # purchase/sale/adjustment/wastage/transfer/return
    quantity: float  # Positive = in, Negative = out
    reference_type: Optional[str] = None  # order/purchase/adjustment
    reference_id: Optional[str] = None
    batch_number: Optional[str] = None
    expiry_date: Optional[datetime] = None
    notes: Optional[str] = None

class StockMovementCreate(StockMovementBase):
    inventory_item_id: str
    branch_id: Optional[str] = None
    created_by: Optional[str] = None

class StockMovementUpdate(BaseModel):
    movement_type: Optional[str] = None
    quantity: Optional[float] = None
    reference_type: Optional[str] = None
    reference_id: Optional[str] = None
    batch_number: Optional[str] = None
    expiry_date: Optional[datetime] = None
    notes: Optional[str] = None

class StockMovementResponse(StockMovementBase):
    id: str
    inventory_item_id: str
    branch_id: Optional[str] = None
    created_by: Optional[str] = None
    created_at: datetime

    class Config:
        orm_mode = True