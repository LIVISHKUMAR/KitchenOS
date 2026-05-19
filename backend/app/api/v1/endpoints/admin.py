"""Admin dashboard API endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from app.api.dependencies import get_current_user
from app.infrastructure.database import get_db_session
from app.models import Tenant, Branch, User, Order, Payment, Customer
from app.core.config import settings

router = APIRouter()


@router.get("/dashboard")
async def admin_dashboard(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Platform admin dashboard overview."""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    tenant_id = current_user["tenant_id"]
    now = datetime.utcnow()
    today = now.date()
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)

    # Tenant info
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()

    # Branch count
    branch_count = db.query(Branch).filter(
        Branch.tenant_id == tenant_id, Branch.is_active == True
    ).count()

    # User count
    user_count = db.query(User).filter(
        User.tenant_id == tenant_id, User.is_active == True
    ).count()

    # Today's orders
    today_orders = db.query(func.count(Order.id)).filter(
        Order.tenant_id == tenant_id,
        func.date(Order.created_at) == today,
        Order.status != "cancelled"
    ).scalar() or 0

    # Today's revenue
    today_revenue = db.query(func.sum(Order.total)).filter(
        Order.tenant_id == tenant_id,
        func.date(Order.created_at) == today,
        Order.status != "cancelled"
    ).scalar() or 0

    # This week's orders
    week_orders = db.query(func.count(Order.id)).filter(
        Order.tenant_id == tenant_id,
        Order.created_at >= week_ago,
        Order.status != "cancelled"
    ).scalar() or 0

    # This week's revenue
    week_revenue = db.query(func.sum(Order.total)).filter(
        Order.tenant_id == tenant_id,
        Order.created_at >= week_ago,
        Order.status != "cancelled"
    ).scalar() or 0

    # This month's orders
    month_orders = db.query(func.count(Order.id)).filter(
        Order.tenant_id == tenant_id,
        Order.created_at >= month_ago,
        Order.status != "cancelled"
    ).scalar() or 0

    # This month's revenue
    month_revenue = db.query(func.sum(Order.total)).filter(
        Order.tenant_id == tenant_id,
        Order.created_at >= month_ago,
        Order.status != "cancelled"
    ).scalar() or 0

    # Customer count
    customer_count = db.query(Customer).filter(
        Customer.tenant_id == tenant_id
    ).count()

    # Active orders
    active_orders = db.query(func.count(Order.id)).filter(
        Order.tenant_id == tenant_id,
        Order.status.in_(["pending", "confirmed", "preparing"])
    ).scalar() or 0

    return {
        "tenant": {
            "id": str(tenant.id) if tenant else None,
            "name": tenant.name if tenant else None,
            "subscription_plan": tenant.subscription_plan if tenant else None,
            "subscription_status": tenant.subscription_status if tenant else None,
        },
        "branches": branch_count,
        "users": user_count,
        "customers": customer_count,
        "active_orders": active_orders,
        "today": {
            "orders": today_orders,
            "revenue": float(today_revenue)
        },
        "this_week": {
            "orders": week_orders,
            "revenue": float(week_revenue)
        },
        "this_month": {
            "orders": month_orders,
            "revenue": float(month_revenue)
        }
    }


@router.get("/system-health")
async def system_health(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """System health metrics for admin."""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    # Total tenants
    total_tenants = db.query(func.count(Tenant.id)).scalar() or 0

    # Active tenants (with orders in last 30 days)
    month_ago = datetime.utcnow() - timedelta(days=30)
    active_tenants = db.query(func.count(func.distinct(Order.tenant_id))).filter(
        Order.created_at >= month_ago
    ).scalar() or 0

    # Total orders today
    today = datetime.utcnow().date()
    total_orders_today = db.query(func.count(Order.id)).filter(
        func.date(Order.created_at) == today
    ).scalar() or 0

    return {
        "total_tenants": total_tenants,
        "active_tenants": active_tenants,
        "total_orders_today": total_orders_today,
        "version": settings.APP_VERSION,
        "debug_mode": settings.DEBUG
    }
