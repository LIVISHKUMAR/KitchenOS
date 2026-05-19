"""Application Performance Monitoring endpoints."""

from fastapi import APIRouter, Depends
from app.api.dependencies import get_current_user
from app.infrastructure.apm import performance_tracker, error_tracker

router = APIRouter()


@router.get("/metrics")
async def get_performance_metrics(
    current_user: dict = Depends(get_current_user)
):
    """Get application performance metrics."""
    if current_user.get("role") != "admin":
        return {"error": "Admin only"}
    return performance_tracker.get_metrics()


@router.get("/errors")
async def get_errors(
    limit: int = 50,
    current_user: dict = Depends(get_current_user)
):
    """Get recent errors."""
    if current_user.get("role") != "admin":
        return {"error": "Admin only"}
    return {
        "errors": error_tracker.get_errors(limit),
        "counts": error_tracker.get_error_counts()
    }
