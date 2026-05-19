from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.api.dependencies import get_current_user
from app.infrastructure.database import get_db_session
from app.modules.audit.service import AuditService
from app.modules.auth.rbac import require_permission

router = APIRouter()


@router.get("/")
async def list_audit_logs(
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    user_id: Optional[str] = None,
    action: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: dict = Depends(require_permission("audit:read")),
    db: Session = Depends(get_db_session)
):
    audit_service = AuditService(db)
    logs = audit_service.get_audit_logs(
        tenant_id=current_user["tenant_id"],
        resource_type=resource_type,
        resource_id=resource_id,
        user_id=user_id,
        action=action,
        skip=skip,
        limit=limit
    )

    return [
        {
            "id": str(log.id),
            "tenant_id": str(log.tenant_id),
            "user_id": str(log.user_id),
            "branch_id": str(log.branch_id) if log.branch_id else None,
            "action": log.action,
            "resource_type": log.resource_type,
            "resource_id": str(log.resource_id),
            "old_value": log.old_value,
            "new_value": log.new_value,
            "ip_address": log.ip_address,
            "created_at": log.created_at.isoformat() if log.created_at else None
        }
        for log in logs
    ]
