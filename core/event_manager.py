"""
KrystalOS — core/event_manager.py
PHASE 3 STUB: WebSocket-based Event Bus for inter-widget communication.

Widgets declare events_emitted / events_subscribed in krystal.json.
EventManager will wire those declarations into live pub-sub channels.
"""

from __future__ import annotations

import asyncio
from typing import Any, Callable

# Future Phase 3 imports (uncomment when implementing):
# import websockets
# from websockets.server import WebSocketServerProtocol


class EventManager:
    """
    Central event bus for KrystalOS widgets.

    Phase 3 will:
      - Run a local WebSocket server (default ws://localhost:4242).
      - Route events by name between subscribed widgets.
      - Persist an event log for replay / debugging.
      - Support typed payloads validated via Pydantic.

    Current behaviour: all methods are no-ops or raise NotImplementedError.
    """

    def __init__(self, host: str = "localhost", port: int = 4242) -> None:
        self.host = host
        self.port = port
        # TODO (Phase 3): replace with async-safe subscriber registry
        self._subscribers: dict[str, list[Callable]] = {}

    # ------------------------------------------------------------------
    # Public API (Phase 3 contract)
    # ------------------------------------------------------------------

    def subscribe(self, event: str, handler: Callable[[Any], None]) -> None:
        """
        Register *handler* to be called whenever *event* is emitted.

        Phase 3 will support coroutine handlers for async widgets.
        """
        raise NotImplementedError(
            f"EventManager.subscribe('{event}') — Phase 3 not yet implemented."
        )

    def emit(self, event: str, payload: Any = None) -> None:
        """
        Broadcast *event* with optional *payload* to all subscribers.

        Phase 3 will serialise payload as JSON and push over WebSocket.
        """
        raise NotImplementedError(
            f"EventManager.emit('{event}') — Phase 3 not yet implemented."
        )

    async def connect_ws(self, url: str) -> None:
        """
        Connect to a remote KrystalOS event bus at *url*.

        Phase 3 will use this for multi-host widget meshes.
        """
        raise NotImplementedError(
            f"EventManager.connect_ws('{url}') — Phase 3 not yet implemented."
        )

    async def start_server(self) -> None:
        """Start the local WebSocket event bus server. Phase 3 stub."""
        raise NotImplementedError(
            "EventManager.start_server() — Phase 3 not yet implemented."
        )
