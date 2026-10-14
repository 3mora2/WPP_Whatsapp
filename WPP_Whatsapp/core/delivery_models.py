"""Delivery metadata shared by tracking logic and persistence adapters."""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class DeliveryState(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    FAILED = "failed"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class DeliveryReceipt:
    operation_id: str
    state: DeliveryState
    message_id: Optional[str] = None


@dataclass(frozen=True)
class ExpectedMessage:
    """Minimal evidence reserved before dispatch; never stores the message body."""

    message_id: str
    chat_id: str
    type: str
