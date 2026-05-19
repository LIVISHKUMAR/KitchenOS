"""Complete loyalty system endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel
from app.api.dependencies import get_current_user
from app.infrastructure.database import get_db_session
from app.modules.loyalty.engine import LoyaltyEngine

router = APIRouter()


class RedeemRequest(BaseModel):
    customer_id: str
    points: int
    order_id: str


@router.get("/balance/{customer_id}")
async def get_balance(
    customer_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Get loyalty balance and tier info."""
    engine = LoyaltyEngine(db)
    return engine.get_balance(customer_id)


@router.post("/earn")
async def earn_points(
    customer_id: str,
    order_id: str,
    order_total: float,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Earn points on order completion."""
    engine = LoyaltyEngine(db)
    return engine.earn_points(
        customer_id=customer_id,
        order_id=order_id,
        order_total=order_total,
        tenant_id=current_user["tenant_id"]
    )


@router.post("/redeem")
async def redeem_points(
    data: RedeemRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Redeem points for discount."""
    engine = LoyaltyEngine(db)
    result = engine.redeem_points(
        customer_id=data.customer_id,
        points=data.points,
        order_id=data.order_id,
        tenant_id=current_user["tenant_id"]
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.get("/birthday-check")
async def check_birthdays(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Check for today's birthdays/anniversaries."""
    engine = LoyaltyEngine(db)
    # Would iterate through customers to find matches
    return {"message": "Run scheduled task to check birthdays"}


@router.post("/expire")
async def expire_points(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Expire old points (admin only)."""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    engine = LoyaltyEngine(db)
    count = engine.expire_points()
    return {"expired": count}
