"""Scheduler and worker management endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from app.api.dependencies import get_current_user
from app.workers.scheduler import scheduler
from app.workers.webhook_worker import webhook_worker

router = APIRouter()


@router.get("/tasks")
async def list_scheduled_tasks(
    current_user: dict = Depends(get_current_user)
):
    """List all scheduled tasks."""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    return scheduler.get_status()


@router.get("/webhook-worker")
async def webhook_worker_status(
    current_user: dict = Depends(get_current_user)
):
    """Get webhook worker status."""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    return webhook_worker.get_status()
