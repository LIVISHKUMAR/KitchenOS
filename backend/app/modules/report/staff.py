"""Staff performance analytics."""

from typing import Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models import Order, User, ShiftAssignment


class StaffPerformanceService:
    def __init__(self, db: Session):
        self.db = db

    def get_performance(self, tenant_id: str, branch_id: Optional[str] = None,
                        date_from: Optional[str] = None, date_to: Optional[str] = None) -> list:
        """Get staff performance metrics."""
        query = self.db.query(User).filter(
            User.tenant_id == tenant_id,
            User.is_active == True,
            User.role.in_(["cashier", "waiter"])
        )
        if branch_id:
            query = query.filter(User.branch_id == branch_id)

        users = query.all()

        results = []
        for user in users:
            order_query = self.db.query(
                func.count(Order.id).label("order_count"),
                func.sum(Order.total).label("total_revenue")
            ).filter(
                Order.created_by == user.id,
                Order.status != "cancelled"
            )

            if date_from:
                order_query = order_query.filter(Order.created_at >= date_from)
            if date_to:
                order_query = order_query.filter(Order.created_at <= date_to)

            stats = order_query.first()

            # Get attendance
            attendance = self.db.query(
                func.count(ShiftAssignment.id).label("shifts"),
                func.sum(ShiftAssignment.work_hours).label("hours")
            ).filter(
                ShiftAssignment.user_id == user.id,
                ShiftAssignment.status.in_(["checked_in", "checked_out"])
            ).first()

            results.append({
                "user_id": str(user.id),
                "name": f"{user.first_name or ''} {user.last_name or ''}".strip() or user.email,
                "role": user.role,
                "orders": stats.order_count or 0,
                "revenue": round(float(stats.total_revenue or 0), 2),
                "avg_order_value": round(float(stats.total_revenue or 0) / (stats.order_count or 1), 2),
                "shifts_worked": attendance.shifts or 0,
                "hours_worked": float(attendance.hours or 0)
            })

        return sorted(results, key=lambda x: x["revenue"], reverse=True)

    def get_leaderboard(self, tenant_id: str, metric: str = "revenue",
                        limit: int = 10) -> list:
        """Get staff leaderboard."""
        performance = self.get_performance(tenant_id)
        return performance[:limit]
