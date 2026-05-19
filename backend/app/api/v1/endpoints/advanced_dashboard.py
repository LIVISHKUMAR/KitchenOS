"""Advanced analytics dashboard endpoints."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timedelta
from sqlalchemy import func, cast, Date

from app.api.dependencies import get_current_user
from app.infrastructure.database import get_db_session
from app.models import Order, OrderItem, Customer, MenuItem, MenuCategory, Payment

router = APIRouter()


@router.get("/customer-lifetime-value")
async def customer_lifetime_value(
    limit: int = Query(default=20, le=100),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Get customer lifetime value analysis."""
    tenant_id = current_user["tenant_id"]

    customers = db.query(Customer).filter(
        Customer.tenant_id == tenant_id,
        Customer.total_orders > 0
    ).order_by(Customer.total_spent.desc()).limit(limit).all()

    return [
        {
            "customer_id": str(c.id),
            "name": c.name,
            "phone": c.phone,
            "total_orders": c.total_orders or 0,
            "total_spent": round(float(c.total_spent or 0), 2),
            "avg_order_value": round(float(c.total_spent or 0) / max(c.total_orders or 1, 1), 2),
            "loyalty_points": c.loyalty_points or 0,
            "tier": c.membership_tier or "bronze"
        }
        for c in customers
    ]


@router.get("/retention-metrics")
async def retention_metrics(
    months_back: int = Query(default=6, le=12),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Get customer retention metrics."""
    tenant_id = current_user["tenant_id"]
    now = datetime.utcnow()

    cohorts = {}
    for i in range(months_back):
        month_start = now - timedelta(days=30 * (i + 1))
        month_end = now - timedelta(days=30 * i)

        new_customers = db.query(func.count(Customer.id)).filter(
            Customer.tenant_id == tenant_id,
            Customer.created_at >= month_start,
            Customer.created_at < month_end
        ).scalar() or 0

        returning = db.query(func.count(func.distinct(Order.customer_id))).filter(
            Order.tenant_id == tenant_id,
            Order.created_at >= month_start,
            Order.created_at < month_end,
            Order.customer_id.in_(
                db.query(Order.customer_id).filter(
                    Order.tenant_id == tenant_id,
                    Order.created_at < month_start,
                    Order.status != "cancelled"
                )
            ),
            Order.status != "cancelled"
        ).scalar() or 0

        cohort_label = month_start.strftime("%Y-%m")
        cohorts[cohort_label] = {
            "new_customers": new_customers,
            "returning_customers": returning,
            "retention_rate": round((returning / max(new_customers + returning, 1)) * 100, 1)
        }

    return cohorts


@router.get("/profitability-trends")
async def profitability_trends(
    days_back: int = Query(default=30, le=90),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Get profitability trends."""
    tenant_id = current_user["tenant_id"]
    cutoff = datetime.utcnow() - timedelta(days=days_back)

    daily = db.query(
        func.date(Order.created_at).label('date'),
        func.count(Order.id).label('orders'),
        func.sum(Order.subtotal).label('revenue'),
        func.sum(Order.tax_amount).label('tax'),
        func.sum(Order.total).label('total')
    ).filter(
        Order.tenant_id == tenant_id,
        Order.created_at >= cutoff,
        Order.status != "cancelled"
    ).group_by(
        func.date(Order.created_at)
    ).order_by(
        func.date(Order.created_at)
    ).all()

    return [
        {
            "date": str(d.date),
            "orders": d.orders,
            "revenue": round(float(d.revenue or 0), 2),
            "tax": round(float(d.tax or 0), 2),
            "total": round(float(d.total or 0), 2)
        }
        for d in daily
    ]


@router.get("/operational-efficiency")
async def operational_efficiency(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Get operational efficiency metrics."""
    tenant_id = current_user["tenant_id"]
    today = datetime.utcnow().date()

    # Average order preparation time
    completed_orders = db.query(Order).filter(
        Order.tenant_id == tenant_id,
        func.date(Order.created_at) == today,
        Order.status == "completed",
        Order.completed_at.isnot(None)
    ).all()

    prep_times = []
    for order in completed_orders:
        if order.created_at and order.completed_at:
            diff = (order.completed_at - order.created_at).total_seconds() / 60
            prep_times.append(diff)

    avg_prep_time = sum(prep_times) / len(prep_times) if prep_times else 0

    # Orders per hour
    orders_today = db.query(func.count(Order.id)).filter(
        Order.tenant_id == tenant_id,
        func.date(Order.created_at) == today,
        Order.status != "cancelled"
    ).scalar() or 0

    hours_open = max(1, datetime.utcnow().hour - 6)  # Assume 6 AM opening

    return {
        "date": str(today),
        "avg_prep_time_minutes": round(avg_prep_time, 1),
        "orders_today": orders_today,
        "orders_per_hour": round(orders_today / hours_open, 1),
        "peak_hour": "12:00-14:00",  # Would calculate from data
        "efficiency_score": min(100, round(100 - (avg_prep_time - 15) * 2))  # 15 min baseline
    }
