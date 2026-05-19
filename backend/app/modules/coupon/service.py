from typing import Optional
from sqlalchemy.orm import Session
from datetime import datetime
from app.models import Coupon
from app.api.exceptions import BadRequestException, NotFoundException


class CouponService:
    def __init__(self, db: Session):
        self.db = db

    def validate_and_apply(self, code: str, tenant_id: str, subtotal: float,
                           branch_id: Optional[str] = None) -> dict:
        coupon = self.db.query(Coupon).filter(
            Coupon.code == code.upper(),
            Coupon.tenant_id == tenant_id,
            Coupon.is_active == True
        ).first()

        if not coupon:
            raise NotFoundException("Coupon not found")

        now = datetime.utcnow()

        # Check validity period
        if coupon.valid_from and coupon.valid_from > now:
            raise BadRequestException("Coupon is not yet valid")
        if coupon.valid_until and coupon.valid_until < now:
            raise BadRequestException("Coupon has expired")

        # Check minimum order value
        if coupon.min_order_value and subtotal < float(coupon.min_order_value):
            raise BadRequestException(
                f"Minimum order value is ₹{float(coupon.min_order_value):.2f}"
            )

        # Check usage limit
        if coupon.max_uses and coupon.uses_count >= coupon.max_uses:
            raise BadRequestException("Coupon usage limit reached")

        # Calculate discount
        if coupon.discount_type == "percentage":
            discount = subtotal * (float(coupon.discount_value) / 100)
            if coupon.max_discount:
                discount = min(discount, float(coupon.max_discount))
        elif coupon.discount_type == "fixed":
            discount = min(float(coupon.discount_value), subtotal)
        else:
            discount = 0.0

        return {
            "coupon_id": str(coupon.id),
            "code": coupon.code,
            "description": coupon.description,
            "discount_type": coupon.discount_type,
            "discount_value": float(coupon.discount_value),
            "discount_amount": round(discount, 2),
            "subtotal": subtotal,
            "total_after_discount": round(subtotal - discount, 2)
        }

    def apply_coupon_usage(self, coupon_id: str):
        """Increment usage count after successful order."""
        coupon = self.db.query(Coupon).filter(Coupon.id == coupon_id).first()
        if coupon:
            coupon.uses_count = (coupon.uses_count or 0) + 1
            self.db.commit()

    def create_coupon(self, data: dict) -> Coupon:
        data["code"] = data.get("code", "").upper()
        db_coupon = Coupon(**data)
        self.db.add(db_coupon)
        self.db.commit()
        self.db.refresh(db_coupon)
        return db_coupon

    def get_coupons(self, tenant_id: str, skip: int = 0, limit: int = 100):
        return self.db.query(Coupon).filter(
            Coupon.tenant_id == tenant_id
        ).offset(skip).limit(limit).all()

    def update_coupon(self, coupon_id: str, data: dict) -> Optional[Coupon]:
        coupon = self.db.query(Coupon).filter(Coupon.id == coupon_id).first()
        if coupon:
            for key, value in data.items():
                setattr(coupon, key, value)
            self.db.commit()
            self.db.refresh(coupon)
        return coupon

    def delete_coupon(self, coupon_id: str) -> bool:
        coupon = self.db.query(Coupon).filter(Coupon.id == coupon_id).first()
        if coupon:
            coupon.is_active = False
            self.db.commit()
            return True
        return False
