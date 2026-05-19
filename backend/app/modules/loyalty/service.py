"""Loyalty points earn/redeem system."""

from typing import Optional
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import uuid

from app.models import Customer, LoyaltyTransaction, Order
from app.api.exceptions import BadRequestException, NotFoundException


class LoyaltyService:
    def __init__(self, db: Session):
        self.db = db

    # Default: 1 point per ₹100 spent, 1 point = ₹1 discount
    POINTS_PER_RUPEE = 0.01  # 1% of order value
    RUPEES_PER_POINT = 1.0  # Each point is worth ₹1
    MIN_POINTS_TO_REDEEM = 10
    POINTS_EXPIRY_DAYS = 365

    def earn_points(self, customer_id: str, order_id: str, order_total: float, tenant_id: str):
        """Award loyalty points for an order."""
        customer = self.db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer:
            return None

        points = int(order_total * self.POINTS_PER_RUPEE)
        if points <= 0:
            return None

        transaction = LoyaltyTransaction(
            id=str(uuid.uuid4()),
            customer_id=customer_id,
            tenant_id=tenant_id,
            order_id=order_id,
            transaction_type="earn",
            points=points,
            reason=f"Earned from order {order_id}",
            expires_at=datetime.utcnow() + timedelta(days=self.POINTS_EXPIRY_DAYS),
            created_at=datetime.utcnow()
        )
        self.db.add(transaction)

        customer.loyalty_points = (customer.loyalty_points or 0) + points
        self.db.commit()

        return {
            "points_earned": points,
            "total_points": customer.loyalty_points,
            "expires_at": transaction.expires_at.isoformat()
        }

    def redeem_points(self, customer_id: str, points: int, order_id: str, tenant_id: str) -> dict:
        """Redeem loyalty points for discount."""
        if points < self.MIN_POINTS_TO_REDEEM:
            raise BadRequestException(f"Minimum {self.MIN_POINTS_TO_REDEEM} points required to redeem")

        customer = self.db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer:
            raise NotFoundException("Customer not found")

        available_points = customer.loyalty_points or 0
        if points > available_points:
            raise BadRequestException(f"Insufficient points. Available: {available_points}")

        # Check for non-expired points
        valid_points = self.db.query(LoyaltyTransaction).filter(
            LoyaltyTransaction.customer_id == customer_id,
            LoyaltyTransaction.transaction_type == "earn",
            LoyaltyTransaction.points > 0,
            (LoyaltyTransaction.expires_at == None) | (LoyaltyTransaction.expires_at > datetime.utcnow())
        ).all()

        total_valid = sum(t.points for t in valid_points)
        if points > total_valid:
            raise BadRequestException(f"Insufficient valid points. Available: {total_valid}")

        discount = points * self.RUPEES_PER_POINT

        transaction = LoyaltyTransaction(
            id=str(uuid.uuid4()),
            customer_id=customer_id,
            tenant_id=tenant_id,
            order_id=order_id,
            transaction_type="redeem",
            points=-points,
            reason=f"Redeemed for order {order_id}",
            created_at=datetime.utcnow()
        )
        self.db.add(transaction)

        customer.loyalty_points = available_points - points
        self.db.commit()

        return {
            "points_redeemed": points,
            "discount_amount": discount,
            "remaining_points": customer.loyalty_points
        }

    def get_balance(self, customer_id: str) -> dict:
        """Get customer's loyalty points balance."""
        customer = self.db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer:
            raise NotFoundException("Customer not found")

        # Get expiring points (within 30 days)
        expiring_soon = self.db.query(LoyaltyTransaction).filter(
            LoyaltyTransaction.customer_id == customer_id,
            LoyaltyTransaction.transaction_type == "earn",
            LoyaltyTransaction.points > 0,
            LoyaltyTransaction.expires_at != None,
            LoyaltyTransaction.expires_at <= datetime.utcnow() + timedelta(days=30),
            LoyaltyTransaction.expires_at > datetime.utcnow()
        ).all()

        return {
            "customer_id": str(customer_id),
            "total_points": customer.loyalty_points or 0,
            "points_value": (customer.loyalty_points or 0) * self.RUPEES_PER_POINT,
            "expiring_soon": sum(t.points for t in expiring_soon),
            "customer_type": customer.customer_type,
            "membership_tier": customer.membership_tier
        }

    def get_history(self, customer_id: str, skip: int = 0, limit: int = 50):
        """Get loyalty transaction history."""
        transactions = self.db.query(LoyaltyTransaction).filter(
            LoyaltyTransaction.customer_id == customer_id
        ).order_by(
            LoyaltyTransaction.created_at.desc()
        ).offset(skip).limit(limit).all()

        return [
            {
                "id": str(t.id),
                "type": t.transaction_type,
                "points": t.points,
                "reason": t.reason,
                "order_id": str(t.order_id) if t.order_id else None,
                "expires_at": t.expires_at.isoformat() if t.expires_at else None,
                "created_at": t.created_at.isoformat() if t.created_at else None
            }
            for t in transactions
        ]

    def expire_points(self):
        """Expire loyalty points that have passed their expiry date. Run as scheduled task."""
        expired = self.db.query(LoyaltyTransaction).filter(
            LoyaltyTransaction.transaction_type == "earn",
            LoyaltyTransaction.points > 0,
            LoyaltyTransaction.expires_at != None,
            LoyaltyTransaction.expires_at <= datetime.utcnow()
        ).all()

        for tx in expired:
            customer = self.db.query(Customer).filter(Customer.id == tx.customer_id).first()
            if customer:
                customer.loyalty_points = max(0, (customer.loyalty_points or 0) - tx.points)

                expire_tx = LoyaltyTransaction(
                    id=str(uuid.uuid4()),
                    customer_id=tx.customer_id,
                    tenant_id=tx.tenant_id,
                    transaction_type="expire",
                    points=-tx.points,
                    reason="Points expired",
                    created_at=datetime.utcnow()
                )
                self.db.add(expire_tx)
                tx.points = 0  # Mark as processed

        self.db.commit()
        return len(expired)
