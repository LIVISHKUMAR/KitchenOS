"""Production WebSocket endpoint."""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from app.core.security import decode_token
from app.infrastructure.websocket_manager import ws_manager, WebSocketConnection

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(...),
    client_type: str = Query(default="pos"),
    device_id: str = Query(default="unknown")
):
    """Production WebSocket endpoint.

    Connect: ws://host:8000/api/v1/ws?token=<jwt>&client_type=pos&device_id=tablet-1

    Client types: pos, kds, admin, display

    Messages from server:
    - order.created: New order created
    - order.updated: Order status changed
    - table.updated: Table status changed
    - payment.completed: Payment processed
    - kot.new: New KOT for kitchen
    - kot.updated: KOT status changed

    Messages from client:
    - ping: Keepalive (server responds with pong)
    - ack: Message acknowledgment
    """
    # Validate token
    payload = decode_token(token)
    if not payload:
        await websocket.close(code=4001, reason="Invalid token")
        return

    tenant_id = payload.get("tenant_id")
    branch_id = payload.get("branch_id", "default")

    if not tenant_id:
        await websocket.close(code=4001, reason="Missing tenant_id")
        return

    # Create connection
    conn = WebSocketConnection(
        ws=websocket,
        tenant_id=tenant_id,
        branch_id=branch_id,
        client_type=client_type,
        device_id=device_id
    )

    await ws_manager.connect(conn)

    try:
        while True:
            data = await websocket.receive_json()

            # Handle client messages
            msg_type = data.get("type")

            if msg_type == "ping":
                await websocket.send_json({"type": "pong"})
                conn.last_ping = datetime.utcnow()

            elif msg_type == "ack":
                # Message acknowledgment (for reliability)
                pass

    except WebSocketDisconnect:
        ws_manager.disconnect(conn)
    except Exception:
        ws_manager.disconnect(conn)


from datetime import datetime
