from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.api.dependencies import get_current_user
from app.infrastructure.database import get_db_session
from app.modules.loyalty.service import LoyaltyService

router = APIRouter()


class RedeemRequest(BaseModel):
    customer_id: str
    points: int
    order_id: str


@router.get("/balance/{customer_id}")
async def get_loyalty_balance(
    customer_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    loyalty_service = LoyaltyService(db)
    return loyalty_service.get_balance(customer_id)


@router.get("/history/{customer_id}")
async def get_loyalty_history(
    customer_id: str,
    skip: int = 0,
    limit: int = 50,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    loyalty_service = LoyaltyService(db)
    return loyalty_service.get_history(customer_id, skip=skip, limit=limit)


@router.post("/redeem")
async def redeem_points(
    data: RedeemRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    loyalty_service = LoyaltyService(db)
    return loyalty_service.redeem_points(
        customer_id=data.customer_id,
        points=data.points,
        order_id=data.order_id,
        tenant_id=current_user["tenant_id"]
    )


@router.post("/earn/{customer_id}")
async def earn_points(
    customer_id: str,
    order_id: str,
    order_total: float,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    loyalty_service = LoyaltyService(db)
    result = loyalty_service.earn_points(
        customer_id=customer_id,
        order_id=order_id,
        order_total=order_total,
        tenant_id=current_user["tenant_id"]
    )
    if not result:
        raise HTTPException(status_code=400, detail="Could not earn points")
    return result


@router.post("/expire")
async def expire_points(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Expire loyalty points. Admin only."""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    loyalty_service = LoyaltyService(db)
    count = loyalty_service.expire_points()
    return {"expired_transactions": count}
