"""Offline sync protocol with conflict resolution."""

import uuid
import hashlib
import json
from typing import List, Optional, Dict
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import Column, String, JSON, DateTime, Integer, Text
from app.infrastructure.database import Base
from app.models import generate_uuid


class SyncRecord(Base):
    __tablename__ = "sync_records"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    tenant_id = Column(String(36), nullable=False, index=True)
    branch_id = Column(String(36), nullable=False, index=True)
    device_id = Column(String(100), nullable=False, index=True)
    entity_type = Column(String(50), nullable=False)  # order, payment, inventory, etc.
    entity_id = Column(String(36), nullable=False)
    operation = Column(String(20), nullable=False)  # create, update, delete
    data = Column(JSON)
    version = Column(Integer, default=1)
    checksum = Column(String(64))
    synced = Column(String(20), default="pending")  # pending, synced, conflict
    server_data = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    synced_at = Column(DateTime)


class SyncService:
    def __init__(self, db: Session):
        self.db = db

    def push_changes(self, tenant_id: str, branch_id: str, device_id: str,
                     changes: List[dict]) -> dict:
        """Push offline changes to server. Returns sync results with conflicts."""
        results = {"synced": [], "conflicts": [], "errors": []}

        for change in changes:
            try:
                entity_type = change.get("entity_type")
                entity_id = change.get("entity_id")
                operation = change.get("operation")
                data = change.get("data")
                client_version = change.get("version", 1)
                client_checksum = change.get("checksum")

                # Check for conflicts
                existing = self.db.query(SyncRecord).filter(
                    SyncRecord.entity_type == entity_type,
                    SyncRecord.entity_id == entity_id,
                    SyncRecord.synced == "synced"
                ).order_by(SyncRecord.version.desc()).first()

                if existing and existing.version >= client_version:
                    # Conflict: server version is newer
                    results["conflicts"].append({
                        "entity_type": entity_type,
                        "entity_id": entity_id,
                        "server_version": existing.version,
                        "client_version": client_version,
                        "server_data": existing.data,
                        "client_data": data
                    })
                    sync_status = "conflict"
                else:
                    # No conflict, apply change
                    self._apply_change(entity_type, entity_id, operation, data)
                    sync_status = "synced"

                # Record sync
                record = SyncRecord(
                    id=str(uuid.uuid4()),
                    tenant_id=tenant_id,
                    branch_id=branch_id,
                    device_id=device_id,
                    entity_type=entity_type,
                    entity_id=entity_id,
                    operation=operation,
                    data=data,
                    version=client_version,
                    checksum=client_checksum,
                    synced=sync_status,
                    synced_at=datetime.utcnow() if sync_status == "synced" else None
                )
                self.db.add(record)

                if sync_status == "synced":
                    results["synced"].append({
                        "entity_type": entity_type,
                        "entity_id": entity_id
                    })

            except Exception as e:
                results["errors"].append({
                    "entity_id": change.get("entity_id"),
                    "error": str(e)
                })

        self.db.commit()
        return results

    def pull_changes(self, tenant_id: str, branch_id: str, device_id: str,
                     since_version: int = 0) -> List[dict]:
        """Pull changes since a version number."""
        records = self.db.query(SyncRecord).filter(
            SyncRecord.tenant_id == tenant_id,
            SyncRecord.branch_id == branch_id,
            SyncRecord.synced == "synced",
            SyncRecord.version > since_version
        ).order_by(SyncRecord.version.asc()).all()

        return [
            {
                "entity_type": r.entity_type,
                "entity_id": r.entity_id,
                "operation": r.operation,
                "data": r.data,
                "version": r.version,
                "timestamp": r.synced_at.isoformat() if r.synced_at else None
            }
            for r in records
        ]

    def resolve_conflict(self, conflict_id: str, resolution: str, data: dict = None) -> dict:
        """Resolve a sync conflict."""
        record = self.db.query(SyncRecord).filter(SyncRecord.id == conflict_id).first()
        if not record:
            return {"error": "Conflict not found"}

        if resolution == "accept_server":
            record.synced = "synced"
        elif resolution == "accept_client":
            self._apply_change(record.entity_type, record.entity_id, record.operation, record.data)
            record.synced = "synced"
        elif resolution == "merge":
            self._apply_change(record.entity_type, record.entity_id, record.operation, data)
            record.synced = "synced"

        record.synced_at = datetime.utcnow()
        self.db.commit()
        return {"status": "resolved", "resolution": resolution}

    def _apply_change(self, entity_type: str, entity_id: str, operation: str, data: dict):
        """Apply a synced change to the database."""
        from app.models import Order, MenuItem, InventoryItem, Customer

        model_map = {
            "order": Order,
            "menu_item": MenuItem,
            "inventory_item": InventoryItem,
            "customer": Customer
        }

        model = model_map.get(entity_type)
        if not model:
            return

        if operation == "create":
            obj = model(id=entity_id, **data)
            self.db.add(obj)
        elif operation == "update":
            obj = self.db.query(model).filter(model.id == entity_id).first()
            if obj:
                for key, value in data.items():
                    if hasattr(obj, key):
                        setattr(obj, key, value)
        elif operation == "delete":
            obj = self.db.query(model).filter(model.id == entity_id).first()
            if obj:
                self.db.delete(obj)

        self.db.commit()
