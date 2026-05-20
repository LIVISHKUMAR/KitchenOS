"""Production WebSocket manager with Redis Pub/Sub for multi-instance support."""

import asyncio
import json
import logging
from typing import Dict, Set, Optional, Any
from datetime import datetime
from fastapi import WebSocket
import redis.asyncio as aioredis

from app.core.config import settings

logger = logging.getLogger("kitchenos.websocket")


class WebSocketConnection:
    """Represents a single WebSocket connection."""

    def __init__(self, ws: WebSocket, tenant_id: str, branch_id: str,
                 client_type: str, device_id: str = None):
        self.ws = ws
        self.tenant_id = tenant_id
        self.branch_id = branch_id
        self.client_type = client_type  # pos, kds, admin, display
        self.device_id = device_id or "unknown"
        self.connected_at = datetime.utcnow()
        self.last_ping = datetime.utcnow()

    async def send(self, data: dict) -> bool:
        """Send data to this connection."""
        try:
            await self.ws.send_json(data)
            return True
        except Exception:
            return False

    def to_dict(self) -> dict:
        return {
            "tenant_id": self.tenant_id,
            "branch_id": self.branch_id,
            "client_type": self.client_type,
            "device_id": self.device_id,
            "connected_at": self.connected_at.isoformat()
        }


class WebSocketManager:
    """Production WebSocket manager with pub/sub support."""

    def __init__(self):
        # tenant_id → branch_id → set of connections
        self._connections: Dict[str, Dict[str, Set[WebSocketConnection]]] = {}
        self._redis: Optional[aioredis.Redis] = None
        self._pubsub_task: Optional[asyncio.Task] = None

    async def initialize(self):
        """Initialize Redis connection for pub/sub."""
        try:
            self._redis = aioredis.from_url(
                settings.REDIS_URL,
                decode_responses=True
            )
            await self._redis.ping()
            self._pubsub_task = asyncio.create_task(self._listen_pubsub())
            logger.info("WebSocket manager initialized with Redis pub/sub")
        except Exception as e:
            logger.warning(f"Redis not available, using local-only WebSocket: {e}")

    async def shutdown(self):
        """Clean shutdown."""
        if self._pubsub_task:
            self._pubsub_task.cancel()
        if self._redis:
            await self._redis.close()

    async def connect(self, conn: WebSocketConnection):
        """Register a new WebSocket connection."""
        tenant_id = conn.tenant_id
        branch_id = conn.branch_id

        if tenant_id not in self._connections:
            self._connections[tenant_id] = {}
        if branch_id not in self._connections[tenant_id]:
            self._connections[tenant_id][branch_id] = set()

        self._connections[tenant_id][branch_id].add(conn)
        logger.info(f"Client connected: {conn.client_type} ({conn.device_id}) to {tenant_id}/{branch_id}")

        # Send connection confirmation
        await conn.send({
            "type": "connected",
            "tenant_id": tenant_id,
            "branch_id": branch_id,
            "timestamp": datetime.utcnow().isoformat()
        })

    def disconnect(self, conn: WebSocketConnection):
        """Remove a WebSocket connection."""
        try:
            tenant_conns = self._connections.get(conn.tenant_id, {})
            branch_conns = tenant_conns.get(conn.branch_id, set())
            branch_conns.discard(conn)
            logger.info(f"Client disconnected: {conn.client_type} ({conn.device_id})")
        except Exception:
            pass

    async def broadcast_to_branch(self, tenant_id: str, branch_id: str,
                                   message: dict, exclude_device: str = None):
        """Broadcast message to all connections in a branch.

        When Redis is available, only publishes to Redis. The pub/sub handler
        (_listen_pubsub) will deliver to local connections. This prevents
        double-send in single-instance deployments.
        """
        if self._redis:
            # Publish to Redis — pub/sub handler delivers locally
            await self._redis.publish(
                f"ws:{tenant_id}:{branch_id}",
                json.dumps({"message": message, "exclude_device": exclude_device})
            )
        else:
            # No Redis — send directly to local connections
            await self._send_local(tenant_id, branch_id, message, exclude_device)

    async def broadcast_to_tenant(self, tenant_id: str, message: dict):
        """Broadcast to all connections in a tenant."""
        if self._redis:
            await self._redis.publish(
                f"ws:{tenant_id}:*",
                json.dumps({"message": message})
            )
        else:
            tenant_conns = self._connections.get(tenant_id, {})
            for branch_id in tenant_conns:
                await self._send_local(tenant_id, branch_id, message)

    async def send_to_client_type(self, tenant_id: str, branch_id: str,
                                   client_type: str, message: dict):
        """Send to specific client type (e.g., only KDS clients)."""
        connections = self._connections.get(tenant_id, {}).get(branch_id, set())
        dead = set()

        for conn in connections:
            if conn.client_type == client_type:
                if not await conn.send(message):
                    dead.add(conn)

        for conn in dead:
            self.disconnect(conn)

    async def _send_local(self, tenant_id: str, branch_id: str,
                          message: dict, exclude_device: str = None):
        """Send to local connections."""
        connections = self._connections.get(tenant_id, {}).get(branch_id, set())
        dead = set()

        for conn in connections:
            if exclude_device and conn.device_id == exclude_device:
                continue
            if not await conn.send(message):
                dead.add(conn)

        for conn in dead:
            self.disconnect(conn)

    async def _listen_pubsub(self):
        """Listen for Redis pub/sub messages from other instances."""
        if not self._redis:
            return

        pubsub = self._redis.pubsub()
        await pubsub.psubscribe("ws:*")

        try:
            async for message in pubsub.listen():
                if message["type"] == "pmessage":
                    channel = message["channel"]
                    data = json.loads(message["data"])

                    # Parse channel: ws:tenant_id:branch_id
                    parts = channel.split(":")
                    if len(parts) >= 3:
                        tenant_id = parts[1]
                        branch_id = parts[2]

                        msg = data.get("message", {})
                        exclude = data.get("exclude_device")

                        if branch_id == "*":
                            await self._send_local(tenant_id, None, msg, exclude)
                        else:
                            await self._send_local(tenant_id, branch_id, msg, exclude)
        except asyncio.CancelledError:
            pass
        finally:
            await pubsub.unsubscribe()

    def get_connection_count(self, tenant_id: str = None,
                              branch_id: str = None) -> int:
        """Get number of active connections."""
        if tenant_id and branch_id:
            return len(self._connections.get(tenant_id, {}).get(branch_id, set()))
        elif tenant_id:
            return sum(
                len(conns)
                for conns in self._connections.get(tenant_id, {}).values()
            )
        return sum(
            len(conns)
            for tenant in self._connections.values()
            for conns in tenant.values()
        )

    def get_connections(self) -> list:
        """Get all connections info."""
        result = []
        for tenant_id, branches in self._connections.items():
            for branch_id, connections in branches.items():
                for conn in connections:
                    result.append(conn.to_dict())
        return result


