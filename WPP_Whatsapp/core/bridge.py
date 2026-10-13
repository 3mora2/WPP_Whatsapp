from __future__ import annotations

import time

from playwright.async_api import Error as PlaywrightError

from .commands import COMMANDS
from .errors import BridgeError, RuntimeCompatibilityError


class JavascriptBridge:
    """Single command registry, session page binding, errors and safe metrics."""

    def __init__(self, transport, page):
        self.transport, self.page = transport, page
        self.metrics = {"calls": 0, "failures": 0, "duration_seconds": 0.0}

    async def call(self, command, arg=None):
        try:
            source = COMMANDS[command]
        except KeyError:
            raise BridgeError(command, dispatched=False) from None
        start = time.monotonic()
        self.metrics["calls"] += 1
        try:
            return await self.transport.page_evaluate(source, arg, page=self.page)
        except PlaywrightError:
            self.metrics["failures"] += 1
            raise BridgeError(command) from None
        finally:
            self.metrics["duration_seconds"] += time.monotonic() - start

    def call_sync(self, command, arg=None, timeout_=120):
        return self.transport.run_threadsafe(self.call(command, arg), timeout_=timeout_)

    async def capabilities(self):
        result = await self.transport.page_evaluate(
            """() => ({
          version: window.WPP?.version,
          ready: Boolean(window.WPP?.isReady),
          history: typeof window.WPP?.chat?.getMessages === 'function',
          events: typeof window.WPP?.on === 'function',
          auth: typeof window.WPP?.conn?.isRegistered === 'function'
        })""",
            page=self.page,
        )
        if not result or not all(result.get(key) for key in ("ready", "history", "events", "auth")):
            raise RuntimeCompatibilityError("WA-JS is missing required runtime capabilities")
        return result
