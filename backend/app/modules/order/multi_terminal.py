"""Multi-terminal concurrent access management."""

import uuid
import logging
from typing import Optional, Dict
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.models import Order, DiningTable

logger = logging.getLogger("kitchenos.multi_terminal")


class TableLock:
    """Optimistic locking for table operations."""

    def __init__(self, db: Session):
        self.db = db
        self._locks: Dict[str, dict] = {}  # table_id → {device_id, expires_at}

    def acquire_lock(self, table_id: str, device_id: str,
                     timeout_seconds: int = 30) -> bool:
        """Attempt to acquire a lock on a table."""
        now = datetime.utcnow()

        # Check existing lock
        if table_id in self._locks:
            lock = self._locks[table_id]
            if lock["expires_at"] > now and lock["device_id"] != device_id:
                return False  # Locked by another device
            # Lock expired or same device, can acquire
            if lock["device_id"] == device_id:
                # Extend lock
                lock["expires_at"] = now + timedelta(seconds=timeout_seconds)
                return True

        # Acquire new lock
        self._locks[table_id] = {
            "device_id": device_id,
            "acquired_at": now,
            "expires_at": now + timedelta(seconds=timeout_seconds)
        }
        return True

    def release_lock(self, table_id: str, device_id: str) -> bool:
        """Release a table lock."""
        if table_id in self._locks:
            lock = self._locks[table_id]
            if lock["device_id"] == device_id:
                del self._locks[table_id]
                return True
        return False

    def is_locked(self, table_id: str, device_id: str = None) -> bool:
        """Check if a table is locked."""
        if table_id not in self._locks:
            return False

        lock = self._locks[table_id]
        if lock["expires_at"] < datetime.utcnow():
            del self._locks[table_id]
            return False

        if device_id and lock["device_id"] == device_id:
            return False  # Not locked for this device

        return True

    def get_lock_info(self, table_id: str) -> Optional[dict]:
        """Get lock information for a table."""
        if table_id in self._locks:
            lock = self._locks[table_id]
            if lock["expires_at"] > datetime.utcnow():
                return lock
            else:
                del self._locks[table_id]
        return None

    def cleanup_expired(self):
        """Remove expired locks."""
        now = datetime.utcnow()
        expired = [
            tid for tid, lock in self._locks.items()
            if lock["expires_at"] < now
        ]
        for tid in expired:
            del self._locks[tid]


class OrderConflictDetector:
    """Detect and handle order conflicts from multiple terminals."""

    def __init__(self, db: Session):
        self.db = db

    def check_conflict(self, order_id: str, expected_version: int = None) -> dict:
        """Check if an order has been modified by another terminal."""
        order = self.db.query(Order).filter(Order.id == order_id).first()
        if not order:
            return {"conflict": False, "error": "Order not found"}

        # Use updated_at as version indicator
        current_version = int(order.updated_at.timestamp()) if order.updated_at else 0

        if expected_version and current_version != expected_version:
            return {
                "conflict": True,
                "message": "Order was modified by another terminal",
                "current_version": current_version,
                "expected_version": expected_version
            }

        return {"conflict": False, "version": current_version}

    def detect_duplicate_order(self, idempotency_key: str) -> Optional[dict]:
        """Detect if an order with this idempotency key already exists."""
        if not idempotency_key:
            return None

        existing = self.db.query(Order).filter(
            Order.idempotency_key == idempotency_key
        ).first()

        if existing:
            return {
                "duplicate": True,
                "existing_order_id": str(existing.id),
                "existing_order_number": existing.order_number,
                "status": existing.status
            }

        return None


class TerminalManager:
    """Manage multiple POS terminals."""

    def __init__(self):
        self._terminals: Dict[str, dict] = {}

    def register_terminal(self, device_id: str, branch_id: str,
                          user_id: str, terminal_type: str = "pos") -> dict:
        """Register a terminal."""
        terminal = {
            "device_id": device_id,
            "branch_id": branch_id,
            "user_id": user_id,
            "terminal_type": terminal_type,
            "registered_at": datetime.utcnow().isoformat(),
            "last_active": datetime.utcnow().isoformat()
        }
        self._terminals[device_id] = terminal
        return terminal

    def heartbeat(self, device_id: str):
        """Update terminal last active time."""
        if device_id in self._terminals:
            self._terminals[device_id]["last_active"] = datetime.utcnow().isoformat()

    def get_active_terminals(self, branch_id: str) -> list:
        """Get all active terminals for a branch."""
        now = datetime.utcnow()
        active = []

        for device_id, terminal in self._terminals.items():
            if terminal["branch_id"] != branch_id:
                continue

            last_active = datetime.fromisoformat(terminal["last_active"])
            if (now - last_active).seconds < 300:  # 5 minute timeout
                active.append(terminal)

        return active

    def get_terminal_count(self, branch_id: str) -> int:
        """Get number of active terminals."""
        return len(self.get_active_terminals(branch_id))


# Global instances
table_lock = TableLock(None)  # Will be initialized with db
terminal_manager = TerminalManager()
