"""Offline sync endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
from app.api.dependencies import get_current_user
from app.infrastructure.database import get_db_session
from app.modules.sync.service import SyncService

router = APIRouter()


class SyncChange(BaseModel):
    entity_type: str
    entity_id: str
    operation: str
    data: dict
    version: int = 1
    checksum: str = None


class SyncPush(BaseModel):
    device_id: str
    changes: List[SyncChange]


@router.post("/push")
async def push_changes(
    data: SyncPush,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Push offline changes to server."""
    service = SyncService(db)
    return service.push_changes(
        tenant_id=current_user["tenant_id"],
        branch_id=current_user.get("branch_id", ""),
        device_id=data.device_id,
        changes=[c.model_dump() for c in data.changes]
    )


@router.get("/pull")
async def pull_changes(
    device_id: str,
    since_version: int = 0,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Pull changes since a version."""
    service = SyncService(db)
    return service.pull_changes(
        tenant_id=current_user["tenant_id"],
        branch_id=current_user.get("branch_id", ""),
        device_id=device_id,
        since_version=since_version
    )


@router.post("/resolve/{conflict_id}")
async def resolve_conflict(
    conflict_id: str,
    resolution: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Resolve a sync conflict."""
    service = SyncService(db)
    return service.resolve_conflict(conflict_id, resolution)
