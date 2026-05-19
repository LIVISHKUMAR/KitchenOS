"""Demand forecasting service."""

from typing import Optional, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, extract, cast, Date

from app.models import Order, OrderItem


class DemandForecastService:
    def __init__(self, db: Session):
        self.db = db

    def get_hourly_pattern(self, tenant_id: str, branch_id: Optional[str] = None,
                           days_back: int = 30) -> list:
        """Get hourly order patterns for staffing optimization."""
        cutoff = datetime.utcnow() - timedelta(days=days_back)

        query = self.db.query(
            extract('hour', Order.created_at).label('hour'),
            func.count(Order.id).label('order_count'),
            func.avg(Order.total).label('avg_order_value')
        ).filter(
            Order.tenant_id == tenant_id,
            Order.created_at >= cutoff,
            Order.status != 'cancelled'
        )

        if branch_id:
            query = query.filter(Order.branch_id == branch_id)

        results = query.group_by(
            extract('hour', Order.created_at)
        ).order_by(
            extract('hour', Order.created_at)
        ).all()

        return [
            {
                "hour": int(r.hour),
                "avg_orders": round(r.order_count / days_back, 1),
                "avg_order_value": round(float(r.avg_order_value or 0), 2),
                "total_orders": r.order_count
            }
            for r in results
        ]

    def get_daily_pattern(self, tenant_id: str, branch_id: Optional[str] = None,
                          weeks_back: int = 4) -> list:
        """Get day-of-week patterns."""
        cutoff = datetime.utcnow() - timedelta(weeks=weeks_back)

        query = self.db.query(
            extract('dow', Order.created_at).label('dow'),
            func.count(Order.id).label('order_count'),
            func.sum(Order.total).label('revenue')
        ).filter(
            Order.tenant_id == tenant_id,
            Order.created_at >= cutoff,
            Order.status != 'cancelled'
        )

        if branch_id:
            query = query.filter(Order.branch_id == branch_id)

        results = query.group_by(
            extract('dow', Order.created_at)
        ).all()

        day_names = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']

        return [
            {
                "day": day_names[int(r.dow)],
                "day_of_week": int(r.dow),
                "avg_orders": round(r.order_count / weeks_back, 1),
                "avg_revenue": round(float(r.revenue or 0) / weeks_back, 2)
            }
            for r in sorted(results, key=lambda x: int(x.dow))
        ]

    def get_peak_hours(self, tenant_id: str, branch_id: Optional[str] = None) -> dict:
        """Identify peak hours for staffing."""
        hourly = self.get_hourly_pattern(tenant_id, branch_id)

        if not hourly:
            return {"peak_hours": [], "slow_hours": []}

        avg_orders = sum(h["avg_orders"] for h in hourly) / len(hourly)

        peak = [h for h in hourly if h["avg_orders"] > avg_orders * 1.5]
        slow = [h for h in hourly if h["avg_orders"] < avg_orders * 0.5]

        return {
            "peak_hours": [{"hour": h["hour"], "label": f"{h['hour']:02d}:00"} for h in peak],
            "slow_hours": [{"hour": h["hour"], "label": f"{h['hour']:02d}:00"} for h in slow],
            "avg_orders_per_hour": round(avg_orders, 1)
        }

    def forecast_demand(self, tenant_id: str, target_date: str,
                        branch_id: Optional[str] = None) -> dict:
        """Forecast demand for a specific date."""
        target = datetime.strptime(target_date, "%Y-%m-%d")
        day_of_week = target.weekday()

        # Get historical data for same day of week
        historical = self.db.query(
            func.count(Order.id).label('orders'),
            func.sum(Order.total).label('revenue')
        ).filter(
            Order.tenant_id == tenant_id,
            extract('dow', Order.created_at) == day_of_week,
            Order.status != 'cancelled'
        )

        if branch_id:
            historical = historical.filter(Order.branch_id == branch_id)

        # Last 4 weeks
        four_weeks_ago = target - timedelta(weeks=4)
        historical = historical.filter(
            Order.created_at >= four_weeks_ago,
            Order.created_at < target
        ).first()

        weeks_of_data = 4
        forecast_orders = round((historical.orders or 0) / weeks_of_data)
        forecast_revenue = round(float(historical.revenue or 0) / weeks_of_data, 2)

        return {
            "target_date": target_date,
            "day_of_week": day_of_week,
            "forecast": {
                "expected_orders": forecast_orders,
                "expected_revenue": forecast_revenue,
                "confidence": "medium"  # Would use ML model in production
            },
            "recommendations": {
                "min_staff": max(2, forecast_orders // 10),
                "recommended_staff": max(3, forecast_orders // 7),
                "prep_start": "2 hours before peak"
            }
        }
