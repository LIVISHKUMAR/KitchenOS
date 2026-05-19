"""Advanced discount endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel
from datetime import datetime
from app.api.dependencies import get_current_user
from app.infrastructure.database import get_db_session
from app.modules.discount.engine import DiscountEngine

router = APIRouter()


class DiscountRuleCreate(BaseModel):
    name: str
    description: str = ""
    rule_type: str  # combo, volume, loyalty, time_limited, flash_sale
    priority: int = 0
    min_quantity: Optional[int] = None
    min_order_value: Optional[float] = None
    applicable_items: list = []
    applicable_to: str = "all"
    customer_tiers: list = []
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    days_of_week: list = []
    discount_type: str  # percentage, fixed, buy_x_get_y
    discount_value: float
    max_discount: Optional[float] = None
    buy_quantity: Optional[int] = None
    get_quantity: Optional[int] = None


@router.post("/rules", status_code=201)
async def create_rule(
    data: DiscountRuleCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    engine = DiscountEngine(db)
    return engine.create_rule(current_user["tenant_id"], data.model_dump())


@router.get("/rules")
async def list_rules(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    engine = DiscountEngine(db)
    return engine.get_rules(current_user["tenant_id"])


@router.post("/calculate")
async def calculate_discount(
    order_data: dict,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Calculate applicable discounts for an order."""
    engine = DiscountEngine(db)
    return engine.calculate_discount(current_user["tenant_id"], order_data)


@router.delete("/rules/{rule_id}")
async def delete_rule(
    rule_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    engine = DiscountEngine(db)
    if not engine.delete_rule(rule_id, current_user["tenant_id"]):
        raise HTTPException(status_code=404, detail="Rule not found")
    return {"message": "Rule deleted"}
