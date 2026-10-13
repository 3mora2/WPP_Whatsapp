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
