from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class OrderItemBase(BaseModel):
    menu_item_id: str
    item_name: str
    item_code: Optional[str] = None
    quantity: float = 1
    unit_price: float
    tax_amount: float = 0
    discount_amount: float = 0
    total: float
    variant_id: Optional[str] = None
    variant_name: Optional[str] = None
    modifiers: Optional[List[dict]] = []
    cooking_instructions: Optional[str] = None
    course_type: Optional[str] = None
    prep_status: Optional[str] = 'pending'
    priority: Optional[str] = 'normal'

class OrderItemCreate(OrderItemBase):
    pass

class OrderItemUpdate(BaseModel):
    menu_item_id: Optional[str] = None
    item_name: Optional[str] = None
    item_code: Optional[str] = None
    quantity: Optional[float] = None
    unit_price: Optional[float] = None
    tax_amount: Optional[float] = None
    discount_amount: Optional[float] = None
    total: Optional[float] = None
    variant_id: Optional[str] = None
    variant_name: Optional[str] = None
    modifiers: Optional[List[dict]] = None
    cooking_instructions: Optional[str] = None
    course_type: Optional[str] = None
    prep_status: Optional[str] = None
    priority: Optional[str] = None

class OrderItemResponse(OrderItemBase):
    id: str
    order_id: str
    created_at: datetime

    class Config:
        orm_mode = True

class OrderBase(BaseModel):
    order_number: str
    tenant_id: str
    branch_id: str
    table_id: Optional[str] = None
    order_type: str  # dine_in/takeaway/delivery/qr
    status: str = 'pending'  # pending → confirmed → preparing → ready → completed → cancelled
    customer_id: Optional[str] = None
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    subtotal: float = 0
    tax_amount: float = 0
    discount_amount: float = 0
    tip_amount: float = 0
    total: float = 0
    payment_status: str = 'pending'  # pending/partial/paid/refunded
    special_instructions: Optional[str] = None
    source: str = 'pos'  # pos/kds/qr/aggregator
    delivery_address: Optional[dict] = None
    delivery_partner: Optional[str] = None
    aggregator_order_id: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_by: Optional[str] = None
    assigned_to: Optional[str] = None

class OrderCreate(OrderBase):
    items: List[OrderItemCreate]

class OrderUpdate(BaseModel):
    order_number: Optional[str] = None
    tenant_id: Optional[str] = None
    branch_id: Optional[str] = None
    table_id: Optional[str] = None
    order_type: Optional[str] = None
    status: Optional[str] = None
    customer_id: Optional[str] = None
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    subtotal: Optional[float] = None
    tax_amount: Optional[float] = None
    discount_amount: Optional[float] = None
    tip_amount: Optional[float] = None
    total: Optional[float] = None
    payment_status: Optional[str] = None
    special_instructions: Optional[str] = None
    source: Optional[str] = None
    delivery_address: Optional[dict] = None
    delivery_partner: Optional[str] = None
    aggregator_order_id: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_by: Optional[str] = None
    assigned_to: Optional[str] = None

class OrderResponse(OrderBase):
    id: str
    items: List[OrderItemResponse] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True