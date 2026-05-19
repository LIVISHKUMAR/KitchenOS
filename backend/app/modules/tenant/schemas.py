from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class TenantBase(BaseModel):
    name: str
    slug: str
    logo_url: Optional[str] = None
    phone: Optional[str] = None
    email: str
    subscription_plan: Optional[str] = 'basic'
    subscription_status: Optional[str] = 'trial'
    max_branches: Optional[int] = 1
    max_users: Optional[int] = 10
    max_terminals: Optional[int] = 5
    settings: Optional[dict] = {}
    is_active: Optional[bool] = True


class TenantCreate(TenantBase):
    pass


class TenantUpdate(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None
    logo_url: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    subscription_plan: Optional[str] = None
    subscription_status: Optional[str] = None
    max_branches: Optional[int] = None
    max_users: Optional[int] = None
    max_terminals: Optional[int] = None
    settings: Optional[dict] = None
    is_active: Optional[bool] = None


class TenantResponse(TenantBase):
    id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
