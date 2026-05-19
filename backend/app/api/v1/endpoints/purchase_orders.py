from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import uuid
from app.api.dependencies import get_current_user
from app.infrastructure.database import get_db_session
from app.models import PurchaseOrder

router = APIRouter()


class PurchaseOrderCreate(BaseModel):
    vendor_id: str
    branch_id: str
    expected_delivery: Optional[str] = None
    notes: Optional[str] = None
    items: List[dict]  # [{inventory_item_id, quantity, unit_price}]


class PurchaseOrderUpdate(BaseModel):
    status: Optional[str] = None
    expected_delivery: Optional[str] = None
    notes: Optional[str] = None
    approved_by: Optional[str] = None


class PurchaseOrderResponse(BaseModel):
    id: str
    tenant_id: str
    branch_id: str
    vendor_id: str
    order_number: str
    status: str
    subtotal: float
    tax_amount: float
    total: float
    notes: Optional[str]
    expected_delivery: Optional[str]

    class Config:
        from_attributes = True


@router.post("/", response_model=PurchaseOrderResponse, status_code=status.HTTP_201_CREATED)
async def create_purchase_order(
    po: PurchaseOrderCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    subtotal = sum(item.get("quantity", 0) * item.get("unit_price", 0) for item in po.items)
    tax_amount = subtotal * 0.18
    total = subtotal + tax_amount

    today = datetime.utcnow().strftime("%Y%m%d")
    count = db.query(PurchaseOrder).filter(
        PurchaseOrder.tenant_id == current_user["tenant_id"]
    ).count()

    db_po = PurchaseOrder(
        id=str(uuid.uuid4()),
        tenant_id=current_user["tenant_id"],
        branch_id=po.branch_id,
        vendor_id=po.vendor_id,
        order_number=f"PO-{today}-{count + 1:04d}",
        status="draft",
        subtotal=subtotal,
        tax_amount=tax_amount,
        total=total,
        notes=po.notes,
        expected_delivery=datetime.strptime(po.expected_delivery, "%Y-%m-%d") if po.expected_delivery else None,
        created_by=current_user["user_id"]
    )
    db.add(db_po)
    db.commit()
    db.refresh(db_po)
    return db_po


@router.get("/", response_model=List[PurchaseOrderResponse])
async def list_purchase_orders(
    branch_id: Optional[str] = None,
    status_filter: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    query = db.query(PurchaseOrder).filter(
        PurchaseOrder.tenant_id == current_user["tenant_id"]
    )
    if branch_id:
        query = query.filter(PurchaseOrder.branch_id == branch_id)
    if status_filter:
        query = query.filter(PurchaseOrder.status == status_filter)
    return query.order_by(PurchaseOrder.created_at.desc()).offset(skip).limit(limit).all()


@router.get("/{po_id}", response_model=PurchaseOrderResponse)
async def get_purchase_order(
    po_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    if str(po.tenant_id) != current_user["tenant_id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    return po


@router.put("/{po_id}", response_model=PurchaseOrderResponse)
async def update_purchase_order(
    po_id: str,
    po_update: PurchaseOrderUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    if str(po.tenant_id) != current_user["tenant_id"]:
        raise HTTPException(status_code=403, detail="Access denied")

    update_data = po_update.model_dump(exclude_unset=True)
    if "expected_delivery" in update_data and update_data["expected_delivery"]:
        update_data["expected_delivery"] = datetime.strptime(update_data["expected_delivery"], "%Y-%m-%d")

    for key, value in update_data.items():
        setattr(po, key, value)
    db.commit()
    db.refresh(po)
    return po


@router.post("/{po_id}/approve")
async def approve_purchase_order(
    po_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    if po.status != "draft":
        raise HTTPException(status_code=400, detail=f"Cannot approve PO in '{po.status}' status")

    po.status = "approved"
    po.approved_by = current_user["user_id"]
    db.commit()
    return {"id": str(po.id), "status": "approved", "message": "Purchase order approved"}


@router.post("/{po_id}/receive")
async def receive_purchase_order(
    po_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    if po.status != "approved":
        raise HTTPException(status_code=400, detail=f"Cannot receive PO in '{po.status}' status")

    po.status = "received"
    db.commit()
    return {"id": str(po.id), "status": "received", "message": "Goods received. Update inventory stock."}
