"""WebSocket endpoint for real-time sync."""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from app.infrastructure.websocket import ws_manager
from app.core.security import decode_token

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(...),
    client_type: str = Query(default="pos")
):
    """WebSocket endpoint for real-time POS/KDS sync.

    Connect with: ws://host:8000/api/v1/ws?token=<jwt>&client_type=pos|kds|admin
    """
    # Validate token
    payload = decode_token(token)
    if not payload:
        await websocket.close(code=4001, reason="Invalid token")
        return

    tenant_id = payload.get("tenant_id")
    branch_id = payload.get("branch_id", "default")

    if not tenant_id:
        await websocket.close(code=4001, reason="Missing tenant_id in token")
        return

    await ws_manager.connect(websocket, tenant_id, branch_id, client_type)

    try:
        while True:
            # Keep connection alive, handle client messages
            data = await websocket.receive_json()

            # Handle ping/pong
            if data.get("type") == "ping":
                await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception:
        ws_manager.disconnect(websocket)
