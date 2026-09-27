"""
WebSocket Connection Manager.
Manages active socket registries, presence tracking (ONLINE/OFFLINE), and message dispatching.
"""

import asyncio
from collections import defaultdict
import logging
from typing import Any
import uuid

from fastapi import WebSocket

logger = logging.getLogger("squadsync.websocket")


class WebSocketManager:
    """
    Thread-safe registry for connected WebSockets and presence dispatching.
    Supports multiple concurrent tabs/devices per authenticated gamer.
    """

    def __init__(self):
        # Maps user_id -> set of active WebSocket connections
        self._active_connections: dict[uuid.UUID, set[WebSocket]] = defaultdict(set)
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, user_id: uuid.UUID) -> None:
        """Registers an accepted WebSocket connection for a given user."""
        await websocket.accept()
        async with self._lock:
            self._active_connections[user_id].add(websocket)
            logger.info("User %s connected via WebSocket (active sockets: %d)", user_id, len(self._active_connections[user_id]))

    async def disconnect(self, websocket: WebSocket, user_id: uuid.UUID) -> None:
        """Removes a closed WebSocket from registry."""
        async with self._lock:
            if user_id in self._active_connections:
                self._active_connections[user_id].discard(websocket)
                if not self._active_connections[user_id]:
                    del self._active_connections[user_id]
                    logger.info("User %s has disconnected all WebSocket sessions (OFFLINE)", user_id)

    def is_user_online(self, user_id: uuid.UUID) -> bool:
        """Checks if a gamer currently has at least one active socket open."""
        return user_id in self._active_connections and len(self._active_connections[user_id]) > 0

    async def send_direct_message(self, message: dict[str, Any], recipient_id: uuid.UUID) -> bool:
        """Delivers a real-time message payload to all active sockets of the recipient."""
        async with self._lock:
            sockets = list(self._active_connections.get(recipient_id, []))

        if not sockets:
            return False

        delivered = False
        for ws in sockets:
            try:
                await ws.send_json(message)
                delivered = True
            except Exception as e:
                logger.warning("Failed sending message to socket of user %s: %s", recipient_id, e)
        return delivered

    async def broadcast_to_users(self, message: dict[str, Any], user_ids: list[uuid.UUID]) -> None:
        """Broadcasts a payload to a collection of users (e.g. squad members)."""
        tasks = [self.send_direct_message(message, uid) for uid in user_ids]
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)


# Global singleton instance
ws_manager = WebSocketManager()
