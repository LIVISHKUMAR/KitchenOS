"""Advanced discount rules engine."""

from typing import List, Optional, Dict
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import Column, String, Boolean, JSON, DateTime, Numeric, Integer
import uuid

from app.infrastructure.database import Base
from app.models import generate_uuid


class DiscountRule(Base):
    __tablename__ = "discount_rules"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    tenant_id = Column(String(36), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    description = Column(String(255))
    rule_type = Column(String(50), nullable=False)  # combo, volume, loyalty, time_limited, flash_sale
    priority = Column(Integer, default=0)

    # Conditions
    min_quantity = Column(Integer)
    min_order_value = Column(Numeric(10, 2))
    applicable_items = Column(JSON, default=[])  # item_ids or category_ids
    applicable_to = Column(String(20), default="all")  # all, items, categories
    customer_tiers = Column(JSON, default=[])  # loyalty tiers

    # Time conditions
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    days_of_week = Column(JSON, default=[])

    # Discount
    discount_type = Column(String(20))  # percentage, fixed, buy_x_get_y
    discount_value = Column(Numeric(10, 2))
    max_discount = Column(Numeric(10, 2))

    # Buy X Get Y
    buy_quantity = Column(Integer)
    get_quantity = Column(Integer)

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class DiscountEngine:
    def __init__(self, db: Session):
        self.db = db

    def calculate_discount(self, tenant_id: str, order_data: Dict) -> Dict:
        """Calculate applicable discounts for an order."""
        now = datetime.utcnow()
        applicable_discounts = []

        # Get active rules
        rules = self.db.query(DiscountRule).filter(
            DiscountRule.tenant_id == tenant_id,
            DiscountRule.is_active == True
        ).order_by(DiscountRule.priority.desc()).all()

        for rule in rules:
            if self._is_rule_applicable(rule, order_data, now):
                discount = self._calculate_rule_discount(rule, order_data)
                if discount > 0:
                    applicable_discounts.append({
                        "rule_id": str(rule.id),
                        "rule_name": rule.name,
                        "rule_type": rule.rule_type,
                        "discount_type": rule.discount_type,
                        "discount": round(discount, 2)
                    })

        # Apply best discount only
        if applicable_discounts:
            best = max(applicable_discounts, key=lambda x: x["discount"])
            return {
                "applied_discount": best,
                "all_eligible": applicable_discounts,
                "total_discount": best["discount"]
            }

        return {"applied_discount": None, "all_eligible": [], "total_discount": 0}

    def _is_rule_applicable(self, rule: DiscountRule, order_data: Dict, now: datetime) -> bool:
        """Check if a rule is applicable to the order."""
        # Check time conditions
        if rule.start_time and rule.end_time:
            if not (rule.start_time <= now <= rule.end_time):
                return False

        if rule.days_of_week and now.weekday() not in rule.days_of_week:
            return False

        # Check minimum order value
        if rule.min_order_value:
            subtotal = order_data.get("subtotal", 0)
            if subtotal < float(rule.min_order_value):
                return False

        # Check minimum quantity
        if rule.min_quantity:
            total_qty = sum(item.get("quantity", 0) for item in order_data.get("items", []))
            if total_qty < rule.min_quantity:
                return False

        # Check customer tier
        if rule.customer_tiers:
            customer_tier = order_data.get("customer_tier")
            if customer_tier not in rule.customer_tiers:
                return False

        # Check applicable items
        if rule.applicable_items and rule.applicable_to != "all":
            order_items = order_data.get("items", [])
            has_applicable = False
            for item in order_items:
                if rule.applicable_to == "items" and item.get("item_id") in rule.applicable_items:
                    has_applicable = True
                elif rule.applicable_to == "categories" and item.get("category_id") in rule.applicable_items:
                    has_applicable = True
            if not has_applicable:
                return False

        return True

    def _calculate_rule_discount(self, rule: DiscountRule, order_data: Dict) -> float:
        """Calculate discount amount for a rule."""
        subtotal = order_data.get("subtotal", 0)

        if rule.discount_type == "percentage":
            discount = subtotal * (float(rule.discount_value) / 100)
            if rule.max_discount:
                discount = min(discount, float(rule.max_discount))
            return discount

        elif rule.discount_type == "fixed":
            return min(float(rule.discount_value), subtotal)

        elif rule.discount_type == "buy_x_get_y":
            # Calculate free items
            items = order_data.get("items", [])
            free_discount = 0
            for item in items:
                qty = item.get("quantity", 0)
                if qty >= (rule.buy_quantity or 1):
                    free_count = (qty // (rule.buy_quantity or 1)) * (rule.get_quantity or 1)
                    free_discount += free_count * item.get("unit_price", 0)
            return free_discount

        return 0

    def create_rule(self, tenant_id: str, data: Dict) -> DiscountRule:
        rule = DiscountRule(id=str(uuid.uuid4()), tenant_id=tenant_id, **data)
        self.db.add(rule)
        self.db.commit()
        self.db.refresh(rule)
        return rule

    def get_rules(self, tenant_id: str) -> List[DiscountRule]:
        return self.db.query(DiscountRule).filter(
            DiscountRule.tenant_id == tenant_id,
            DiscountRule.is_active == True
        ).order_by(DiscountRule.priority.desc()).all()

    def delete_rule(self, rule_id: str, tenant_id: str) -> bool:
        rule = self.db.query(DiscountRule).filter(
            DiscountRule.id == rule_id,
            DiscountRule.tenant_id == tenant_id
        ).first()
        if rule:
            rule.is_active = False
            self.db.commit()
            return True
        return False
