"""Bounded opt-in recovery. It only reopens a session, never replays operations."""

from __future__ import annotations

import asyncio

from .diagnostics import classify_failure
from .errors import ProfileInUseError, RuntimeCompatibilityError
from .lifecycle import SessionState


class RecoverySupervisor:
    def __init__(self, client):
        self.client = client
        self.task = None
        self.blocked = False
        self.stats = {"attempts": 0, "successes": 0, "exhausted": 0}

    def schedule(self):
        if self.blocked or not self.client.options.get("reconnectAttempts", 0):
            return
        if self.task is None or self.task.done():
            self.task = asyncio.create_task(self._run())

    async def _run(self):
        options = self.client.options
        delay = options.get("reconnectInitialDelay", 1)
        ceiling = options.get("reconnectMaxDelay", 30)
        for _ in range(options["reconnectAttempts"]):
            await asyncio.sleep(min(delay, ceiling))
            if self.blocked:
                return
            if self.client.state == SessionState.READY:
                return  # The existing transport recovered before reopening was needed.
            self.stats["attempts"] += 1
            try:
                await asyncio.wait_for(
                    self.client._recover_once(), options.get("reconnectAttemptTimeout", 30)
                )
                self.stats["successes"] += 1
                return
            except (ProfileInUseError, RuntimeCompatibilityError) as error:
                self.client._failure = classify_failure("recovery", error)
                self.blocked = True
                return
            except Exception as error:
                self.client._failure = classify_failure("recovery", error)
            delay = min(ceiling, max(delay * 2, 0.01))
        self.stats["exhausted"] += 1
        self.blocked = True

    async def stop(self):
        task = self.task
        self.task = None
        if task is not None and task is not asyncio.current_task() and not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
