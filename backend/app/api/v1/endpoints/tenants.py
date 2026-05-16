from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.api.dependencies import get_current_user, require_role
from app.infrastructure.database import get_db_session
from app.modules.tenant.service import TenantService
from app.modules.tenant.schemas import TenantCreate, TenantUpdate, TenantResponse

router = APIRouter()

@router.post("/", response_model=TenantResponse, status_code=status.HTTP_201_CREATED)
async def create_tenant(
    tenant: TenantCreate,
    current_user: dict = Depends(require_role("admin")),
    db: Session = Depends(get_db_session)
):
    """
    Create a new tenant.
    Only super admin can create tenants.
    """
    tenant_service = TenantService(db)
    return tenant_service.create_tenant(tenant)

@router.get("/", response_model=List[TenantResponse])
async def read_tenants(
    skip: int = 0,
    limit: int = 100,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """
    Retrieve tenants.
    """
    tenant_service = TenantService(db)
    return tenant_service.get_tenants(skip=skip, limit=limit)

@router.get("/{tenant_id}", response_model=TenantResponse)
async def read_tenant(
    tenant_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """
    Retrieve a specific tenant by ID.
    """
    tenant_service = TenantService(db)
    tenant = tenant_service.get_tenant(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return tenant

@router.put("/{tenant_id}", response_model=TenantResponse)
async def update_tenant(
    tenant_id: str,
    tenant: TenantUpdate,
    current_user: dict = Depends(require_role("admin")),
    db: Session = Depends(get_db_session)
):
    """
    Update a specific tenant.
    """
    tenant_service = TenantService(db)
    updated_tenant = tenant_service.update_tenant(tenant_id, tenant)
    if not updated_tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return updated_tenant

@router.delete("/{tenant_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tenant(
    tenant_id: str,
    current_user: dict = Depends(require_role("admin")),
    db: Session = Depends(get_db_session)
):
    """
    Delete a specific tenant.
    """
    tenant_service = TenantService(db)
    success = tenant_service.delete_tenant(tenant_id)
    if not success:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return None