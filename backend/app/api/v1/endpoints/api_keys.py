"""API key management endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from app.api.dependencies import get_current_user
from app.infrastructure.database import get_db_session
from app.modules.api_key.service import ApiKeyService

router = APIRouter()


class ApiKeyCreate(BaseModel):
    name: str
    permissions: Optional[list] = ["*"]
    rate_limit: Optional[int] = 1000
    expires_at: Optional[datetime] = None


class ApiKeyResponse(BaseModel):
    id: str
    name: str
    key_prefix: str
    permissions: list
    rate_limit: int
    is_active: bool
    last_used_at: Optional[datetime]
    usage_count: int
    expires_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_api_key(
    data: ApiKeyCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Create a new API key. The full key is only shown once."""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    api_key_service = ApiKeyService(db)
    key_obj, raw_key = api_key_service.create_key(
        tenant_id=current_user["tenant_id"],
        name=data.name,
        permissions=data.permissions,
        rate_limit=data.rate_limit,
        expires_at=data.expires_at
    )

    return {
        "id": str(key_obj.id),
        "name": key_obj.name,
        "key": raw_key,  # Only shown once!
        "key_prefix": key_obj.key_prefix,
        "permissions": key_obj.permissions,
        "rate_limit": key_obj.rate_limit,
        "expires_at": key_obj.expires_at.isoformat() if key_obj.expires_at else None,
        "message": "Save this key securely. It will not be shown again."
    }


@router.get("/", response_model=List[ApiKeyResponse])
async def list_api_keys(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """List all API keys (without revealing the full key)."""
    api_key_service = ApiKeyService(db)
    return api_key_service.get_keys(current_user["tenant_id"])


@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_api_key(
    key_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Revoke an API key."""
    api_key_service = ApiKeyService(db)
    if not api_key_service.revoke_key(key_id, current_user["tenant_id"]):
        raise HTTPException(status_code=404, detail="API key not found")
    return None
