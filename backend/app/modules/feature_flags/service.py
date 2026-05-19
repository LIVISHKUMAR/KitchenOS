"""Feature flags system."""

import uuid
from typing import Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import Column, String, Boolean, JSON, DateTime, Integer
from app.infrastructure.database import Base
from app.models import generate_uuid


class FeatureFlag(Base):
    __tablename__ = "feature_flags"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(String(255))
    is_enabled = Column(Boolean, default=False)
    # Tenant-specific overrides
    tenant_overrides = Column(JSON, default={})  # {tenant_id: true/false}
    # Percentage rollout
    rollout_percentage = Column(Integer, default=100)
    # Targeting rules
    targeting_rules = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)


class FeatureFlagService:
    def __init__(self, db: Session):
        self.db = db

    def create_flag(self, name: str, description: str = "",
                    is_enabled: bool = False) -> FeatureFlag:
        flag = FeatureFlag(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            is_enabled=is_enabled
        )
        self.db.add(flag)
        self.db.commit()
        self.db.refresh(flag)
        return flag

    def get_flags(self) -> List[FeatureFlag]:
        return self.db.query(FeatureFlag).all()

    def is_enabled(self, flag_name: str, tenant_id: str = None,
                   user_id: str = None) -> bool:
        """Check if a feature flag is enabled."""
        flag = self.db.query(FeatureFlag).filter(
            FeatureFlag.name == flag_name
        ).first()

        if not flag:
            return False

        # Check tenant override
        if tenant_id and flag.tenant_overrides:
            if tenant_id in flag.tenant_overrides:
                return flag.tenant_overrides[tenant_id]

        # Check global flag
        if not flag.is_enabled:
            return False

        # Check rollout percentage
        if flag.rollout_percentage < 100:
            # Use hash of tenant_id for consistent rollout
            if tenant_id:
                hash_val = hash(tenant_id) % 100
                return hash_val < flag.rollout_percentage

        return True

    def update_flag(self, flag_id: str, data: dict) -> Optional[FeatureFlag]:
        flag = self.db.query(FeatureFlag).filter(FeatureFlag.id == flag_id).first()
        if flag:
            for key, value in data.items():
                if hasattr(flag, key):
                    setattr(flag, key, value)
            self.db.commit()
            self.db.refresh(flag)
        return flag

    def set_tenant_override(self, flag_name: str, tenant_id: str, enabled: bool):
        """Set tenant-specific override."""
        flag = self.db.query(FeatureFlag).filter(FeatureFlag.name == flag_name).first()
        if flag:
            overrides = flag.tenant_overrides or {}
            overrides[tenant_id] = enabled
            flag.tenant_overrides = overrides
            self.db.commit()

    def delete_flag(self, flag_id: str) -> bool:
        flag = self.db.query(FeatureFlag).filter(FeatureFlag.id == flag_id).first()
        if flag:
            self.db.delete(flag)
            self.db.commit()
            return True
        return False
