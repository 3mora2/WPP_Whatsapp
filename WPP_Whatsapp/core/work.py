"""Per-session bounded admission and optional send pacing on the owner loop."""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager

from WPP_Whatsapp.utils.rate_limiter import RateLimiter

from .errors import OperationQueueFullError


class WorkController:
    def __init__(self, options):
        self.capacity = options.get("maxPendingOperations", 64)
        self.semaphore = asyncio.Semaphore(options.get("maxConcurrentOperations", 4))
        calls = options.get("sendRateCalls", 0)
        self.limiter = RateLimiter(calls, options.get("sendRatePeriod", 60)) if calls else None
        self.stats = {"active": 0, "waiting": 0, "rejected": 0, "completed": 0}

    async def pace_send(self):
        if self.limiter is not None:
            await self.limiter.acquire()

    @asynccontextmanager
    async def slot(self, *, send=False):
        if self.stats["waiting"] + self.stats["active"] >= self.capacity:
            self.stats["rejected"] += 1
            raise OperationQueueFullError("Session operation capacity exceeded")
        self.stats["waiting"] += 1
        acquired = False
        try:
            await self.semaphore.acquire()
            acquired = True
            self.stats["waiting"] -= 1
            self.stats["active"] += 1
            if send:
                await self.pace_send()
            yield
        finally:
            if acquired:
                self.stats["active"] -= 1
                self.stats["completed"] += 1
                self.semaphore.release()
            else:
                self.stats["waiting"] -= 1


def controller(context) -> WorkController:
    if getattr(context, "_work_controller", None) is None:
        context._work_controller = WorkController(context.options)
    return context._work_controller
