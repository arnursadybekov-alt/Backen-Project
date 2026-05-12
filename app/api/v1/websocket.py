import asyncio
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from app.core.security import decode_token

logger = logging.getLogger(__name__)
router = APIRouter(tags=["WebSocket"])


class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[int, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, parent_id: int):
        await websocket.accept()
        self.active_connections.setdefault(parent_id, []).append(websocket)
        logger.info(f"Parent {parent_id} connected via WebSocket")

    def disconnect(self, websocket: WebSocket, parent_id: int):
        connections = self.active_connections.get(parent_id, [])
        if websocket in connections:
            connections.remove(websocket)
        if not connections:
            self.active_connections.pop(parent_id, None)

    async def send_to_parent(self, parent_id: int, message: dict):
        for ws in list(self.active_connections.get(parent_id, [])):
            try:
                await ws.send_json(message)
            except Exception:
                self.disconnect(ws, parent_id)


manager = ConnectionManager()


@router.websocket("/ws/notifications")
async def websocket_notifications(websocket: WebSocket, token: str = Query(...)):
    try:
        payload = decode_token(token)
        parent_id = int(payload.get("sub"))
    except Exception:
        await websocket.close(code=4001, reason="Unauthorized")
        return

    await manager.connect(websocket, parent_id)
    try:
        await websocket.send_json({"type": "connected", "message": "Connected to notification stream"})
        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                if data == "ping":
                    await websocket.send_text("pong")
            except asyncio.TimeoutError:
                await websocket.send_json({"type": "ping"})
    except WebSocketDisconnect:
        manager.disconnect(websocket, parent_id)
