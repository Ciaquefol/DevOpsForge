import asyncio
import json
from typing import Any


class ActivityBroadcaster:
    def __init__(self):
        self._connections: set = set()
        self._loop: asyncio.AbstractEventLoop | None = None

    def set_loop(self, loop: asyncio.AbstractEventLoop):
        self._loop = loop

    async def connect(self, websocket):
        await websocket.accept()
        self._connections.add(websocket)

    def disconnect(self, websocket):
        self._connections.discard(websocket)

    async def broadcast(self, payload: dict[str, Any]):
        dead = []
        message = json.dumps(payload, default=str)
        for ws in list(self._connections):
            try:
                await ws.send_text(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)

    def publish_sync(self, payload: dict[str, Any]):
        if self._loop and self._loop.is_running():
            asyncio.run_coroutine_threadsafe(self.broadcast(payload), self._loop)


broadcaster = ActivityBroadcaster()
