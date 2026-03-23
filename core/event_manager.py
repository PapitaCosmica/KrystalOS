"""
KrystalOS — core/event_manager.py
Phase 3: The Nervous System (Event Bus)
Handles realtime WebSocket communication between widgets.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from core.discovery import WidgetRegistry

logger = logging.getLogger("krystal.events")
router = APIRouter(prefix="/ws", tags=["events"])

class EventManager:
    """Manages active WebSockets and broadcasts events based on krystal.json capabilities."""

    def __init__(self) -> None:
        # Map of widget_name -> WebSocket connection
        self.active_connections: dict[str, WebSocket] = {}

    async def connect(self, widget_name: str, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections[widget_name] = websocket
        logger.info("[EventBus] Widget '%s' connected to the Nervous System.", widget_name)

    def disconnect(self, widget_name: str) -> None:
        if widget_name in self.active_connections:
            del self.active_connections[widget_name]
            logger.info("[EventBus] Widget '%s' disconnected.", widget_name)

    async def broadcast(self, sender: str, event: str, data: Any, registry: WidgetRegistry) -> None:
        """
        Broadcast an event.
        Only sends to widgets whose krystal.json says they subscribe to this event.
        """
        sender_entry = registry.get(sender)
        if not sender_entry:
            logger.warning("[EventBus] Rejected event '%s' from unknown sender '%s'", event, sender)
            return
            
        # Optional: Validate sender is allowed to emit this event
        if event not in sender_entry.manifest.capabilities.events_emitted:
            logger.warning("[EventBus] Sender '%s' is not authorized to emit '%s'. Please add it to krystal.json", sender, event)
        
        payload = json.dumps({
            "sender": sender,
            "event": event,
            "data": data
        })

        dispatched = 0
        for target_name, ws in self.active_connections.items():
            if target_name == sender:
                continue # Don't echo back to sender unless needed
                
            target_entry = registry.get(target_name)
            if not target_entry:
                continue
                
            # Check if target is subscribed
            if event in target_entry.manifest.capabilities.events_subscribed or "*" in target_entry.manifest.capabilities.events_subscribed:
                try:
                    await ws.send_text(payload)
                    dispatched += 1
                except Exception as e:
                    logger.error("[EventBus] Failed to send to '%s': %s", target_name, e)

        logger.info("[EventBus] Event '%s' from '%s' dispatched to %d subscribers.", event, sender, dispatched)


# Global instance
manager = EventManager()

@router.websocket("/events/{widget_name}")
async def websocket_endpoint(websocket: WebSocket, widget_name: str):
    """
    Krystal-Bridge JS will connect here: ws://localhost:8000/ws/events/<widget_name>
    """
    # Need to access registry to validate subscriptions during broadcast.
    # We will import the global registry from core.main
    from core.main import registry
    
    await manager.connect(widget_name, websocket)
    try:
        while True:
            text = await websocket.receive_text()
            try:
                msg = json.loads(text)
                sender = msg.get("sender", widget_name)
                event = msg.get("event")
                data = msg.get("data", {})
                
                if event:
                    await manager.broadcast(sender, event, data, registry)
            except json.JSONDecodeError:
                logger.error("[EventBus] Invalid JSON received from '%s': %s", widget_name, text)
                
    except WebSocketDisconnect:
        manager.disconnect(widget_name)
