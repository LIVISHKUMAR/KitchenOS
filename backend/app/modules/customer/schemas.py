from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime

class CustomerBase(BaseModel):
    name: str
    email: Optional[str] = None
    phone: str
    alternate_phone: Optional[str] = None
    date_of_birth: Optional[date] = None
    anniversary: Optional[date] = None
    loyalty_points: Optional[int] = 0
    wallet_balance: Optional[float] = 0.0
    customer_type: Optional[str] = 'regular'
    membership_tier: Optional[str] = None
    preferences: Optional[dict] = {}
    delivery_addresses: Optional[List[dict]] = []
    is_active: Optional[bool] = True

class CustomerCreate(CustomerBase):
    tenant_id: str

class CustomerUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    alternate_phone: Optional[str] = None
    date_of_birth: Optional[date] = None
    anniversary: Optional[date] = None
    loyalty_points: Optional[int] = None
    wallet_balance: Optional[float] = None
    customer_type: Optional[str] = None
    membership_tier: Optional[str] = None
    preferences: Optional[dict] = None
    delivery_addresses: Optional[List[dict]] = None
    is_active: Optional[bool] = None

class CustomerResponse(CustomerBase):
    id: str
    tenant_id: str
    total_orders: int = 0
    total_spent: float = 0.0
    average_order_value: float = 0.0
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
