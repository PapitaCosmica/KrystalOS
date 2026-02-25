from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from core.events.bus import event_bus

router = APIRouter()

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await event_bus.connect(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            # Handle incoming widget events here
            # E.g., a widget broadcasts a state change to other widgets
            
            # Re-broadcast to everyone (basic implementation)
            await event_bus.broadcast({"event": "widget_update", "data": data})
    except WebSocketDisconnect:
        event_bus.disconnect(websocket)
