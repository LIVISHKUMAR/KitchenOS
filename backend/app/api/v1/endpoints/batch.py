"""Batch/bulk operations endpoints."""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
import csv
import io
import uuid
from app.api.dependencies import get_current_user
from app.infrastructure.database import get_db_session
from app.models import MenuItem, Customer, InventoryItem

router = APIRouter()


class BulkMenuImport(BaseModel):
    items: List[dict]  # [{name, category_id, base_price, is_veg, ...}]


class BulkInventoryUpdate(BaseModel):
    updates: List[dict]  # [{id, current_stock}]


class BulkCustomerImport(BaseModel):
    customers: List[dict]  # [{name, email, phone, ...}]


@router.post("/menu/import")
async def bulk_import_menu(
    data: BulkMenuImport,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Bulk import menu items."""
    tenant_id = current_user["tenant_id"]
    branch_id = current_user.get("branch_id")
    imported = 0
    errors = []

    for item_data in data.items:
        try:
            item = MenuItem(
                id=str(uuid.uuid4()),
                tenant_id=tenant_id,
                branch_id=branch_id,
                name=item_data.get("name"),
                category_id=item_data.get("category_id"),
                base_price=item_data.get("base_price", 0),
                is_veg=item_data.get("is_veg", True),
                description=item_data.get("description"),
                item_code=item_data.get("item_code"),
                tax_rate=item_data.get("tax_rate", 18),
                is_available=item_data.get("is_available", True)
            )
            db.add(item)
            imported += 1
        except Exception as e:
            errors.append({"item": item_data.get("name"), "error": str(e)})

    db.commit()
    return {"imported": imported, "errors": errors, "total": len(data.items)}


@router.post("/menu/import-csv")
async def bulk_import_menu_csv(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Import menu items from CSV file."""
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="File must be CSV")

    content = await file.read()
    reader = csv.DictReader(io.StringIO(content.decode("utf-8")))

    tenant_id = current_user["tenant_id"]
    branch_id = current_user.get("branch_id")
    imported = 0
    errors = []

    for row in reader:
        try:
            item = MenuItem(
                id=str(uuid.uuid4()),
                tenant_id=tenant_id,
                branch_id=branch_id,
                name=row.get("name"),
                category_id=row.get("category_id"),
                base_price=float(row.get("base_price", 0)),
                is_veg=row.get("is_veg", "true").lower() == "true",
                description=row.get("description"),
                item_code=row.get("item_code"),
                tax_rate=float(row.get("tax_rate", 18)),
                is_available=True
            )
            db.add(item)
            imported += 1
        except Exception as e:
            errors.append({"row": row, "error": str(e)})

    db.commit()
    return {"imported": imported, "errors": errors}


@router.put("/inventory/update")
async def bulk_update_inventory(
    data: BulkInventoryUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Bulk update inventory stock levels."""
    tenant_id = current_user["tenant_id"]
    updated = 0
    errors = []

    for update in data.updates:
        item = db.query(InventoryItem).filter(
            InventoryItem.id == update.get("id"),
            InventoryItem.tenant_id == tenant_id
        ).first()

        if item:
            item.current_stock = update.get("current_stock", item.current_stock)
            updated += 1
        else:
            errors.append({"id": update.get("id"), "error": "Not found"})

    db.commit()
    return {"updated": updated, "errors": errors}


@router.post("/customers/import")
async def bulk_import_customers(
    data: BulkCustomerImport,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Bulk import customers."""
    tenant_id = current_user["tenant_id"]
    imported = 0
    errors = []

    for cust_data in data.customers:
        try:
            customer = Customer(
                id=str(uuid.uuid4()),
                tenant_id=tenant_id,
                name=cust_data.get("name"),
                email=cust_data.get("email"),
                phone=cust_data.get("phone"),
                customer_type=cust_data.get("customer_type", "regular")
            )
            db.add(customer)
            imported += 1
        except Exception as e:
            errors.append({"customer": cust_data.get("name"), "error": str(e)})

    db.commit()
    return {"imported": imported, "errors": errors}


@router.put("/orders/status")
async def bulk_update_order_status(
    order_ids: List[str],
    new_status: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Bulk update order statuses."""
    from app.models import Order
    tenant_id = current_user["tenant_id"]
    updated = 0

    for order_id in order_ids:
        order = db.query(Order).filter(
            Order.id == order_id,
            Order.tenant_id == tenant_id
        ).first()
        if order:
            order.status = new_status
            updated += 1

    db.commit()
    return {"updated": updated, "total": len(order_ids)}
