"""AI recommendation endpoints."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.api.dependencies import get_current_user
from app.infrastructure.database import get_db_session
from app.modules.ai.recommendations import RecommendationService

router = APIRouter()


@router.get("/personalized/{customer_id}")
async def personalized_recommendations(
    customer_id: str,
    limit: int = Query(default=5, le=20),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Get personalized recommendations for a customer."""
    service = RecommendationService(db)
    return service.get_personalized_recommendations(
        customer_id, current_user["tenant_id"], limit
    )


@router.get("/popular")
async def popular_items(
    limit: int = Query(default=10, le=50),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Get popular menu items."""
    service = RecommendationService(db)
    return service.get_popular_items(current_user["tenant_id"], limit)


@router.get("/frequently-bought-together/{item_id}")
async def frequently_bought_together(
    item_id: str,
    limit: int = Query(default=3, le=10),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Get items frequently bought together."""
    service = RecommendationService(db)
    return service.get_frequently_bought_together(
        item_id, current_user["tenant_id"], limit
    )


@router.get("/time-based")
async def time_based_recommendations(
    limit: int = Query(default=5, le=20),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Get time-based recommendations."""
    service = RecommendationService(db)
    return service.get_time_based_recommendations(
        current_user["tenant_id"],
        current_user.get("branch_id"),
        limit
    )
