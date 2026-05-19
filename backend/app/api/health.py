"""Comprehensive health check endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime
import psutil
import os

from app.infrastructure.database import get_db_session
from app.infrastructure.cache import get_redis
from app.core.config import settings

router = APIRouter()


@router.get("/health")
async def health_check():
    """Basic health check."""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


@router.get("/health/detailed")
async def detailed_health(db: Session = Depends(get_db_session)):
    """Detailed health check with dependency status."""
    checks = {}

    # Database check
    try:
        db.execute("SELECT 1" if settings.DATABASE_URL.startswith("postgresql") else "SELECT 1")
        checks["database"] = {"status": "healthy", "type": "sqlite" if "sqlite" in settings.DATABASE_URL else "postgresql"}
    except Exception as e:
        checks["database"] = {"status": "unhealthy", "error": str(e)}

    # Redis check
    try:
        r = get_redis()
        if r:
            r.ping()
            checks["redis"] = {"status": "healthy"}
        else:
            checks["redis"] = {"status": "not_configured"}
    except Exception as e:
        checks["redis"] = {"status": "unhealthy", "error": str(e)}

    # System resources
    try:
        checks["system"] = {
            "cpu_percent": psutil.cpu_percent(interval=0.1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage("/").percent if os.name != "nt" else psutil.disk_usage("C:\\").percent,
            "pid": os.getpid()
        }
    except Exception:
        checks["system"] = {"status": "unavailable"}

    # Overall status
    all_healthy = all(
        c.get("status") in ("healthy", "not_configured")
        for c in checks.values()
        if isinstance(c, dict) and "status" in c
    )

    return {
        "status": "healthy" if all_healthy else "degraded",
        "version": settings.APP_VERSION,
        "timestamp": datetime.utcnow().isoformat(),
        "checks": checks
    }


@router.get("/health/ready")
async def readiness(db: Session = Depends(get_db_session)):
    """Kubernetes readiness probe."""
    try:
        db.execute("SELECT 1")
        return {"ready": True}
    except Exception:
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=503, content={"ready": False})


@router.get("/health/live")
async def liveness():
    """Kubernetes liveness probe."""
    return {"alive": True}
