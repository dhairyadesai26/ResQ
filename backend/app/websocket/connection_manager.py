"""
ResQ Web - WebSocket Connection Manager
Maintains active real-time connections with frontend clients.
Broadcasts process state updates, events, and performance metrics in real time.
"""

import json
import asyncio
from typing import List, Dict, Any
from fastapi import WebSocket
import logging

logger = logging.getLogger("resq.backend.websocket")


class ConnectionManager:
    """Manages active WebSocket connections."""

    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    def set_loop(self, loop: asyncio.AbstractEventLoop):
        self._loop = loop

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket client connected. Active connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"WebSocket client disconnected. Remaining: {len(self.active_connections)}")

    async def broadcast(self, message: Dict[str, Any]):
        """Broadcasts a JSON-serializable message to all connected clients."""
        if not self.active_connections:
            return

        payload = json.dumps(message, default=str)
        dead_connections = []

        for connection in list(self.active_connections):
            try:
                await connection.send_text(payload)
            except Exception as e:
                logger.debug(f"Failed to send to client: {e}")
                dead_connections.append(connection)

        for dead in dead_connections:
            self.disconnect(dead)

    def broadcast_threadsafe(self, message: Dict[str, Any]):
        """Safe to call from background worker threads and OS hooks."""
        if not self.active_connections:
            return

        try:
            if self._loop and self._loop.is_running():
                asyncio.run_coroutine_threadsafe(self.broadcast(message), self._loop)
        except Exception as e:
            logger.debug(f"Error in threadsafe broadcast: {e}")


ws_manager = ConnectionManager()

