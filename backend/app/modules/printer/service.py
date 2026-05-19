"""Thermal printer integration service (ESC/POS)."""

import uuid
from typing import Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import Column, String, Boolean, JSON, DateTime, Integer, Text
from app.infrastructure.database import Base
from app.models import generate_uuid


class Printer(Base):
    __tablename__ = "printers"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    tenant_id = Column(String(36), nullable=False, index=True)
    branch_id = Column(String(36), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    printer_type = Column(String(20), default="network")  # network, usb, bluetooth
    ip_address = Column(String(50))
    port = Column(Integer, default=9100)
    paper_width = Column(Integer, default=80)  # mm
    is_active = Column(Boolean, default=True)
    capabilities = Column(JSON, default={})  # {cut, drawer, beep}
    created_at = Column(DateTime, default=datetime.utcnow)


class PrintJob(Base):
    __tablename__ = "print_jobs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    printer_id = Column(String(36), nullable=False, index=True)
    tenant_id = Column(String(36), nullable=False)
    job_type = Column(String(20), nullable=False)  # kot, bill, receipt
    content = Column(Text, nullable=False)
    status = Column(String(20), default="pending")  # pending, printing, completed, failed
    error = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    printed_at = Column(DateTime)


class PrinterService:
    def __init__(self, db: Session):
        self.db = db

    def register_printer(self, tenant_id: str, data: dict) -> Printer:
        printer = Printer(id=str(uuid.uuid4()), tenant_id=tenant_id, **data)
        self.db.add(printer)
        self.db.commit()
        self.db.refresh(printer)
        return printer

    def get_printers(self, tenant_id: str, branch_id: Optional[str] = None) -> List[Printer]:
        query = self.db.query(Printer).filter(
            Printer.tenant_id == tenant_id,
            Printer.is_active == True
        )
        if branch_id:
            query = query.filter(Printer.branch_id == branch_id)
        return query.all()

    def generate_kot_content(self, order_data: dict) -> str:
        """Generate ESC/POS compatible KOT content."""
        lines = []
        lines.append("\x1b\x40")  # Initialize printer
        lines.append("\x1b\x61\x01")  # Center align
        lines.append("KITCHEN ORDER TICKET\n")
        lines.append("=" * 32 + "\n")
        lines.append(f"Order: {order_data.get('order_number', '')}\n")
        lines.append(f"Table: {order_data.get('table_id', 'N/A')}\n")
        lines.append(f"Type: {order_data.get('order_type', 'dine_in')}\n")
        lines.append("-" * 32 + "\n")
        lines.append("\x1b\x61\x00")  # Left align

        for item in order_data.get("items", []):
            qty = item.get("quantity", 1)
            name = item.get("item_name", "")
            lines.append(f"  {qty}x {name}\n")
            if item.get("cooking_instructions"):
                lines.append(f"     Note: {item['cooking_instructions']}\n")

        lines.append("-" * 32 + "\n")
        lines.append(f"Time: {datetime.now().strftime('%H:%M:%S')}\n")
        lines.append("\x1d\x56\x00")  # Full cut
        return "".join(lines)

    def generate_bill_content(self, order_data: dict) -> str:
        """Generate ESC/POS compatible bill content."""
        lines = []
        lines.append("\x1b\x40")  # Initialize printer
        lines.append("\x1b\x61\x01")  # Center align
        lines.append("TAX INVOICE\n")
        lines.append("=" * 32 + "\n")
        lines.append("\x1b\x61\x00")  # Left align
        lines.append(f"Order: {order_data.get('order_number', '')}\n")
        lines.append(f"Date: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n")
        lines.append("-" * 32 + "\n")

        for item in order_data.get("items", []):
            qty = item.get("quantity", 1)
            name = item.get("item_name", "")[:20]
            total = item.get("total", 0)
            lines.append(f"{qty}x {name:<20} {total:>6.2f}\n")

        lines.append("-" * 32 + "\n")
        subtotal = order_data.get("subtotal", 0)
        tax = order_data.get("tax_amount", 0)
        total = order_data.get("total", 0)
        lines.append(f"{'Subtotal':<24} {subtotal:>6.2f}\n")
        lines.append(f"{'Tax':<24} {tax:>6.2f}\n")
        lines.append(f"{'TOTAL':<24} {total:>6.2f}\n")
        lines.append("=" * 32 + "\n")
        lines.append("\x1b\x61\x01")  # Center
        lines.append("Thank you!\n")
        lines.append("\x1d\x56\x00")  # Full cut
        return "".join(lines)

    def queue_print(self, printer_id: str, tenant_id: str, job_type: str, content: str) -> PrintJob:
        job = PrintJob(
            id=str(uuid.uuid4()),
            printer_id=printer_id,
            tenant_id=tenant_id,
            job_type=job_type,
            content=content,
            status="pending"
        )
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        return job