# Global manager
ws_manager = WebSocketManager()


# Event publishers
async def notify_order_created(tenant_id: str, branch_id: str, order_data: dict):
    """Notify all clients about new order."""
    await ws_manager.broadcast_to_branch(tenant_id, branch_id, {
        "type": "order.created",
        "data": order_data,
        "timestamp": datetime.utcnow().isoformat()
    })

    # Also notify KDS specifically
    await ws_manager.send_to_client_type(tenant_id, branch_id, "kds", {
        "type": "kot.new",
        "data": order_data,
        "timestamp": datetime.utcnow().isoformat()
    })


async def notify_order_updated(tenant_id: str, branch_id: str, order_data: dict):
    """Notify about order status change."""
    await ws_manager.broadcast_to_branch(tenant_id, branch_id, {
        "type": "order.updated",
        "data": order_data,
        "timestamp": datetime.utcnow().isoformat()
    })


async def notify_table_updated(tenant_id: str, branch_id: str, table_data: dict):
    """Notify about table status change."""
    await ws_manager.broadcast_to_branch(tenant_id, branch_id, {
        "type": "table.updated",
        "data": table_data,
        "timestamp": datetime.utcnow().isoformat()
    })


async def notify_payment_completed(tenant_id: str, branch_id: str, payment_data: dict):
    """Notify about payment completion."""
    await ws_manager.broadcast_to_branch(tenant_id, branch_id, {
        "type": "payment.completed",
        "data": payment_data,
        "timestamp": datetime.utcnow().isoformat()
    })


async def notify_kot_updated(tenant_id: str, branch_id: str, kot_data: dict):
    """Notify about KOT status change."""
    await ws_manager.broadcast_to_branch(tenant_id, branch_id, {
        "type": "kot.updated",
        "data": kot_data,
        "timestamp": datetime.utcnow().isoformat()
    })


async def notify_customer_display(tenant_id: str, branch_id: str, display_data: dict):
    """Push event to customer display screens."""
    await ws_manager.send_to_client_type(tenant_id, branch_id, "display", display_data)
