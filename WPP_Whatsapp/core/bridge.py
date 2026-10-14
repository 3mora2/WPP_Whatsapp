from __future__ import annotations

import time

from playwright.async_api import Error as PlaywrightError

from .commands import COMMANDS
from .diagnostics import classify_failure
from .errors import BridgeError, RuntimeCompatibilityError


class JavascriptBridge:
    """Single command registry, session page binding, errors and safe metrics."""

    def __init__(self, transport, page):
        self.transport, self.page = transport, page
        self.metrics = {"calls": 0, "failures": 0, "duration_seconds": 0.0}
        self.last_failure = None
        self.command_metrics = {}

    async def call(self, command, arg=None):
        try:
            source = COMMANDS[command]
        except KeyError:
            raise BridgeError(command, dispatched=False) from None
        start = time.monotonic()
        self.metrics["calls"] += 1
        measured = self.command_metrics.setdefault(
            command,
            {
                "calls": 0,
                "failures": 0,
                "duration_seconds": 0.0,
                "max_seconds": 0.0,
            },
        )
        measured["calls"] += 1
        try:
            return await self.transport.page_evaluate(source, arg, page=self.page)
        except PlaywrightError as error:
            self.metrics["failures"] += 1
            measured["failures"] += 1
            self.last_failure = classify_failure("browser_operation", error)
            raise BridgeError(command) from None
        finally:
            elapsed = time.monotonic() - start
            self.metrics["duration_seconds"] += elapsed
            measured["duration_seconds"] += elapsed
            measured["max_seconds"] = max(measured["max_seconds"], elapsed)

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
