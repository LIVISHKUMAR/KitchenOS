"""Scheduled report delivery service."""

import uuid
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import Column, String, Boolean, JSON, DateTime, Integer
from app.infrastructure.database import Base
from app.models import generate_uuid


class ScheduledReport(Base):
    __tablename__ = "scheduled_reports"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    tenant_id = Column(String(36), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    report_type = Column(String(50), nullable=False)  # daily_sales, item_wise, inventory, etc.
    frequency = Column(String(20), nullable=False)  # daily, weekly, monthly
    recipients = Column(JSON, default=[])  # ["email1@example.com", ...]
    config = Column(JSON, default={})  # {branch_id, date_range, etc.}
    is_active = Column(Boolean, default=True)
    last_sent_at = Column(DateTime)
    next_send_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)


class ScheduledReportService:
    def __init__(self, db: Session):
        self.db = db

    def create(self, tenant_id: str, data: dict) -> ScheduledReport:
        report = ScheduledReport(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            **data
        )
        self.db.add(report)
        self.db.commit()
        self.db.refresh(report)
        return report

    def get_scheduled_reports(self, tenant_id: str) -> List[ScheduledReport]:
        return self.db.query(ScheduledReport).filter(
            ScheduledReport.tenant_id == tenant_id,
            ScheduledReport.is_active == True
        ).all()

    def delete(self, report_id: str, tenant_id: str) -> bool:
        report = self.db.query(ScheduledReport).filter(
            ScheduledReport.id == report_id,
            ScheduledReport.tenant_id == tenant_id
        ).first()
        if report:
            report.is_active = False
            self.db.commit()
            return True
        return False

    def get_reports_due(self) -> List[ScheduledReport]:
        """Get reports that are due for delivery."""
        return self.db.query(ScheduledReport).filter(
            ScheduledReport.is_active == True,
            ScheduledReport.next_send_at <= datetime.utcnow()
        ).all()
