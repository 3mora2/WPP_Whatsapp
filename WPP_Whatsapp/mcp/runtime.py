"""Serialize MCP operations with session startup and shutdown on one event loop."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Awaitable, Callable, TypeVar

from WPP_Whatsapp import AsyncClient
from WPP_Whatsapp.core.delivery import DeliveryTracker
from WPP_Whatsapp.core.errors import SessionNotReadyError
from WPP_Whatsapp.core.lifecycle import SessionState

from .event_buffer import EventBuffer
from .models import SessionStatus

T = TypeVar("T")


class SessionRuntime:
    def __init__(self, client: AsyncClient, read_only: bool, media_root=None) -> None:
        self.client = client
        self.read_only = read_only
        self.lock = asyncio.Lock()
        self.tracker: DeliveryTracker | None = None
        self.media_root = Path(media_root).resolve() if media_root is not None else None
        self.events = EventBuffer()
        self._event_source = None
        self._unsubscribe = None

    def subscribe(self):
        source = self.client.events
        if source is not self._event_source:
            self.unsubscribe()
            self._unsubscribe = source.on_message(self.events.append)
            self._event_source = source

    def unsubscribe(self):
        if self._unsubscribe is not None:
            self._unsubscribe()
        self._unsubscribe = self._event_source = None

    def media_path(self, relative: str) -> Path:
        if self.media_root is None:
            raise ValueError("Media access is disabled for this account")
        value = Path(relative)
        if value.is_absolute() or not relative.strip():
            raise ValueError("Media paths must be relative to the configured root")
        path = (self.media_root / value).resolve(strict=True)
        if self.media_root not in path.parents or not path.is_file():
            raise ValueError("Media path is outside the configured root or is not a file")
        return path

    def status(self) -> SessionStatus:
        return {
            "session": self.client.session,
            "state": self.client.state,
            "ready": self.client.state == SessionState.READY,
            "read_only": self.read_only,
        }

    async def run(self, action: Callable[[], Awaitable[T]], *, ready: bool = True) -> T:
        async with self.lock:
            if ready and self.client.state != SessionState.READY:
                raise SessionNotReadyError("Connect and finish login in the browser first")
            return await action()
