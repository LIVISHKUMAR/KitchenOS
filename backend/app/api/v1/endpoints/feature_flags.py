"""Feature flags endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel
from app.api.dependencies import get_current_user
from app.infrastructure.database import get_db_session
from app.modules.feature_flags.service import FeatureFlagService

router = APIRouter()


class FlagCreate(BaseModel):
    name: str
    description: str = ""
    is_enabled: bool = False


class FlagUpdate(BaseModel):
    description: Optional[str] = None
    is_enabled: Optional[bool] = None
    rollout_percentage: Optional[int] = None


class TenantOverride(BaseModel):
    tenant_id: str
    enabled: bool


@router.post("/", status_code=201)
async def create_flag(
    data: FlagCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    service = FeatureFlagService(db)
    return service.create_flag(data.name, data.description, data.is_enabled)


@router.get("/")
async def list_flags(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    service = FeatureFlagService(db)
    return service.get_flags()


@router.get("/check/{flag_name}")
async def check_flag(
    flag_name: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    service = FeatureFlagService(db)
    enabled = service.is_enabled(flag_name, current_user.get("tenant_id"))
    return {"flag": flag_name, "enabled": enabled}


@router.put("/{flag_id}")
async def update_flag(
    flag_id: str,
    data: FlagUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    service = FeatureFlagService(db)
    flag = service.update_flag(flag_id, data.model_dump(exclude_unset=True))
    if not flag:
        raise HTTPException(status_code=404, detail="Flag not found")
    return flag


@router.post("/{flag_name}/tenant-override")
async def set_tenant_override(
    flag_name: str,
    data: TenantOverride,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    service = FeatureFlagService(db)
    service.set_tenant_override(flag_name, data.tenant_id, data.enabled)
    return {"message": "Override set"}
