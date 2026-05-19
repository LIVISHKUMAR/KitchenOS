"""Dynamic pricing endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel
from datetime import datetime
from app.api.dependencies import get_current_user
from app.infrastructure.database import get_db_session
from app.modules.pricing.service import DynamicPricingService

router = APIRouter()


class PricingRuleCreate(BaseModel):
    name: str
    rule_type: str  # happy_hour, surge, seasonal, bulk
    priority: int = 0
    start_time: Optional[str] = None  # HH:MM
    end_time: Optional[str] = None
    days_of_week: Optional[list] = []
    discount_type: str  # percentage, fixed
    discount_value: float
    applies_to: str = "all"  # all, category, item
    target_ids: Optional[list] = []
    min_quantity: Optional[int] = None
    min_order_value: Optional[float] = None
    branch_id: Optional[str] = None


@router.post("/rules", status_code=201)
async def create_pricing_rule(
    data: PricingRuleCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    pricing_service = DynamicPricingService(db)
    rule_data = data.model_dump()
    if rule_data.get("start_time"):
        rule_data["start_time"] = datetime.strptime(rule_data["start_time"], "%H:%M").time()
    if rule_data.get("end_time"):
        rule_data["end_time"] = datetime.strptime(rule_data["end_time"], "%H:%M").time()
    return pricing_service.create_rule(current_user["tenant_id"], rule_data)


@router.get("/rules")
async def list_pricing_rules(
    branch_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    pricing_service = DynamicPricingService(db)
    return pricing_service.get_rules(current_user["tenant_id"], branch_id)


@router.delete("/rules/{rule_id}")
async def delete_pricing_rule(
    rule_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    pricing_service = DynamicPricingService(db)
    if not pricing_service.delete_rule(rule_id, current_user["tenant_id"]):
        raise HTTPException(status_code=404, detail="Rule not found")
    return {"message": "Rule deleted"}


@router.get("/calculate")
async def calculate_price(
    item_id: str,
    quantity: int = Query(default=1),
    branch_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Calculate dynamic price for an item."""
    from app.models import MenuItem
    pricing_service = DynamicPricingService(db)

    item = db.query(MenuItem).filter(MenuItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    return pricing_service.calculate_price(
        tenant_id=current_user["tenant_id"],
        branch_id=branch_id or current_user.get("branch_id", ""),
        item_id=item_id,
        base_price=float(item.base_price),
        quantity=quantity
    )
