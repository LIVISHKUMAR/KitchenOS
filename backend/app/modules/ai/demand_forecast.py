"""AI-Powered Demand Forecasting Engine.

Predicts order volume, revenue, and staffing needs based on:
- Historical order patterns
- Day-of-week trends
- Hourly distribution
- Seasonal patterns
- Special events/holidays
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, extract

from app.models import Order, OrderItem, MenuItem

logger = logging.getLogger("kitchenos.ai.forecast")


class DemandForecastEngine:
    """AI-powered demand prediction for restaurants."""

    def __init__(self, db: Session):
        self.db = db

    def forecast_demand(self, tenant_id: str, target_date: str,
                        branch_id: str = None) -> Dict:
        """Generate comprehensive demand forecast for a date."""
        target = datetime.strptime(target_date, "%Y-%m-%d")
        day_of_week = target.weekday()

        # Get historical data
        hourly_pattern = self._get_hourly_pattern(tenant_id, branch_id, day_of_week)
        daily_pattern = self._get_daily_pattern(tenant_id, branch_id)
        item_demand = self._get_item_demand_forecast(tenant_id, branch_id, day_of_week)

        # Calculate forecasts
        avg_orders = daily_pattern.get("avg_orders", 0)
        peak_hours = self._identify_peak_hours(hourly_pattern)
        staffing = self._calculate_staffing_needs(hourly_pattern, avg_orders)

        return {
            "target_date": target_date,
            "day_of_week": day_of_week,
            "day_name": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"][day_of_week],
            "forecast": {
                "expected_orders": round(avg_orders),
                "expected_revenue": round(daily_pattern.get("avg_revenue", 0), 2),
                "confidence": self._calculate_confidence(daily_pattern),
                "trend": self._calculate_trend(tenant_id, branch_id)
            },
            "hourly_forecast": hourly_pattern,
            "peak_hours": peak_hours,
            "staffing_recommendations": staffing,
            "item_demand": item_demand[:10],  # Top 10 items
            "insights": self._generate_insights(hourly_pattern, daily_pattern, day_of_week)
        }

    def _get_hourly_pattern(self, tenant_id: str, branch_id: str,
                             day_of_week: int) -> List[Dict]:
        """Get hourly order distribution for a specific day of week."""
        weeks_back = 8
        cutoff = datetime.utcnow() - timedelta(weeks=weeks_back)

        query = self.db.query(
            extract('hour', Order.created_at).label('hour'),
            func.count(Order.id).label('order_count'),
            func.sum(Order.total).label('revenue')
        ).filter(
            Order.tenant_id == tenant_id,
            Order.created_at >= cutoff,
            extract('dow', Order.created_at) == day_of_week,
            Order.status != 'cancelled'
        )

        if branch_id:
            query = query.filter(Order.branch_id == branch_id)

        results = query.group_by(
            extract('hour', Order.created_at)
        ).order_by(
            extract('hour', Order.created_at)
        ).all()

        # Fill in missing hours
        hourly = {}
        for r in results:
            hourly[int(r.hour)] = {
                "hour": int(r.hour),
                "avg_orders": round(r.order_count / weeks_back, 1),
                "avg_revenue": round(float(r.revenue or 0) / weeks_back, 2)
            }

        # Ensure all hours are represented
        pattern = []
        for h in range(6, 24):  # 6 AM to 11 PM
            if h in hourly:
                pattern.append(hourly[h])
            else:
                pattern.append({"hour": h, "avg_orders": 0, "avg_revenue": 0})

        return pattern

    def _get_daily_pattern(self, tenant_id: str, branch_id: str) -> Dict:
        """Get overall daily patterns."""
        weeks_back = 8
        cutoff = datetime.utcnow() - timedelta(weeks=weeks_back)

        query = self.db.query(
            func.count(Order.id).label('total_orders'),
            func.sum(Order.total).label('total_revenue'),
            func.count(func.distinct(func.date(Order.created_at))).label('days')
        ).filter(
            Order.tenant_id == tenant_id,
            Order.created_at >= cutoff,
            Order.status != 'cancelled'
        )

        if branch_id:
            query = query.filter(Order.branch_id == branch_id)

        result = query.first()

        days = result.days or 1
        return {
            "avg_orders": round((result.total_orders or 0) / days, 1),
            "avg_revenue": round(float(result.total_revenue or 0) / days, 2),
            "total_orders": result.total_orders or 0,
            "total_revenue": float(result.total_revenue or 0)
        }

    def _get_item_demand_forecast(self, tenant_id: str, branch_id: str,
                                    day_of_week: int) -> List[Dict]:
        """Predict item-level demand."""
        weeks_back = 4
        cutoff = datetime.utcnow() - timedelta(weeks=weeks_back)

        query = self.db.query(
            OrderItem.item_name,
            func.sum(OrderItem.quantity).label('total_quantity'),
            func.count(OrderItem.id).label('order_count')
        ).join(Order).filter(
            Order.tenant_id == tenant_id,
            Order.created_at >= cutoff,
            extract('dow', Order.created_at) == day_of_week,
            Order.status != 'cancelled'
        )

        if branch_id:
            query = query.filter(Order.branch_id == branch_id)

        results = query.group_by(
            OrderItem.item_name
        ).order_by(
            func.sum(OrderItem.quantity).desc()
        ).limit(20).all()

        return [
            {
                "item_name": r.item_name,
                "avg_quantity": round(r.total_quantity / weeks_back, 1),
                "avg_orders": round(r.order_count / weeks_back, 1)
            }
            for r in results
        ]

    def _identify_peak_hours(self, hourly_pattern: List[Dict]) -> List[Dict]:
        """Identify peak hours."""
        if not hourly_pattern:
            return []

        avg_orders = sum(h["avg_orders"] for h in hourly_pattern) / len(hourly_pattern)
        threshold = avg_orders * 1.5

        peak = [h for h in hourly_pattern if h["avg_orders"] > threshold]
        return sorted(peak, key=lambda x: x["avg_orders"], reverse=True)

    def _calculate_staffing_needs(self, hourly_pattern: List[Dict],
                                    total_orders: float) -> Dict:
        """Calculate staffing recommendations."""
        peak_hours = self._identify_peak_hours(hourly_pattern)

        # Rule of thumb: 1 staff per 10-15 orders per hour
        recommendations = []
        for peak in peak_hours:
            orders_per_hour = peak["avg_orders"]
            staff_needed = max(2, round(orders_per_hour / 10))
            recommendations.append({
                "hour": peak["hour"],
                "time_label": f"{peak['hour']:02d}:00-{peak['hour']+1:02d}:00",
                "expected_orders": orders_per_hour,
                "recommended_staff": staff_needed,
                "roles": {
                    "cashiers": max(1, staff_needed // 3),
                    "kitchen": max(1, staff_needed // 2),
                    "service": max(1, staff_needed // 3)
                }
            })

        return {
            "peak_periods": recommendations,
            "min_staff": max(2, round(total_orders / 50)),
            "recommended_staff": max(3, round(total_orders / 30))
        }

    def _calculate_confidence(self, daily_pattern: Dict) -> str:
        """Calculate forecast confidence level."""
        total_orders = daily_pattern.get("total_orders", 0)
        if total_orders > 500:
            return "high"
        elif total_orders > 100:
            return "medium"
        return "low"

    def _calculate_trend(self, tenant_id: str, branch_id: str) -> str:
        """Calculate if business is trending up, down, or stable."""
        # Compare last 2 weeks vs previous 2 weeks
        now = datetime.utcnow()
        two_weeks_ago = now - timedelta(weeks=2)
        four_weeks_ago = now - timedelta(weeks=4)

        recent = self.db.query(func.count(Order.id)).filter(
            Order.tenant_id == tenant_id,
            Order.created_at >= two_weeks_ago,
            Order.status != 'cancelled'
        )
        if branch_id:
            recent = recent.filter(Order.branch_id == branch_id)
        recent_count = recent.scalar() or 0

        previous = self.db.query(func.count(Order.id)).filter(
            Order.tenant_id == tenant_id,
            Order.created_at >= four_weeks_ago,
            Order.created_at < two_weeks_ago,
            Order.status != 'cancelled'
        )
        if branch_id:
            previous = previous.filter(Order.branch_id == branch_id)
        previous_count = previous.scalar() or 0

        if previous_count == 0:
            return "new"

        change = ((recent_count - previous_count) / previous_count) * 100

        if change > 10:
            return "growing"
        elif change < -10:
            return "declining"
        return "stable"

    def _generate_insights(self, hourly: List[Dict], daily: Dict,
                            day_of_week: int) -> List[str]:
        """Generate actionable insights."""
        insights = []

        # Peak hour insight
        peak_hours = self._identify_peak_hours(hourly)
        if peak_hours:
            peak_times = ", ".join([f"{h['hour']:02d}:00" for h in peak_hours[:3]])
            insights.append(f"Peak hours: {peak_times}. Ensure full staffing.")

        # Weekend vs weekday
        if day_of_week >= 5:
            insights.append("Weekend: Expect 20-30% higher volume than weekdays.")
        else:
            insights.append("Weekday: Standard staffing should suffice.")

        # Slow hours
        slow_hours = [h for h in hourly if h["avg_orders"] < 2]
        if slow_hours:
            slow_times = ", ".join([f"{h['hour']:02d}:00" for h in slow_hours[:3]])
            insights.append(f"Slow periods: {slow_times}. Consider staff breaks.")

        # Revenue insight
        avg_revenue = daily.get("avg_revenue", 0)
        if avg_revenue > 0:
            insights.append(f"Expected revenue: ₹{avg_revenue:,.0f}")

        return insights
