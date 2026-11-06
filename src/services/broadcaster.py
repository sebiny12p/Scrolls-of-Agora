"""
WebSocket Event Broadcaster for Scrolls of Agora.
Provides pub/sub broadcasting for real-time market orderbooks,
outbid alerts, trade executions, and courier parcel arrivals.
"""

import asyncio
import json
from typing import Set, Dict, Any
from fastapi import WebSocket


class EventBroadcaster:
    """Singleton connection pool for active WebSocket telemetry clients."""

    def __init__(self):
        self._connections: Set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self._connections.add(websocket)

    async def disconnect(self, websocket: WebSocket) -> None:
        async with self._lock:
            self._connections.discard(websocket)

    async def broadcast(self, event_type: str, payload: Dict[str, Any]) -> None:
        """Broadcasts a JSON payload to all active WebSocket clients."""
        if not self._connections:
            return

        message = json.dumps({"event": event_type, "data": payload})
        dead_connections = set()

        async with self._lock:
            clients = list(self._connections)

        for ws in clients:
            try:
                await ws.send_text(message)
            except Exception:
                dead_connections.add(ws)

        if dead_connections:
            async with self._lock:
                self._connections.difference_update(dead_connections)

    def broadcast_sync(self, event_type: str, payload: Dict[str, Any]) -> None:
        """Thread-safe synchronous wrapper for background workers and sync repositories."""
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self.broadcast(event_type, payload))
        except RuntimeError:
            pass


broadcaster = EventBroadcaster()
