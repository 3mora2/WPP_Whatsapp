"""Legacy event helpers and loop-owned cancellable intervals."""

from __future__ import annotations

import asyncio
import inspect
from threading import Event
from typing import Any, Callable, Optional


class EventEmitter:
    """Compatibility emitter; session event dispatch lives in core.events."""

    def __init__(self) -> None:
        self._callbacks: dict[str, list[Callable[..., Any]]] = {}

    def on(self, event_name, function):
        self._callbacks.setdefault(event_name, []).append(function)
        return function

    def emit(self, event_name, *args, **kwargs):
        for function in self._callbacks.get(event_name, []):
            function(*args, **kwargs)

    def off(self, event_name, function):
        self._callbacks.get(event_name, []).remove(function)


class LoopInterval(Event):
    def __init__(self, loop: asyncio.AbstractEventLoop) -> None:
        super().__init__()
        self.loop = loop
        self.task: Optional[asyncio.Task] = None

    def set(self) -> None:
        super().set()
        try:
            current = asyncio.current_task()
        except RuntimeError:
            current = None
        if (
            self.task is not None
            and self.task is not current
            and not self.task.done()
            and not self.loop.is_closed()
        ):
            self.loop.call_soon_threadsafe(self.task.cancel)


def setInterval(loop, func, interval, *args, **kwargs):
    """Run immediately, then periodically until cancelled on the owning loop."""
    stopped = LoopInterval(loop)

    async def run():
        while not stopped.is_set():
            result = func(*args, **kwargs)
            if inspect.isawaitable(result):
                await result
            await asyncio.sleep(interval)

    def start():
        if not stopped.is_set():
            stopped.task = loop.create_task(run())

    # Create the coroutine only after the owner loop accepts the callback.
    loop.call_soon_threadsafe(start)
    return stopped
