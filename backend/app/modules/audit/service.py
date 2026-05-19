"""Audit logging service for tracking all data mutations."""

from typing import Optional
from sqlalchemy.orm import Session
from datetime import datetime
import json
import uuid

from app.models import AuditLog


class AuditService:
    def __init__(self, db: Session):
        self.db = db

    def log(
        self,
        tenant_id: str,
        user_id: str,
        action: str,
        resource_type: str,
        resource_id: str,
        old_value: Optional[dict] = None,
        new_value: Optional[dict] = None,
        branch_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        request_id: Optional[str] = None
    ):
        """Create an audit log entry."""
        audit_log = AuditLog(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            user_id=user_id,
            branch_id=branch_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            old_value=old_value,
            new_value=new_value,
            ip_address=ip_address,
            user_agent=user_agent,
            request_id=request_id,
            created_at=datetime.utcnow()
        )
        self.db.add(audit_log)
        self.db.commit()
        return audit_log

    def log_create(self, tenant_id: str, user_id: str, resource_type: str,
                   resource_id: str, data: dict, **kwargs):
        """Log a create action."""
        return self.log(
            tenant_id=tenant_id,
            user_id=user_id,
            action="create",
            resource_type=resource_type,
            resource_id=resource_id,
            new_value=data,
            **kwargs
        )

    def log_update(self, tenant_id: str, user_id: str, resource_type: str,
                   resource_id: str, old_data: dict, new_data: dict, **kwargs):
        """Log an update action."""
        return self.log(
            tenant_id=tenant_id,
            user_id=user_id,
            action="update",
            resource_type=resource_type,
            resource_id=resource_id,
            old_value=old_data,
            new_value=new_data,
            **kwargs
        )

    def log_delete(self, tenant_id: str, user_id: str, resource_type: str,
                   resource_id: str, data: dict, **kwargs):
        """Log a delete action."""
        return self.log(
            tenant_id=tenant_id,
            user_id=user_id,
            action="delete",
            resource_type=resource_type,
            resource_id=resource_id,
            old_value=data,
            **kwargs
        )

    def get_audit_logs(
        self,
        tenant_id: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        user_id: Optional[str] = None,
        action: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ):
        """Query audit logs with filters."""
        query = self.db.query(AuditLog).filter(AuditLog.tenant_id == tenant_id)

        if resource_type:
            query = query.filter(AuditLog.resource_type == resource_type)
        if resource_id:
            query = query.filter(AuditLog.resource_id == resource_id)
        if user_id:
            query = query.filter(AuditLog.user_id == user_id)
        if action:
            query = query.filter(AuditLog.action == action)

        return query.order_by(AuditLog.created_at.desc()).offset(skip).limit(limit).all()


def get_changed_fields(old_data: dict, new_data: dict) -> tuple:
    """Compare old and new data, return only changed fields."""
    old_filtered = {}
    new_filtered = {}

    for key in new_data:
        if key in old_data:
            if old_data[key] != new_data[key]:
                old_filtered[key] = old_data[key]
                new_filtered[key] = new_data[key]
        else:
            new_filtered[key] = new_data[key]

    return old_filtered, new_filtered


def model_to_dict(obj) -> dict:
    """Convert SQLAlchemy model to dict for audit logging."""
    if obj is None:
        return {}
    result = {}
    for column in obj.__table__.columns:
        value = getattr(obj, column.name)
        if isinstance(value, datetime):
            value = value.isoformat()
        elif hasattr(value, '__str__'):
            value = str(value)
        result[column.name] = value
    return result
