"""Prometheus metrics endpoint."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from app.infrastructure.database import get_db_session
from app.models import Order, Payment, Customer, Tenant
from app.core.config import settings

router = APIRouter()


@router.get("/metrics")
async def prometheus_metrics(db: Session = Depends(get_db_session)):
    """Prometheus-compatible metrics endpoint."""
    now = datetime.utcnow()
    today = now.date()
    hour_ago = now - timedelta(hours=1)

    # Business metrics
    orders_today = db.query(func.count(Order.id)).filter(
        func.date(Order.created_at) == today,
        Order.status != "cancelled"
    ).scalar() or 0

    orders_last_hour = db.query(func.count(Order.id)).filter(
        Order.created_at >= hour_ago,
        Order.status != "cancelled"
    ).scalar() or 0

    revenue_today = db.query(func.sum(Order.total)).filter(
        func.date(Order.created_at) == today,
        Order.status != "cancelled"
    ).scalar() or 0

    active_orders = db.query(func.count(Order.id)).filter(
        Order.status.in_(["pending", "confirmed", "preparing"])
    ).scalar() or 0

    total_tenants = db.query(func.count(Tenant.id)).filter(
        Tenant.is_active == True
    ).scalar() or 0

    total_customers = db.query(func.count(Customer.id)).scalar() or 0

    # Format as Prometheus text
    lines = [
        f"# HELP kitchenos_orders_today Total orders today",
        f"# TYPE kitchenos_orders_today gauge",
        f"kitchenos_orders_today {orders_today}",
        f"",
        f"# HELP kitchenos_orders_last_hour Orders in the last hour",
        f"# TYPE kitchenos_orders_last_hour gauge",
        f"kitchenos_orders_last_hour {orders_last_hour}",
        f"",
        f"# HELP kitchenos_revenue_today Revenue today in INR",
        f"# TYPE kitchenos_revenue_today gauge",
        f"kitchenos_revenue_today {float(revenue_today)}",
        f"",
        f"# HELP kitchenos_active_orders Currently active orders",
        f"# TYPE kitchenos_active_orders gauge",
        f"kitchenos_active_orders {active_orders}",
        f"",
        f"# HELP kitchenos_tenants_total Total active tenants",
        f"# TYPE kitchenos_tenants_total gauge",
        f"kitchenos_tenants_total {total_tenants}",
        f"",
        f"# HELP kitchenos_customers_total Total customers",
        f"# TYPE kitchenos_customers_total gauge",
        f"kitchenos_customers_total {total_customers}",
        f"",
        f"# HELP kitchenos_app_info Application info",
        f"# TYPE kitchenos_app_info gauge",
        f'kitchenos_app_info{{version="{settings.APP_VERSION}"}} 1',
    ]

    from fastapi.responses import PlainTextResponse
    return PlainTextResponse("\n".join(lines), media_type="text/plain")
