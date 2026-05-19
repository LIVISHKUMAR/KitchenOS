"""Complete loyalty engine with auto-earn, redeem, tiers, and expiry."""

import uuid
import logging
from typing import Dict, Optional, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models import Customer, LoyaltyTransaction, Order

logger = logging.getLogger("kitchenos.loyalty")


class LoyaltyEngine:
    """Production loyalty system with tiers, auto-earn, redeem, and expiry."""

    # Tier thresholds
    TIERS = {
        "bronze": {"min_spent": 0, "earn_rate": 0.01, "redeem_rate": 1.0},
        "silver": {"min_spent": 10000, "earn_rate": 0.015, "redeem_rate": 1.0},
        "gold": {"min_spent": 50000, "earn_rate": 0.02, "redeem_rate": 1.2},
        "platinum": {"min_spent": 200000, "earn_rate": 0.025, "redeem_rate": 1.5}
    }

    MIN_REDEEM_POINTS = 50
    POINTS_EXPIRY_DAYS = 365

    def __init__(self, db: Session):
        self.db = db

    def earn_points(self, customer_id: str, order_id: str,
                    order_total: float, tenant_id: str) -> Dict:
        """Auto-earn loyalty points on order completion."""
        customer = self.db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer:
            return {"error": "Customer not found"}

        # Determine tier and earn rate
        tier = self._get_tier(float(customer.total_spent or 0))
        earn_rate = self.TIERS[tier]["earn_rate"]

        # Calculate points (1 point per ₹100 default)
        points = int(order_total * earn_rate * 100)  # 1% of order = 1 point per ₹100

        if points <= 0:
            return {"points_earned": 0, "tier": tier}

        # Create transaction
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

        # Update customer
        customer.loyalty_points = (customer.loyalty_points or 0) + points
        customer.membership_tier = tier

        self.db.commit()

        return {
            "points_earned": points,
            "total_points": customer.loyalty_points,
            "tier": tier,
            "earn_rate": f"{earn_rate * 100}%",
            "expires_at": transaction.expires_at.isoformat()
        }

    def redeem_points(self, customer_id: str, points: int,
                      order_id: str, tenant_id: str) -> Dict:
        """Redeem loyalty points for discount."""
        if points < self.MIN_REDEEM_POINTS:
            return {"error": f"Minimum {self.MIN_REDEEM_POINTS} points required"}

        customer = self.db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer:
            return {"error": "Customer not found"}

        available = customer.loyalty_points or 0
        if points > available:
            return {"error": f"Insufficient points. Available: {available}"}

        # Check non-expired points
        valid_points = self.db.query(func.sum(LoyaltyTransaction.points)).filter(
            LoyaltyTransaction.customer_id == customer_id,
            LoyaltyTransaction.transaction_type == "earn",
            LoyaltyTransaction.points > 0,
            (LoyaltyTransaction.expires_at == None) | (LoyaltyTransaction.expires_at > datetime.utcnow())
        ).scalar() or 0

        if points > valid_points:
            return {"error": f"Insufficient valid points. Available: {valid_points}"}

        # Calculate discount
        tier = self._get_tier(float(customer.total_spent or 0))
        redeem_rate = self.TIERS[tier]["redeem_rate"]
        discount = points * redeem_rate  # 1 point = ₹1 (or more for higher tiers)

        # Create transaction
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

        # Update customer
        customer.loyalty_points = available - points

        self.db.commit()

        return {
            "points_redeemed": points,
            "discount_amount": round(discount, 2),
            "remaining_points": customer.loyalty_points,
            "tier": tier
        }

    def get_balance(self, customer_id: str) -> Dict:
        """Get loyalty balance and tier info."""
        customer = self.db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer:
            return {"error": "Customer not found"}

        tier = self._get_tier(float(customer.total_spent or 0))
        next_tier = self._get_next_tier(float(customer.total_spent or 0))

        # Expiring points (within 30 days)
        expiring = self.db.query(func.sum(LoyaltyTransaction.points)).filter(
            LoyaltyTransaction.customer_id == customer_id,
            LoyaltyTransaction.transaction_type == "earn",
            LoyaltyTransaction.points > 0,
            LoyaltyTransaction.expires_at != None,
            LoyaltyTransaction.expires_at <= datetime.utcnow() + timedelta(days=30),
            LoyaltyTransaction.expires_at > datetime.utcnow()
        ).scalar() or 0

        return {
            "customer_id": str(customer_id),
            "total_points": customer.loyalty_points or 0,
            "points_value": round((customer.loyalty_points or 0) * self.TIERS[tier]["redeem_rate"], 2),
            "tier": tier,
            "tier_benefits": self.TIERS[tier],
            "total_spent": float(customer.total_spent or 0),
            "next_tier": next_tier,
            "expiring_soon": expiring
        }

    def check_birthday(self, customer_id: str) -> Optional[Dict]:
        """Check if today is customer's birthday/anniversary."""
        customer = self.db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer:
            return None

        today = datetime.utcnow().date()

        if customer.date_of_birth:
            dob = customer.date_of_birth
            if dob.month == today.month and dob.day == today.day:
                return {
                    "type": "birthday",
                    "customer_name": customer.name,
                    "phone": customer.phone
                }

        if customer.anniversary:
            ann = customer.anniversary
            if ann.month == today.month and ann.day == today.day:
                return {
                    "type": "anniversary",
                    "customer_name": customer.name,
                    "phone": customer.phone
                }

        return None

    def expire_points(self) -> int:
        """Expire points past their expiry date."""
        expired = self.db.query(LoyaltyTransaction).filter(
            LoyaltyTransaction.transaction_type == "earn",
            LoyaltyTransaction.points > 0,
            LoyaltyTransaction.expires_at != None,
            LoyaltyTransaction.expires_at <= datetime.utcnow()
        ).all()

        count = 0
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
                tx.points = 0
                count += 1

        self.db.commit()
        return count

    def _get_tier(self, total_spent: float) -> str:
        """Determine tier based on total spending."""
        if total_spent >= self.TIERS["platinum"]["min_spent"]:
            return "platinum"
        elif total_spent >= self.TIERS["gold"]["min_spent"]:
            return "gold"
        elif total_spent >= self.TIERS["silver"]["min_spent"]:
            return "silver"
        return "bronze"

    def _get_next_tier(self, total_spent: float) -> Optional[Dict]:
        """Get next tier info."""
        if total_spent < self.TIERS["silver"]["min_spent"]:
            return {"tier": "silver", "spend_needed": self.TIERS["silver"]["min_spent"] - total_spent}
        elif total_spent < self.TIERS["gold"]["min_spent"]:
            return {"tier": "gold", "spend_needed": self.TIERS["gold"]["min_spent"] - total_spent}
        elif total_spent < self.TIERS["platinum"]["min_spent"]:
            return {"tier": "platinum", "spend_needed": self.TIERS["platinum"]["min_spent"] - total_spent}
        return None
