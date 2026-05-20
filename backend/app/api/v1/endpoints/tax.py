from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from app.api.dependencies import get_current_user
from app.modules.auth.rbac import require_permission
from app.infrastructure.database import get_db_session
from app.modules.tax.service import TaxService

router = APIRouter()


class TaxConfigCreate(BaseModel):
    name: str
    rate: float
    tax_type: str = "gst"
    applicable_to: Optional[list] = ["dine_in", "takeaway", "delivery"]
    branch_id: Optional[str] = None


class TaxConfigUpdate(BaseModel):
    name: Optional[str] = None
    rate: Optional[float] = None
    tax_type: Optional[str] = None
    applicable_to: Optional[list] = None
    is_active: Optional[bool] = None


class TaxConfigResponse(BaseModel):
    id: str
    tenant_id: str
    branch_id: Optional[str]
    name: str
    rate: float
    tax_type: str
    applicable_to: Optional[list]
    is_active: bool

    class Config:
        from_attributes = True


@router.post("/", response_model=TaxConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_tax_config(
    tax: TaxConfigCreate,
    current_user: dict = Depends(require_permission("tax:create")),
    db: Session = Depends(get_db_session)
):
    tax_service = TaxService(db)
    data = tax.model_dump()
    data["tenant_id"] = current_user["tenant_id"]
    return tax_service.create_tax_config(data)


@router.get("/", response_model=List[TaxConfigResponse])
async def list_tax_configs(
    branch_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    tax_service = TaxService(db)
    return tax_service.get_tax_configs(current_user["tenant_id"], branch_id)


@router.get("/calculate")
async def calculate_tax(
    subtotal: float,
    order_type: str = "dine_in",
    branch_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    tax_service = TaxService(db)
    return tax_service.calculate_tax(
        tenant_id=current_user["tenant_id"],
        subtotal=subtotal,
        order_type=order_type,
        branch_id=branch_id
    )


@router.get("/{tax_id}", response_model=TaxConfigResponse)
async def get_tax_config(
    tax_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    tax_service = TaxService(db)
    tax = tax_service.get_tax_config(tax_id)
    if not tax:
        raise HTTPException(status_code=404, detail="Tax config not found")
    return tax


@router.put("/{tax_id}", response_model=TaxConfigResponse)
async def update_tax_config(
    tax_id: str,
    tax: TaxConfigUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    tax_service = TaxService(db)
    updated = tax_service.update_tax_config(tax_id, tax.model_dump(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=404, detail="Tax config not found")
    return updated


@router.delete("/{tax_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tax_config(
    tax_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    tax_service = TaxService(db)
    if not tax_service.delete_tax_config(tax_id):
        raise HTTPException(status_code=404, detail="Tax config not found")
    return None
