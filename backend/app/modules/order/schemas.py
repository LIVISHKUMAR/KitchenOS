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
    total: float = 0
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
        from_attributes = True


class OrderBase(BaseModel):
    order_type: str
    table_id: Optional[str] = None
    customer_id: Optional[str] = None
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    special_instructions: Optional[str] = None
    source: str = 'pos'


class OrderCreate(OrderBase):
    branch_id: Optional[str] = None
    items: List[OrderItemCreate]
    discount_amount: Optional[float] = 0


class OrderUpdate(BaseModel):
    order_type: Optional[str] = None
    status: Optional[str] = None
    table_id: Optional[str] = None
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


class OrderResponse(BaseModel):
    id: str
    order_number: str
    tenant_id: str
    branch_id: str
    table_id: Optional[str] = None
    order_type: str
    status: str
    customer_id: Optional[str] = None
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    subtotal: float = 0
    tax_amount: float = 0
    discount_amount: float = 0
    tip_amount: float = 0
    total: float = 0
    payment_status: str = 'pending'
    special_instructions: Optional[str] = None
    source: str = 'pos'
    delivery_address: Optional[dict] = None
    delivery_partner: Optional[str] = None
    aggregator_order_id: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_by: Optional[str] = None
    assigned_to: Optional[str] = None
    items: List[OrderItemResponse] = []
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
