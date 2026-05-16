from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    role: str  # admin/manager/cashier/chef/waiter
    is_active: bool = True
    branch_id: Optional[str] = None

class UserCreate(UserBase):
    password: str
    tenant_id: str

class UserUpdate(BaseModel):
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    branch_id: Optional[str] = None

class UserResponse(UserBase):
    id: str
    tenant_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True