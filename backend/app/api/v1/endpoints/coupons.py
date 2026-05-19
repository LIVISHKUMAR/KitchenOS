from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from app.api.dependencies import get_current_user
from app.infrastructure.database import get_db_session
from app.modules.coupon.service import CouponService

router = APIRouter()


class CouponCreate(BaseModel):
    code: str
    description: Optional[str] = None
    discount_type: str  # percentage, fixed
    discount_value: float
    min_order_value: Optional[float] = None
    max_discount: Optional[float] = None
    max_uses: Optional[int] = None
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None


class CouponUpdate(BaseModel):
    description: Optional[str] = None
    discount_value: Optional[float] = None
    min_order_value: Optional[float] = None
    max_discount: Optional[float] = None
    max_uses: Optional[int] = None
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    is_active: Optional[bool] = None


class CouponResponse(BaseModel):
    id: str
    tenant_id: str
    code: str
    description: Optional[str]
    discount_type: str
    discount_value: float
    min_order_value: Optional[float]
    max_discount: Optional[float]
    max_uses: Optional[int]
    uses_count: int
    valid_from: Optional[datetime]
    valid_until: Optional[datetime]
    is_active: bool

    class Config:
        from_attributes = True


@router.post("/", response_model=CouponResponse, status_code=status.HTTP_201_CREATED)
async def create_coupon(
    coupon: CouponCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    coupon_service = CouponService(db)
    data = coupon.model_dump()
    data["tenant_id"] = current_user["tenant_id"]
    return coupon_service.create_coupon(data)


@router.get("/", response_model=List[CouponResponse])
async def list_coupons(
    skip: int = 0,
    limit: int = 100,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    coupon_service = CouponService(db)
    return coupon_service.get_coupons(current_user["tenant_id"], skip=skip, limit=limit)


@router.post("/validate")
async def validate_coupon(
    code: str,
    subtotal: float,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    coupon_service = CouponService(db)
    return coupon_service.validate_and_apply(
        code=code,
        tenant_id=current_user["tenant_id"],
        subtotal=subtotal
    )


@router.put("/{coupon_id}", response_model=CouponResponse)
async def update_coupon(
    coupon_id: str,
    coupon: CouponUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    coupon_service = CouponService(db)
    updated = coupon_service.update_coupon(coupon_id, coupon.model_dump(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=404, detail="Coupon not found")
    return updated


@router.delete("/{coupon_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_coupon(
    coupon_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    coupon_service = CouponService(db)
    if not coupon_service.delete_coupon(coupon_id):
        raise HTTPException(status_code=404, detail="Coupon not found")
    return None
