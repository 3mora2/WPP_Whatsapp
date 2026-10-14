"""Observe ACK evidence independently from send confirmation and operation retries."""

from __future__ import annotations

import asyncio
import math
from typing import Literal, Optional

from typing_extensions import TypedDict

from .errors import AcknowledgementTimeoutError, SessionClosedError

AckTarget = Literal["server", "delivered", "read", "played"]
LEVELS = {"server": 1, "delivered": 2, "read": 3, "played": 4}


class Acknowledgement(TypedDict):
    operation_id: str
    message_id: Optional[str]
    ack: Optional[int]
    delivered: bool
    read: bool
    played: bool


class AckObserver:
    def __init__(self, context):
        self.values: dict[str, int] = {}
        self.changed = asyncio.Condition()
        self.closed = False
        self.unsubscribe = context.onAck(self.observe)

    async def observe(self, event):
        if self.closed or not isinstance(event, dict):
            return
        ident, ack = event.get("id"), event.get("ack")
        if isinstance(ident, dict):
            ident = ident.get("_serialized")
        # PEER=5 is a separate protocol signal, not evidence of delivery/read.
        if not isinstance(ident, str) or type(ack) is not int or not -7 <= ack <= 4:
            return
        async with self.changed:
            previous = self.values.get(ident)
            self.values[ident] = (
                ack if previous is None or ack < 0 or previous < 0 else max(previous, ack)
            )
            # Bounded recent evidence; get_message refreshes an evicted/missed ACK.
            if len(self.values) > 1024:
                self.values.pop(next(iter(self.values)))
            self.changed.notify_all()

    async def close(self):
        self.unsubscribe()
        async with self.changed:
            self.closed = True
            self.changed.notify_all()


def validate_wait(target: AckTarget, timeout: float) -> int:
    if target not in LEVELS:
        raise ValueError("Unsupported acknowledgement target")
    if type(timeout) not in (float, int) or not math.isfinite(timeout) or timeout < 0:
        raise ValueError("ACK timeout must be finite and nonnegative")
    return LEVELS[target]


async def wait_for_ack(
    service, operation_id: str, target: AckTarget, timeout: float
) -> Acknowledgement:
    validate_wait(target, timeout)
    try:
        return await asyncio.wait_for(_wait(service, operation_id, target, timeout), timeout)
    except asyncio.TimeoutError:
        raise AcknowledgementTimeoutError("Requested acknowledgement was not observed") from None


async def _wait(service, operation_id, target, timeout):
    level = validate_wait(target, timeout)
    observer = service._ack_observer()
    deadline = asyncio.get_running_loop().time() + timeout
    while True:
        if observer.closed:
            raise SessionClosedError("Session closed while waiting for acknowledgement")
        result = await service.delivery_status(operation_id)
        if result["ack"] is not None and result["ack"] >= level:
            return result
        remaining = deadline - asyncio.get_running_loop().time()
        if remaining <= 0:
            raise AcknowledgementTimeoutError("Requested acknowledgement was not observed")
        async with observer.changed:
            try:
                await asyncio.wait_for(observer.changed.wait(), min(remaining, 1))
            except asyncio.TimeoutError:
                pass
