"""Public API key management service."""

import uuid
import hashlib
import secrets
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import Column, String, Boolean, JSON, DateTime, Integer
from app.infrastructure.database import Base
from app.models import generate_uuid


class ApiKey(Base):
    __tablename__ = "api_keys"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    tenant_id = Column(String(36), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    key_hash = Column(String(64), nullable=False, unique=True, index=True)
    key_prefix = Column(String(10), nullable=False)  # First 8 chars for identification
    permissions = Column(JSON, default=[])  # ["menu:read", "orders:write", ...]
    rate_limit = Column(Integer, default=1000)  # Requests per hour
    is_active = Column(Boolean, default=True)
    last_used_at = Column(DateTime)
    usage_count = Column(Integer, default=0)
    expires_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)


class ApiKeyService:
    def __init__(self, db: Session):
        self.db = db

    def create_key(self, tenant_id: str, name: str, permissions: list = None,
                   rate_limit: int = 1000, expires_at: datetime = None) -> tuple:
        """Create a new API key. Returns (key_object, raw_key)."""
        raw_key = f"kos_{secrets.token_urlsafe(32)}"
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        key_prefix = raw_key[:8]

        api_key = ApiKey(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            name=name,
            key_hash=key_hash,
            key_prefix=key_prefix,
            permissions=permissions or ["*"],
            rate_limit=rate_limit,
            expires_at=expires_at
        )
        self.db.add(api_key)
        self.db.commit()
        self.db.refresh(api_key)

        return api_key, raw_key

    def validate_key(self, raw_key: str) -> Optional[ApiKey]:
        """Validate an API key and return the key object."""
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()

        api_key = self.db.query(ApiKey).filter(
            ApiKey.key_hash == key_hash,
            ApiKey.is_active == True
        ).first()

        if not api_key:
            return None

        # Check expiry
        if api_key.expires_at and api_key.expires_at < datetime.utcnow():
            return None

        # Update usage
        api_key.last_used_at = datetime.utcnow()
        api_key.usage_count = (api_key.usage_count or 0) + 1
        self.db.commit()

        return api_key

    def get_keys(self, tenant_id: str) -> List[ApiKey]:
        """Get all API keys for a tenant."""
        return self.db.query(ApiKey).filter(
            ApiKey.tenant_id == tenant_id
        ).order_by(ApiKey.created_at.desc()).all()

    def revoke_key(self, key_id: str, tenant_id: str) -> bool:
        """Revoke an API key."""
        api_key = self.db.query(ApiKey).filter(
            ApiKey.id == key_id,
            ApiKey.tenant_id == tenant_id
        ).first()
        if api_key:
            api_key.is_active = False
            self.db.commit()
            return True
        return False

    def has_permission(self, api_key: ApiKey, permission: str) -> bool:
        """Check if an API key has a specific permission."""
        if "*" in (api_key.permissions or []):
            return True
        return permission in (api_key.permissions or [])
