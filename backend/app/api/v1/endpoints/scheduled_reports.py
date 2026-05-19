"""Scheduled report endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
from datetime import datetime
from app.api.dependencies import get_current_user
from app.infrastructure.database import get_db_session
from app.modules.scheduled_report.service import ScheduledReportService

router = APIRouter()


class ScheduledReportCreate(BaseModel):
    name: str
    report_type: str
    frequency: str  # daily, weekly, monthly
    recipients: List[str]
    config: dict = {}


@router.post("/", status_code=201)
async def create_scheduled_report(
    data: ScheduledReportCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    service = ScheduledReportService(db)
    return service.create(current_user["tenant_id"], data.model_dump())


@router.get("/")
async def list_scheduled_reports(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    service = ScheduledReportService(db)
    return service.get_scheduled_reports(current_user["tenant_id"])


@router.delete("/{report_id}")
async def delete_scheduled_report(
    report_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    service = ScheduledReportService(db)
    if not service.delete(report_id, current_user["tenant_id"]):
        raise HTTPException(status_code=404, detail="Report not found")
    return {"message": "Report deleted"}
