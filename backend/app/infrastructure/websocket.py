"""WebSocket manager for real-time sync across terminals and KDS."""

import json
import asyncio
from typing import Dict, Set, Optional
from fastapi import WebSocket, WebSocketDisconnect
from datetime import datetime


class ConnectionManager:
    """Manages WebSocket connections grouped by tenant/branch."""

    def __init__(self):
        # tenant_id -> branch_id -> set of websockets
        self._connections: Dict[str, Dict[str, Set[WebSocket]]] = {}
        # ws -> (tenant_id, branch_id, client_type)
        self._client_info: Dict[WebSocket, tuple] = {}

    async def connect(self, websocket: WebSocket, tenant_id: str, branch_id: str, client_type: str = "pos"):
        await websocket.accept()
        if tenant_id not in self._connections:
            self._connections[tenant_id] = {}
        if branch_id not in self._connections[tenant_id]:
            self._connections[tenant_id][branch_id] = set()
        self._connections[tenant_id][branch_id].add(websocket)
        self._client_info[websocket] = (tenant_id, branch_id, client_type)

    def disconnect(self, websocket: WebSocket):
        info = self._client_info.pop(websocket, None)
        if info:
            tenant_id, branch_id, _ = info
            if tenant_id in self._connections and branch_id in self._connections[tenant_id]:
                self._connections[tenant_id][branch_id].discard(websocket)

    async def send_to_branch(self, tenant_id: str, branch_id: str, message: dict):
        """Send message to all connections in a branch."""
        if tenant_id in self._connections and branch_id in self._connections[tenant_id]:
            dead = set()
            for ws in self._connections[tenant_id][branch_id]:
                try:
                    await ws.send_json(message)
                except Exception:
                    dead.add(ws)
            for ws in dead:
                self.disconnect(ws)

    async def send_to_tenant(self, tenant_id: str, message: dict):
        """Send message to all connections in a tenant."""
        if tenant_id in self._connections:
            for branch_id in self._connections[tenant_id]:
                await self.send_to_branch(tenant_id, branch_id, message)

    async def broadcast(self, message: dict):
        """Send to all connected clients."""
        for tenant_id in list(self._connections.keys()):
            await self.send_to_tenant(tenant_id, message)

    def get_connection_count(self, tenant_id: Optional[str] = None, branch_id: Optional[str] = None) -> int:
        if tenant_id and branch_id:
            return len(self._connections.get(tenant_id, {}).get(branch_id, set()))
        elif tenant_id:
            return sum(len(ws_set) for ws_set in self._connections.get(tenant_id, {}).values())
        return sum(len(ws_set) for tenant in self._connections.values() for ws_set in tenant.values())


# Global connection manager
ws_manager = ConnectionManager()


async def notify_order_update(tenant_id: str, branch_id: str, order_data: dict):
    """Send order update to all clients in the branch."""
    await ws_manager.send_to_branch(tenant_id, branch_id, {
        "type": "order_update",
        "data": order_data,
        "timestamp": datetime.utcnow().isoformat()
    })


async def notify_kot_update(tenant_id: str, branch_id: str, kot_data: dict):
    """Send KOT update to kitchen displays."""
    await ws_manager.send_to_branch(tenant_id, branch_id, {
        "type": "kot_update",
        "data": kot_data,
        "timestamp": datetime.utcnow().isoformat()
    })


async def notify_table_update(tenant_id: str, branch_id: str, table_data: dict):
    """Send table status update."""
    await ws_manager.send_to_branch(tenant_id, branch_id, {
        "type": "table_update",
        "data": table_data,
        "timestamp": datetime.utcnow().isoformat()
    })


async def notify_payment_update(tenant_id: str, branch_id: str, payment_data: dict):
    """Send payment notification."""
    await ws_manager.send_to_branch(tenant_id, branch_id, {
        "type": "payment_update",
        "data": payment_data,
        "timestamp": datetime.utcnow().isoformat()
    })
