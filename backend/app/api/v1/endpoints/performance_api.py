"""Performance monitoring endpoints."""

from fastapi import APIRouter, Depends
from app.api.dependencies import get_current_user
from app.infrastructure.performance import query_profiler, n_plus_one_detector, response_cache
from app.infrastructure.security_advanced import brute_force, ip_allowlist, activity_detector

router = APIRouter()


@router.get("/query-stats")
async def query_stats(
    current_user: dict = Depends(get_current_user)
):
    """Get database query statistics."""
    if current_user.get("role") != "admin":
        return {"error": "Admin only"}
    return query_profiler.get_stats()


@router.get("/slow-queries")
async def slow_queries(
    limit: int = 20,
    current_user: dict = Depends(get_current_user)
):
    """Get slow queries."""
    if current_user.get("role") != "admin":
        return {"error": "Admin only"}
    return query_profiler.get_slow_queries(limit)


@router.get("/cache-stats")
async def cache_stats(
    current_user: dict = Depends(get_current_user)
):
    """Get cache statistics."""
    if current_user.get("role") != "admin":
        return {"error": "Admin only"}
    return response_cache.get_stats()


@router.get("/security-status")
async def security_status(
    current_user: dict = Depends(get_current_user)
):
    """Get security status."""
    if current_user.get("role") != "admin":
        return {"error": "Admin only"}
    return {
        "brute_force": brute_force.get_status(),
        "ip_allowlist": ip_allowlist.get_status(),
        "recent_alerts": activity_detector.get_alerts(10)
    }
