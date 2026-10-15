"""Bounded account-local event history with explicit cursor gaps."""

import asyncio
from collections import deque
from copy import deepcopy

from WPP_Whatsapp.core.event_store import SQLiteEventStore

MAX_BODY_CHARS = 65536


class EventBuffer:
    def __init__(self, capacity: int = 256, *, path=None, namespace="default", retention=86400):
        if type(capacity) is not int or capacity < 1:
            raise ValueError("Event capacity must be positive")
        self.items: deque = deque(maxlen=capacity)
        self._sequence = 0
        self.store = SQLiteEventStore(path, namespace, capacity, retention) if path else None

    @property
    def sequence(self):
        return self.store.sequence if self.store else self._sequence

    async def append(self, message):
        # Keep the stable event fields; never retain inline base64 or arbitrary
        # upstream objects in a long-lived buffer. Full IDs are preserved.
        payload = {
            key: value
            for key, value in message.items()
            if key in {"id", "body", "fromMe", "type", "timestamp", "t", "author", "from", "to"}
        }
        truncated = isinstance(payload.get("body"), str) and len(payload["body"]) > MAX_BODY_CHARS
        if truncated:
            payload["body"] = payload["body"][:MAX_BODY_CHARS]
        if self.store:
            write = asyncio.create_task(
                asyncio.to_thread(
                    self.store.append, {"message": deepcopy(payload), "truncated": truncated}
                )
            )
            try:
                await asyncio.shield(write)
            except asyncio.CancelledError:
                # Finish an accepted journal write before callback shutdown can
                # close its store. Cancellation cannot interrupt SQLite's thread.
                await write
                raise
            return
        self._sequence += 1
        self.items.append(
            {"sequence": self.sequence, "message": deepcopy(payload), "truncated": truncated}
        )

    def read(self, after: int = 0, limit: int = 50) -> dict:
        if type(limit) is not int or not 1 <= limit <= 200:
            raise ValueError("Event limit must be between 1 and 200")
        if self.store:
            return self.store.read(after, limit)
        if type(after) is not int or not 0 <= after <= self.sequence:
            raise ValueError("Invalid event cursor")
        if type(limit) is not int or not 1 <= limit <= 200:
            raise ValueError("Event limit must be between 1 and 200")
        first = self.items[0]["sequence"] if self.items else self.sequence + 1
        gap = max(0, first - after - 1)
        selected = [item for item in self.items if item["sequence"] > after][:limit]
        return {
            "events": deepcopy(selected),
            "lost": gap,
            "cursor": selected[-1]["sequence"] if selected else self.sequence,
        }

    async def close(self):
        if self.store:
            await asyncio.to_thread(self.store.close)
