"""Custom report builder endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import uuid
import csv
import io
from fastapi.responses import StreamingResponse

from app.api.dependencies import get_current_user
from app.infrastructure.database import get_db_session

router = APIRouter()


class ReportTemplate(BaseModel):
    name: str
    entity: str  # orders, payments, customers, inventory
    columns: List[str]
    filters: dict = {}
    sort_by: str = "created_at"
    sort_order: str = "desc"


class SavedReport(BaseModel):
    id: str
    name: str
    entity: str
    columns: List[str]
    filters: dict
    created_at: str


# Available columns per entity
ENTITY_COLUMNS = {
    "orders": [
        "order_number", "order_type", "status", "customer_name",
        "subtotal", "tax_amount", "discount_amount", "total",
        "payment_status", "source", "created_at"
    ],
    "payments": [
        "amount", "payment_method", "status", "transaction_id",
        "processed_at", "created_at"
    ],
    "customers": [
        "name", "email", "phone", "loyalty_points",
        "total_orders", "total_spent", "customer_type", "created_at"
    ],
    "inventory": [
        "name", "item_code", "unit", "current_stock",
        "minimum_stock", "cost_price", "selling_price"
    ],
    "order_items": [
        "item_name", "quantity", "unit_price", "tax_amount",
        "total", "prep_status"
    ]
}


@router.get("/templates")
async def list_report_templates(
    current_user: dict = Depends(get_current_user)
):
    """List available report templates and columns."""
    return {
        "entities": list(ENTITY_COLUMNS.keys()),
        "columns": ENTITY_COLUMNS
    }


@router.post("/generate")
async def generate_report(
    template: ReportTemplate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Generate a custom report."""
    if template.entity not in ENTITY_COLUMNS:
        raise HTTPException(status_code=400, detail=f"Invalid entity: {template.entity}")

    available = ENTITY_COLUMNS[template.entity]
    invalid = [c for c in template.columns if c not in available]
    if invalid:
        raise HTTPException(status_code=400, detail=f"Invalid columns: {invalid}")

    # Build query
    columns = ", ".join(template.columns)
    table = template.entity

    where_clauses = [f"tenant_id = :tenant_id"]
    params = {"tenant_id": current_user["tenant_id"]}

    for key, value in template.filters.items():
        if key in available:
            where_clauses.append(f"{key} = :{key}")
            params[key] = value

    where = " AND ".join(where_clauses)
    order = f"{template.sort_by} {template.sort_order}"

    query = f"SELECT {columns} FROM {table} WHERE {where} ORDER BY {order} LIMIT 1000"

    try:
        result = db.execute(text(query), params)
        rows = result.fetchall()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Query error: {str(e)}")

    return {
        "columns": template.columns,
        "rows": [dict(zip(template.columns, row)) for row in rows],
        "total": len(rows)
    }


@router.post("/export")
async def export_report(
    template: ReportTemplate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Export report as CSV."""
    if template.entity not in ENTITY_COLUMNS:
        raise HTTPException(status_code=400, detail=f"Invalid entity: {template.entity}")

    columns = ", ".join(template.columns)
    table = template.entity

    where_clauses = [f"tenant_id = :tenant_id"]
    params = {"tenant_id": current_user["tenant_id"]}

    for key, value in template.filters.items():
        where_clauses.append(f"{key} = :{key}")
        params[key] = value

    where = " AND ".join(where_clauses)
    order = f"{template.sort_by} {template.sort_order}"

    query = f"SELECT {columns} FROM {table} WHERE {where} ORDER BY {order} LIMIT 10000"

    try:
        result = db.execute(text(query), params)
        rows = result.fetchall()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Query error: {str(e)}")

    # Generate CSV
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(template.columns)
    for row in rows:
        writer.writerow(row)

    csv_data = output.getvalue()

    return StreamingResponse(
        io.StringIO(csv_data),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={template.entity}_report.csv"}
    )
