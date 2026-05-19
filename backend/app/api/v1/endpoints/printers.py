"""Printer management endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel
from app.api.dependencies import get_current_user
from app.infrastructure.database import get_db_session
from app.modules.printer.service import PrinterService

router = APIRouter()


class PrinterCreate(BaseModel):
    branch_id: str
    name: str
    printer_type: str = "network"
    ip_address: Optional[str] = None
    port: int = 9100
    paper_width: int = 80


class PrintRequest(BaseModel):
    printer_id: str
    job_type: str  # kot, bill, receipt
    order_data: dict


@router.post("/", status_code=201)
async def register_printer(
    data: PrinterCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    service = PrinterService(db)
    return service.register_printer(current_user["tenant_id"], data.model_dump())


@router.get("/")
async def list_printers(
    branch_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    service = PrinterService(db)
    return service.get_printers(current_user["tenant_id"], branch_id)


@router.post("/print")
async def print_document(
    data: PrintRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    service = PrinterService(db)

    if data.job_type == "kot":
        content = service.generate_kot_content(data.order_data)
    elif data.job_type == "bill":
        content = service.generate_bill_content(data.order_data)
    else:
        content = str(data.order_data)

    job = service.queue_print(
        printer_id=data.printer_id,
        tenant_id=current_user["tenant_id"],
        job_type=data.job_type,
        content=content
    )
    return {"job_id": str(job.id), "status": "queued"}
