"""Event sourcing endpoints."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.api.dependencies import get_current_user
from app.infrastructure.database import get_db_session
from app.modules.events.service import EventSourcingService

router = APIRouter()


@router.get("/{aggregate_type}/{aggregate_id}")
async def get_events(
    aggregate_type: str,
    aggregate_id: str,
    from_version: int = 0,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Get events for an aggregate."""
    service = EventSourcingService(db)
    events = service.get_events(aggregate_type, aggregate_id, from_version)
    return [
        {
            "id": str(e.id),
            "event_type": e.event_type,
            "event_data": e.event_data,
            "version": e.version,
            "created_at": e.created_at.isoformat() if e.created_at else None
        }
        for e in events
    ]


@router.get("/replay/{aggregate_type}/{aggregate_id}")
async def replay_events(
    aggregate_type: str,
    aggregate_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Replay events to reconstruct state."""
    service = EventSourcingService(db)
    return service.replay_events(aggregate_type, aggregate_id)


@router.get("/type/{event_type}")
async def get_events_by_type(
    event_type: str,
    skip: int = 0,
    limit: int = 100,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Get events by type."""
    service = EventSourcingService(db)
    events = service.get_events_by_type(current_user["tenant_id"], event_type, skip, limit)
    return [
        {
            "id": str(e.id),
            "aggregate_id": e.aggregate_id,
            "event_data": e.event_data,
            "version": e.version,
            "created_at": e.created_at.isoformat() if e.created_at else None
        }
        for e in events
    ]
