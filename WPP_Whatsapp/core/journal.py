"""Opt-in private event journal attached to client-owned subscriptions."""

from __future__ import annotations

import asyncio
from pathlib import Path
from types import TracebackType
from typing import TYPE_CHECKING, Any, Callable, Optional, Union

from .consumers import DurableConsumer
from .event_buffer import EventBuffer

if TYPE_CHECKING:
    from .subscriptions import ClientEvents


class EventJournal:
    def __init__(
        self,
        events: ClientEvents,
        path: Union[str, Path],
        *,
        namespace: str = "default",
        capacity: int = 10000,
        retention: float = 86400,
    ) -> None:
        if not path:
            raise ValueError("A durable journal requires a nonempty path")
        self.events = events
        self.buffer = EventBuffer(capacity, path=path, namespace=namespace, retention=retention)
        self._remove: Optional[Callable[[], None]] = None
        self._active: set[asyncio.Future[None]] = set()
        self._closed = False

    async def _receive(self, message: dict[str, Any]) -> None:
        if self._closed:
            return
        completed = asyncio.get_running_loop().create_future()
        self._active.add(completed)
        try:
            await self.buffer.append(message)
        finally:
            if not completed.done():
                completed.set_result(None)
            self._active.discard(completed)

    def consumer(
        self,
        consumer_id: str,
        *,
        lease_seconds: float = 60,
        max_attempts: int = 5,
        retry_delay: float = 1,
    ) -> DurableConsumer:
        assert self.buffer.store is not None
        return DurableConsumer(
            self.buffer.store,
            consumer_id,
            lease_seconds=lease_seconds,
            max_attempts=max_attempts,
            retry_delay=retry_delay,
        )

    async def read(self, after: int = 0, limit: int = 50) -> dict[str, Any]:
        return await asyncio.to_thread(self.buffer.read, after, limit)

    async def __aenter__(self) -> EventJournal:
        if self._remove is not None or self._closed:
            raise RuntimeError("A journal can be entered only once")
        self._remove = self.events.on_message(self._receive)
        return self

    async def __aexit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        self._closed = True
        if self._remove is not None:
            self._remove()
        pending = set(self._active)
        try:
            if pending:
                waiting = asyncio.gather(*pending, return_exceptions=True)
                try:
                    await asyncio.shield(waiting)
                except asyncio.CancelledError:
                    await waiting
                    raise
        finally:
            await self.buffer.close()
