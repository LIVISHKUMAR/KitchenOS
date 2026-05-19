"""Open API ecosystem endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel
from datetime import datetime
import uuid

from app.api.dependencies import get_current_user
from app.infrastructure.database import get_db_session
from app.modules.api_key.service import ApiKey

router = APIRouter()


class ApiKeyCreate(BaseModel):
    name: str
    permissions: list = ["*"]
    rate_limit: int = 1000
    expires_at: Optional[datetime] = None


@router.post("/keys", status_code=201)
async def create_api_key(
    data: ApiKeyCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Create a new API key for third-party integrations."""
    import hashlib
    import secrets

    raw_key = f"kitchenos_{secrets.token_urlsafe(32)}"
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()

    api_key = ApiKey(
        id=str(uuid.uuid4()),
        tenant_id=current_user["tenant_id"],
        name=data.name,
        key_hash=key_hash,
        key_prefix=raw_key[:15],
        permissions=data.permissions,
        rate_limit=data.rate_limit,
        expires_at=data.expires_at,
        is_active=True
    )
    db.add(api_key)
    db.commit()

    return {
        "id": str(api_key.id),
        "key": raw_key,  # Only shown once
        "key_prefix": api_key.key_prefix,
        "name": data.name,
        "permissions": data.permissions,
        "rate_limit": data.rate_limit,
        "message": "Save this key securely. It will not be shown again."
    }


@router.get("/keys")
async def list_api_keys(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """List API keys (without revealing the full key)."""
    keys = db.query(ApiKey).filter(
        ApiKey.tenant_id == current_user["tenant_id"]
    ).all()

    return [
        {
            "id": str(k.id),
            "name": k.name,
            "key_prefix": k.key_prefix,
            "permissions": k.permissions,
            "rate_limit": k.rate_limit,
            "is_active": k.is_active,
            "last_used_at": k.last_used_at.isoformat() if k.last_used_at else None,
            "usage_count": k.usage_count,
            "created_at": k.created_at.isoformat() if k.created_at else None
        }
        for k in keys
    ]


@router.delete("/keys/{key_id}")
async def revoke_api_key(
    key_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Revoke an API key."""
    key = db.query(ApiKey).filter(
        ApiKey.id == key_id,
        ApiKey.tenant_id == current_user["tenant_id"]
    ).first()

    if not key:
        raise HTTPException(status_code=404, detail="API key not found")

    key.is_active = False
    db.commit()

    return {"message": "API key revoked"}


@router.get("/documentation")
async def api_documentation():
    """Get API documentation for developers."""
    return {
        "version": "v1",
        "base_url": "/api/v1",
        "authentication": "Bearer JWT token or API key",
        "rate_limits": {
            "default": "100 requests/minute",
            "authenticated": "1000 requests/minute"
        },
        "endpoints": {
            "menu": {
                "GET /menu/categories": "List categories",
                "GET /menu/items": "List items",
                "POST /orders/": "Create order"
            },
            "orders": {
                "GET /orders/": "List orders",
                "GET /orders/{id}": "Get order",
                "PUT /orders/{id}/status": "Update status"
            },
            "webhooks": {
                "POST /webhooks/": "Register webhook",
                "GET /webhooks/": "List webhooks"
            }
        },
        "webhook_events": [
            "order.created",
            "order.updated",
            "order.completed",
            "payment.completed",
            "inventory.low_stock"
        ],
        "sdks": {
            "python": "pip install kitchenos-sdk",
            "javascript": "npm install @kitchenos/sdk"
        }
    }
