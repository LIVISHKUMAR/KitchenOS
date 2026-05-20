from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.api.dependencies import get_current_user
from app.infrastructure.database import get_db_session
from app.modules.report.service import ReportService
from app.models import Order, OrderItem, Payment, Tenant, Branch
from datetime import datetime
from collections import defaultdict

router = APIRouter()


@router.get("/daily-sales")
async def daily_sales_report(
    branch_id: Optional[str] = None,
    date: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    report_service = ReportService(db)
    return report_service.daily_sales(
        tenant_id=current_user["tenant_id"],
        branch_id=branch_id,
        date=date
    )


@router.get("/item-wise-sales")
async def item_wise_sales_report(
    branch_id: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    report_service = ReportService(db)
    return report_service.item_wise_sales(
        tenant_id=current_user["tenant_id"],
        branch_id=branch_id,
        date_from=date_from,
        date_to=date_to
    )


@router.get("/category-wise-sales")
async def category_wise_sales_report(
    branch_id: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    report_service = ReportService(db)
    return report_service.category_wise_sales(
        tenant_id=current_user["tenant_id"],
        branch_id=branch_id,
        date_from=date_from,
        date_to=date_to
    )


@router.get("/hourly-sales")
async def hourly_sales_report(
    branch_id: Optional[str] = None,
    date: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    report_service = ReportService(db)
    return report_service.hourly_sales(
        tenant_id=current_user["tenant_id"],
        branch_id=branch_id,
        date=date
    )


@router.get("/gst-summary")
async def gst_summary_report(
    month: str = Query(..., description="YYYY-MM format"),
    branch_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Generate GST summary for a given month."""
    year, mon = map(int, month.split("-"))
    start = datetime(year, mon, 1)
    if mon == 12:
        end = datetime(year + 1, 1, 1)
    else:
        end = datetime(year, mon + 1, 1)

    query = db.query(Order).filter(
        Order.tenant_id == current_user["tenant_id"],
        Order.created_at >= start,
        Order.created_at < end,
        Order.status.in_(["completed", "ready"])
    )
    if branch_id:
        query = query.filter(Order.branch_id == branch_id)
    orders = query.all()

    total_orders = len(orders)
    total_revenue = sum(float(o.total or 0) for o in orders)
    total_tax = sum(float(o.tax_amount or 0) for o in orders)
    total_cgst = round(total_tax / 2, 2)
    total_sgst = round(total_tax / 2, 2)

    # HSN-wise summary
    hsn_summary = defaultdict(lambda: {"quantity": 0, "taxable_value": 0, "cgst": 0, "sgst": 0, "total": 0})
    for order in orders:
        items = db.query(OrderItem).filter(OrderItem.order_id == order.id).all()
        for item in items:
            hsn = "996331"  # Restaurant services HSN
            taxable = float(item.unit_price or 0) * float(item.quantity or 0)
            tax = float(item.tax_amount or 0)
            hsn_summary[hsn]["quantity"] += float(item.quantity or 0)
            hsn_summary[hsn]["taxable_value"] += taxable
            hsn_summary[hsn]["cgst"] += tax / 2
            hsn_summary[hsn]["sgst"] += tax / 2
            hsn_summary[hsn]["total"] += taxable + tax

    return {
        "month": month,
        "summary": {
            "total_orders": total_orders,
            "total_revenue": round(total_revenue, 2),
            "total_tax": round(total_tax, 2),
            "total_cgst": total_cgst,
            "total_sgst": total_sgst,
        },
        "hsn_summary": [
            {"hsn_code": hsn, **{k: round(v, 2) for k, v in data.items()}}
            for hsn, data in hsn_summary.items()
        ],
    }


@router.get("/gstr1")
async def gstr1_export(
    month: str = Query(..., description="YYYY-MM format"),
    branch_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Export GSTR-1 JSON for GST filing."""
    year, mon = map(int, month.split("-"))
    start = datetime(year, mon, 1)
    if mon == 12:
        end = datetime(year + 1, 1, 1)
    else:
        end = datetime(year, mon + 1, 1)

    tenant = db.query(Tenant).filter(Tenant.id == current_user["tenant_id"]).first()
    branch = None
    if branch_id:
        branch = db.query(Branch).filter(Branch.id == branch_id).first()

    query = db.query(Order).filter(
        Order.tenant_id == current_user["tenant_id"],
        Order.created_at >= start,
        Order.created_at < end,
        Order.status.in_(["completed", "ready"])
    )
    if branch_id:
        query = query.filter(Order.branch_id == branch_id)
    orders = query.all()

    # B2C (Business to Consumer) invoices
    b2c_invoices = []
    for order in orders:
        items = db.query(OrderItem).filter(OrderItem.order_id == order.id).all()
        for item in items:
            taxable = float(item.unit_price or 0) * float(item.quantity or 0)
            tax = float(item.tax_amount or 0)
            b2c_invoices.append({
                "inum": order.order_number,
                "dt": order.created_at.strftime("%d-%m-%Y") if order.created_at else "",
                "val": round(float(order.total or 0), 2),
                "pos": branch.state if branch else "IN",
                "typ": "OE",  # Other than e-commerce
                "hsn_sc": "996331",
                "txval": round(taxable, 2),
                "iamt": 0,
                "samt": round(tax / 2, 2),
                "camt": round(tax / 2, 2),
                "csamt": 0,
            })

    # GSTR-1 JSON structure
    gstr1 = {
        "gstin": tenant.settings.get("gstin", "") if tenant and tenant.settings else "",
        "fp": f"{mon:02d}{year}",
        "gt": 0,
        "cur_gt": 0,
        "version": "GST3.0.4",
        "hash": "hash",
        "b2c": b2c_invoices,
    }

    return gstr1
