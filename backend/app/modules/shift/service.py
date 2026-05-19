"""Shift management with cash reconciliation."""

import uuid
from typing import Optional, List, Dict
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models import Shift, ShiftAssignment, Order, Payment, User


class ShiftService:
    """Shift lifecycle management with cash reconciliation."""

    def __init__(self, db: Session):
        self.db = db

    def start_shift(self, user_id: str, branch_id: str,
                    opening_cash: float = 0) -> Dict:
        """Start a new shift for a user."""
        # Check if user already has an active shift
        active = self.db.query(ShiftAssignment).filter(
            ShiftAssignment.user_id == user_id,
            ShiftAssignment.status == "checked_in"
        ).first()

        if active:
            return {"error": "User already has an active shift"}

        # Find or create shift for today
        today = datetime.utcnow().date()
        shift = self.db.query(Shift).filter(
            Shift.branch_id == branch_id,
            Shift.is_active == True
        ).first()

        if not shift:
            shift = Shift(
                id=str(uuid.uuid4()),
                branch_id=branch_id,
                name="General",
                start_time=datetime.utcnow().time(),
                end_time=(datetime.utcnow() + timedelta(hours=8)).time(),
                is_active=True
            )
            self.db.add(shift)

        # Create assignment
        assignment = ShiftAssignment(
            id=str(uuid.uuid4()),
            shift_id=shift.id,
            user_id=user_id,
            date=today,
            status="checked_in",
            check_in=datetime.utcnow()
        )
        self.db.add(assignment)
        self.db.commit()

        return {
            "shift_assignment_id": str(assignment.id),
            "shift_id": str(shift.id),
            "user_id": user_id,
            "opening_cash": opening_cash,
            "started_at": assignment.check_in.isoformat(),
            "status": "checked_in"
        }

    def end_shift(self, assignment_id: str, closing_cash: float,
                  user_id: str) -> Dict:
        """End shift with cash reconciliation."""
        assignment = self.db.query(ShiftAssignment).filter(
            ShiftAssignment.id == assignment_id
        ).first()

        if not assignment:
            return {"error": "Shift assignment not found"}

        if assignment.status != "checked_in":
            return {"error": "Shift is not active"}

        # Calculate shift stats
        check_in = assignment.check_in
        now = datetime.utcnow()

        # Get orders during shift
        orders = self.db.query(Order).filter(
            Order.created_by == user_id,
            Order.created_at >= check_in,
            Order.created_at <= now,
            Order.status != "cancelled"
        ).all()

        # Get payments during shift
        payments = self.db.query(Payment).filter(
            Payment.tenant_id == assignment.shift.branch_id if hasattr(assignment, 'shift') else None,
            Payment.created_at >= check_in,
            Payment.created_at <= now,
            Payment.status == "completed"
        ).all()

        # Calculate totals
        total_orders = len(orders)
        total_revenue = sum(float(o.total or 0) for o in orders)

        cash_payments = sum(float(p.amount) for p in payments if p.payment_method == "cash")
        card_payments = sum(float(p.amount) for p in payments if p.payment_method == "card")
        upi_payments = sum(float(p.amount) for p in payments if p.payment_method == "upi")

        # Cash reconciliation
        expected_cash = cash_payments  # Would add opening_cash
        cash_variance = closing_cash - expected_cash

        # Update assignment
        assignment.check_out = now
        assignment.status = "checked_out"
        assignment.work_hours = round((now - check_in).total_seconds() / 3600, 2)

        self.db.commit()

        return {
            "shift_assignment_id": str(assignment.id),
            "user_id": str(user_id),
            "check_in": check_in.isoformat(),
            "check_out": now.isoformat(),
            "duration_hours": assignment.work_hours,
            "summary": {
                "total_orders": total_orders,
                "total_revenue": round(total_revenue, 2),
                "cash_collected": round(cash_payments, 2),
                "card_collected": round(card_payments, 2),
                "upi_collected": round(upi_payments, 2)
            },
            "cash_reconciliation": {
                "expected_cash": round(expected_cash, 2),
                "actual_cash": closing_cash,
                "variance": round(cash_variance, 2),
                "status": "balanced" if abs(cash_variance) < 1 else "variance"
            }
        }

    def get_active_shift(self, user_id: str) -> Optional[Dict]:
        """Get current active shift for a user."""
        assignment = self.db.query(ShiftAssignment).filter(
            ShiftAssignment.user_id == user_id,
            ShiftAssignment.status == "checked_in"
        ).first()

        if not assignment:
            return None

        return {
            "shift_assignment_id": str(assignment.id),
            "shift_id": str(assignment.shift_id),
            "user_id": str(assignment.user_id),
            "check_in": assignment.check_in.isoformat() if assignment.check_in else None,
            "status": assignment.status
        }

    def get_shift_report(self, branch_id: str, date: str = None) -> List[Dict]:
        """Get shift report for a branch."""
        target_date = datetime.strptime(date, "%Y-%m-%d").date() if date else datetime.utcnow().date()

        assignments = self.db.query(ShiftAssignment).join(Shift).filter(
            Shift.branch_id == branch_id,
            ShiftAssignment.date == target_date
        ).all()

        results = []
        for a in assignments:
            user = self.db.query(User).filter(User.id == a.user_id).first()
            results.append({
                "shift_assignment_id": str(a.id),
                "user_name": f"{user.first_name} {user.last_name}" if user else "Unknown",
                "role": user.role if user else "unknown",
                "check_in": a.check_in.isoformat() if a.check_in else None,
                "check_out": a.check_out.isoformat() if a.check_out else None,
                "work_hours": a.work_hours,
                "status": a.status
            })

        return results
