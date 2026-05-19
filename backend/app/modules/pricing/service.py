"""Dynamic pricing engine."""

from typing import Optional, List
from datetime import datetime, time
from sqlalchemy.orm import Session
from sqlalchemy import Column, String, Boolean, JSON, DateTime, Numeric, Integer, Time
from app.infrastructure.database import Base
from app.models import generate_uuid, MenuItem


class PricingRule(Base):
    __tablename__ = "pricing_rules"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    tenant_id = Column(String(36), nullable=False, index=True)
    branch_id = Column(String(36), index=True)
    name = Column(String(100), nullable=False)
    rule_type = Column(String(50), nullable=False)  # happy_hour, surge, seasonal, bulk
    priority = Column(Integer, default=0)  # Higher = applied first

    # Time-based rules
    start_time = Column(Time)
    end_time = Column(Time)
    days_of_week = Column(JSON, default=[])  # [0=Mon, 6=Sun]

    # Pricing
    discount_type = Column(String(20))  # percentage, fixed
    discount_value = Column(Numeric(10, 2))

    # Scope
    applies_to = Column(String(50), default="all")  # all, category, item
    target_ids = Column(JSON, default=[])  # category_ids or item_ids

    # Conditions
    min_quantity = Column(Integer)
    min_order_value = Column(Numeric(10, 2))

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class DynamicPricingService:
    def __init__(self, db: Session):
        self.db = db

    def calculate_price(self, tenant_id: str, branch_id: str,
                        item_id: str, base_price: float, quantity: int = 1,
                        order_time: datetime = None) -> dict:
        """Calculate the final price considering all applicable pricing rules."""
        order_time = order_time or datetime.utcnow()
        current_time = order_time.time()
        current_day = order_time.weekday()

        # Get active pricing rules
        rules = self.db.query(PricingRule).filter(
            PricingRule.tenant_id == tenant_id,
            PricingRule.is_active == True
        ).order_by(PricingRule.priority.desc()).all()

        # Get menu item for category info
        menu_item = self.db.query(MenuItem).filter(MenuItem.id == item_id).first()

        applicable_rules = []

        for rule in rules:
            # Check branch scope
            if rule.branch_id and rule.branch_id != branch_id:
                continue

            # Check time scope
            if rule.start_time and rule.end_time:
                if not (rule.start_time <= current_time <= rule.end_time):
                    continue

            # Check day of week
            if rule.days_of_week and current_day not in rule.days_of_week:
                continue

            # Check quantity threshold
            if rule.min_quantity and quantity < rule.min_quantity:
                continue

            # Check item/category scope
            if rule.applies_to == "item" and item_id not in (rule.target_ids or []):
                continue
            if rule.applies_to == "category" and menu_item:
                if menu_item.category_id not in (rule.target_ids or []):
                    continue

            applicable_rules.append(rule)

        # Apply the highest priority rule
        discount = 0.0
        applied_rule = None

        if applicable_rules:
            rule = applicable_rules[0]  # Highest priority
            if rule.discount_type == "percentage":
                discount = base_price * (float(rule.discount_value) / 100)
            elif rule.discount_type == "fixed":
                discount = min(float(rule.discount_value), base_price)
            applied_rule = {
                "id": str(rule.id),
                "name": rule.name,
                "type": rule.rule_type,
                "discount_type": rule.discount_type,
                "discount_value": float(rule.discount_value)
            }

        final_price = base_price - discount

        return {
            "base_price": base_price,
            "discount": round(discount, 2),
            "final_price": round(final_price, 2),
            "quantity": quantity,
            "total": round(final_price * quantity, 2),
            "applied_rule": applied_rule
        }

    def create_rule(self, tenant_id: str, data: dict) -> PricingRule:
        rule = PricingRule(id=str(uuid.uuid4()), tenant_id=tenant_id, **data)
        self.db.add(rule)
        self.db.commit()
        self.db.refresh(rule)
        return rule

    def get_rules(self, tenant_id: str, branch_id: Optional[str] = None) -> List[PricingRule]:
        query = self.db.query(PricingRule).filter(
            PricingRule.tenant_id == tenant_id,
            PricingRule.is_active == True
        )
        if branch_id:
            query = query.filter(
                (PricingRule.branch_id == branch_id) | (PricingRule.branch_id == None)
            )
        return query.order_by(PricingRule.priority.desc()).all()

    def delete_rule(self, rule_id: str, tenant_id: str) -> bool:
        rule = self.db.query(PricingRule).filter(
            PricingRule.id == rule_id,
            PricingRule.tenant_id == tenant_id
        ).first()
        if rule:
            rule.is_active = False
            self.db.commit()
            return True
        return False
