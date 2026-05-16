from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime, timedelta

class SalesReportBase(BaseModel):
    branch_id: str
    date: date
    order_count: int
    total_sales: float
    avg_order_value: float

class SalesReportResponse(SalesReportBase):
    id: str
    created_at: datetime

    class Config:
        orm_mode = True

class PopularItemBase(BaseModel):
    menu_item_id: str
    item_name: str
    times_ordered: int
    total_revenue: float

class PopularItemResponse(PopularItemBase):
    id: str
    created_at: datetime

    class Config:
        orm_mode = True

class LoyaltyReportBase(BaseModel):
    customer_id: str
    customer_name: str
    phone: str
    loyalty_points: int
    wallet_balance: float
    total_orders: int
    total_spent: float

class LoyaltyReportResponse(LoyaltyReportBase):
    id: str
    created_at: datetime

    class Config:
        orm_mode = True

class TaxReportBase(BaseModel):
    tax_config_id: str
    tax_name: str
    tax_rate: float
    total_tax_collected: float
    period_start: date
    period_end: date

class TaxReportResponse(TaxReportBase):
    id: str
    created_at: datetime

    class Config:
        orm_mode = True
