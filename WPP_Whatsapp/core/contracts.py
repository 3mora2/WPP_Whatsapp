"""Structural interfaces shared by services and the browser bridge.

Implementations do not need to inherit these protocols. This keeps browser
transports replaceable and allows unit tests to use small operation contexts.
"""

from __future__ import annotations

import asyncio
from typing import Any, Awaitable, Callable, Protocol, TypeVar, Union

from .lifecycle import SessionLifecycle

Result = TypeVar("Result")
Callback = Callable[..., Any]
Operation = Callable[..., Awaitable[Any]]


class BrowserTransport(Protocol):
    loop: asyncio.AbstractEventLoop

    async def create_task(self, task: Awaitable[Result]) -> Result: ...

    def run_threadsafe(
        self,
        task: Union[Awaitable[Result], Callable[..., Awaitable[Result]]],
        *args: Any,
        timeout_: float = 120,
        **kwargs: Any,
    ) -> Result: ...

    async def page_evaluate(self, expression: str, arg: Any = None, *, page: Any = None) -> Any: ...


class OperationContext(Protocol):
    session: str
    options: dict[str, Any]
    lifecycle: SessionLifecycle
    ThreadsafeBrowser: BrowserTransport

    def __getattr__(self, name: str) -> Any: ...
