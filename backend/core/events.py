"""Thread-safe per-simulation event bus for streaming progress over SSE.

The simulation runs in a worker thread (FastAPI BackgroundTasks invoke sync
functions in a threadpool). The SSE generator runs on the main asyncio loop.
We bridge the two with ``loop.call_soon_threadsafe``.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

logger = logging.getLogger(__name__)

Event = dict[str, Any]
_Sentinel = object()


class EventBus:
    """Replayable pub/sub channel for one simulation's lifecycle events."""

    def __init__(self, loop: asyncio.AbstractEventLoop) -> None:
        self._loop = loop
        self._history: list[Event] = []
        self._subscribers: list[asyncio.Queue[Event | object]] = []
        self._closed = False

    def snapshot(self) -> list[Event]:
        return list(self._history)

    def is_closed(self) -> bool:
        return self._closed

    def subscribe(self) -> asyncio.Queue[Event | object]:
        queue: asyncio.Queue[Event | object] = asyncio.Queue()
        self._subscribers.append(queue)
        return queue

    def unsubscribe(self, queue: asyncio.Queue[Event | object]) -> None:
        try:
            self._subscribers.remove(queue)
        except ValueError:
            pass

    def publish(self, event: Event) -> None:
        """Thread-safe publish. Safe to call from worker threads."""
        try:
            self._loop.call_soon_threadsafe(self._publish_sync, event)
        except RuntimeError:
            logger.warning("Event loop closed; dropping event %s", event.get("type"))

    def _publish_sync(self, event: Event) -> None:
        if self._closed:
            return
        self._history.append(event)
        for queue in list(self._subscribers):
            queue.put_nowait(event)

    def close(self) -> None:
        try:
            self._loop.call_soon_threadsafe(self._close_sync)
        except RuntimeError:
            self._close_sync()

    def _close_sync(self) -> None:
        self._closed = True
        for queue in list(self._subscribers):
            queue.put_nowait(_Sentinel)


SENTINEL = _Sentinel
