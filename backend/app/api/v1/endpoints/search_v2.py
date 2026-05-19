"""Advanced search endpoints."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.api.dependencies import get_current_user
from app.infrastructure.database import get_db_session
from app.modules.search.service import SearchService

router = APIRouter()


@router.get("/")
async def advanced_search(
    q: str = Query(..., min_length=1),
    type: str = Query(default="all"),
    limit: int = Query(default=20, le=100),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Advanced search with ranking."""
    service = SearchService(db)
    return service.search(
        tenant_id=current_user["tenant_id"],
        query=q,
        entity_type=type,
        limit=limit
    )


@router.get("/suggest")
async def search_suggestions(
    q: str = Query(..., min_length=1),
    limit: int = Query(default=5, le=20),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Get search suggestions/autocomplete."""
    service = SearchService(db)
    return service.get_suggestions(current_user["tenant_id"], q, limit)
