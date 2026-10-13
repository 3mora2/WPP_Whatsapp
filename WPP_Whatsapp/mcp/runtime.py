"""Serialize MCP operations with session startup and shutdown on one event loop."""

from __future__ import annotations

import asyncio
from typing import Awaitable, Callable, TypeVar

from WPP_Whatsapp import AsyncClient
from WPP_Whatsapp.core.delivery import DeliveryTracker
from WPP_Whatsapp.core.errors import SessionNotReadyError
from WPP_Whatsapp.core.lifecycle import SessionState

from .models import SessionStatus

T = TypeVar("T")


class SessionRuntime:
    def __init__(self, client: AsyncClient, read_only: bool) -> None:
        self.client = client
        self.read_only = read_only
        self.lock = asyncio.Lock()
        self.tracker: DeliveryTracker | None = None

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
