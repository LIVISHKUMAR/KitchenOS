from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class PaymentBase(BaseModel):
    order_id: str
    amount: float
    payment_method: str
    gateway: Optional[str] = None
    transaction_id: Optional[str] = None
    gateway_reference_id: Optional[str] = None
    status: str = 'pending'
    refund_id: Optional[str] = None
    refund_amount: Optional[float] = None
    refund_reason: Optional[str] = None
    idempotency_key: str
    payment_metadata: Optional[dict] = None


class PaymentCreate(PaymentBase):
    pass


class PaymentUpdate(BaseModel):
    order_id: Optional[str] = None
    amount: Optional[float] = None
    payment_method: Optional[str] = None
    gateway: Optional[str] = None
    transaction_id: Optional[str] = None
    gateway_reference_id: Optional[str] = None
    status: Optional[str] = None
    refund_id: Optional[str] = None
    refund_amount: Optional[float] = None
    refund_reason: Optional[str] = None
    payment_metadata: Optional[dict] = None


class PaymentResponse(PaymentBase):
    id: str
    tenant_id: str
    branch_id: str
    processed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
