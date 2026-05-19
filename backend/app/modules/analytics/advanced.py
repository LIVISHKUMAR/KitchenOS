"""Advanced customer analytics."""

from typing import Optional, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, cast, Date

from app.models import Order, Customer, OrderItem


class AdvancedAnalyticsService:
    def __init__(self, db: Session):
        self.db = db

    def get_customer_lifetime_value(self, tenant_id: str) -> list:
        """Calculate customer lifetime value."""
        customers = self.db.query(Customer).filter(
            Customer.tenant_id == tenant_id,
            Customer.total_orders > 0
        ).all()

        results = []
        for c in customers:
            orders = self.db.query(Order).filter(
                Order.customer_id == c.id,
                Order.status != "cancelled"
            ).all()

            if not orders:
                continue

            total_spent = sum(float(o.total) for o in orders)
            avg_order = total_spent / len(orders)
            first_order = min(o.created_at for o in orders)
            last_order = max(o.created_at for o in orders)
            days_active = (last_order - first_order).days or 1

            # Simple CLV: avg_order * frequency * lifespan
            frequency = len(orders) / max(days_active / 30, 1)  # orders per month
            lifespan_months = max(days_active / 30, 1)
            clv = avg_order * frequency * lifespan_months

            results.append({
                "customer_id": str(c.id),
                "name": c.name,
                "total_orders": len(orders),
                "total_spent": round(total_spent, 2),
                "avg_order_value": round(avg_order, 2),
                "frequency_per_month": round(frequency, 1),
                "lifespan_days": days_active,
                "clv": round(clv, 2)
            })

        return sorted(results, key=lambda x: x["clv"], reverse=True)

    def get_rfm_segmentation(self, tenant_id: str) -> dict:
        """RFM (Recency, Frequency, Monetary) segmentation."""
        customers = self.db.query(Customer).filter(
            Customer.tenant_id == tenant_id,
            Customer.total_orders > 0
        ).all()

        now = datetime.utcnow()
        segments = {"champions": [], "loyal": [], "at_risk": [], "lost": []}

        for c in customers:
            last_order = self.db.query(Order).filter(
                Order.customer_id == c.id,
                Order.status != "cancelled"
            ).order_by(Order.created_at.desc()).first()

            if not last_order:
                continue

            recency = (now - last_order.created_at).days
            frequency = c.total_orders or 0
            monetary = float(c.total_spent or 0)

            # Simple segmentation
            if recency <= 30 and frequency >= 5 and monetary >= 5000:
                segment = "champions"
            elif recency <= 90 and frequency >= 3:
                segment = "loyal"
            elif recency <= 180:
                segment = "at_risk"
            else:
                segment = "lost"

            segments[segment].append({
                "customer_id": str(c.id),
                "name": c.name,
                "recency_days": recency,
                "frequency": frequency,
                "monetary": round(monetary, 2)
            })

        return {
            "champions": len(segments["champions"]),
            "loyal": len(segments["loyal"]),
            "at_risk": len(segments["at_risk"]),
            "lost": len(segments["lost"]),
            "details": segments
        }

    def get_retention_metrics(self, tenant_id: str) -> dict:
        """Customer retention metrics."""
        now = datetime.utcnow()
        month_ago = now - timedelta(days=30)
        three_months_ago = now - timedelta(days=90)

        # New customers this month
        new_customers = self.db.query(Customer).filter(
            Customer.tenant_id == tenant_id,
            Customer.created_at >= month_ago
        ).count()

        # Returning customers (ordered this month AND before this month)
        returning = self.db.query(func.count(func.distinct(Order.customer_id))).filter(
            Order.tenant_id == tenant_id,
            Order.created_at >= month_ago,
            Order.status != "cancelled",
            Order.customer_id.in_(
                self.db.query(Order.customer_id).filter(
                    Order.tenant_id == tenant_id,
                    Order.created_at < month_ago,
                    Order.status != "cancelled"
                )
            )
        ).scalar() or 0

        # Total active customers
        active = self.db.query(func.count(func.distinct(Order.customer_id))).filter(
            Order.tenant_id == tenant_id,
            Order.created_at >= three_months_ago,
            Order.status != "cancelled"
        ).scalar() or 0

        return {
            "new_customers_this_month": new_customers,
            "returning_customers": returning,
            "active_customers_90d": active,
            "retention_rate": round((returning / max(active, 1)) * 100, 1)
        }
