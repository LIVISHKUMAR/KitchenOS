"""Cohort analysis service."""

from typing import Optional, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, extract

from app.models import Order, Customer


class CohortAnalysisService:
    def __init__(self, db: Session):
        self.db = db

    def get_retention_cohorts(self, tenant_id: str, months_back: int = 6) -> dict:
        """Get customer retention cohorts."""
        now = datetime.utcnow()
        cohorts = {}

        for i in range(months_back):
            month_start = now - timedelta(days=30 * (i + 1))
            month_end = now - timedelta(days=30 * i)

            # Customers who first ordered in this month
            cohort_customers = self.db.query(Customer.id).filter(
                Customer.tenant_id == tenant_id,
                Customer.created_at >= month_start,
                Customer.created_at < month_end
            ).all()

            if not cohort_customers:
                continue

            cohort_ids = [str(c.id) for c in cohort_customers]
            cohort_size = len(cohort_ids)

            # Track retention in subsequent months
            retention = {}
            for j in range(i + 1):
                check_start = now - timedelta(days=30 * j)
                check_end = now - timedelta(days=30 * (j - 1)) if j > 0 else now

                active = self.db.query(func.count(func.distinct(Order.customer_id))).filter(
                    Order.tenant_id == tenant_id,
                    Order.customer_id.in_(cohort_ids),
                    Order.created_at >= check_start,
                    Order.created_at < check_end,
                    Order.status != "cancelled"
                ).scalar() or 0

                retention[f"month_{j}"] = {
                    "active": active,
                    "rate": round((active / cohort_size) * 100, 1)
                }

            cohort_label = month_start.strftime("%Y-%m")
            cohorts[cohort_label] = {
                "cohort_size": cohort_size,
                "retention": retention
            }

        return cohorts

    def get_revenue_cohorts(self, tenant_id: str, months_back: int = 6) -> dict:
        """Get revenue cohorts."""
        now = datetime.utcnow()
        cohorts = {}

        for i in range(months_back):
            month_start = now - timedelta(days=30 * (i + 1))
            month_end = now - timedelta(days=30 * i)

            # Revenue from new customers in this month
            new_customer_revenue = self.db.query(
                func.sum(Order.total)
            ).join(
                Customer, Order.customer_id == Customer.id
            ).filter(
                Order.tenant_id == tenant_id,
                Customer.created_at >= month_start,
                Customer.created_at < month_end,
                Order.status != "cancelled"
            ).scalar() or 0

            # Revenue from returning customers
            returning_revenue = self.db.query(
                func.sum(Order.total)
            ).join(
                Customer, Order.customer_id == Customer.id
            ).filter(
                Order.tenant_id == tenant_id,
                Customer.created_at < month_start,
                Order.created_at >= month_start,
                Order.created_at < month_end,
                Order.status != "cancelled"
            ).scalar() or 0

            cohort_label = month_start.strftime("%Y-%m")
            cohorts[cohort_label] = {
                "new_customer_revenue": round(float(new_customer_revenue), 2),
                "returning_customer_revenue": round(float(returning_revenue), 2),
                "total_revenue": round(float(new_customer_revenue) + float(returning_revenue), 2)
            }

        return cohorts

    def get_behavior_cohorts(self, tenant_id: str) -> dict:
        """Get behavior-based cohorts."""
        now = datetime.utcnow()

        # Define cohorts based on order frequency
        cohorts = {
            "power_users": {"min_orders": 10, "customers": []},
            "regular_users": {"min_orders": 3, "max_orders": 9, "customers": []},
            "occasional_users": {"min_orders": 1, "max_orders": 2, "customers": []},
            "one_time_users": {"min_orders": 1, "max_orders": 1, "customers": []}
        }

        # Get all customers with order counts
        customer_orders = self.db.query(
            Customer.id,
            Customer.name,
            func.count(Order.id).label("order_count"),
            func.sum(Order.total).label("total_spent")
        ).join(
            Order, Customer.id == Order.customer_id
        ).filter(
            Customer.tenant_id == tenant_id,
            Order.status != "cancelled",
            Order.created_at >= now - timedelta(days=90)
        ).group_by(
            Customer.id, Customer.name
        ).all()

        for c in customer_orders:
            customer_data = {
                "id": str(c.id),
                "name": c.name,
                "orders": c.order_count,
                "spent": round(float(c.total_spent or 0), 2)
            }

            if c.order_count >= 10:
                cohorts["power_users"]["customers"].append(customer_data)
            elif c.order_count >= 3:
                cohorts["regular_users"]["customers"].append(customer_data)
            elif c.order_count >= 2:
                cohorts["occasional_users"]["customers"].append(customer_data)
            else:
                cohorts["one_time_users"]["customers"].append(customer_data)

        # Add counts
        for key in cohorts:
            cohorts[key]["count"] = len(cohorts[key]["customers"])

        return cohorts
