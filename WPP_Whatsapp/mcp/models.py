"""Stable structured outputs advertised in MCP tool schemas."""

from typing import Optional

from typing_extensions import TypedDict

from WPP_Whatsapp.core.delivery_models import DeliveryState
from WPP_Whatsapp.core.lifecycle import SessionState


class SessionStatus(TypedDict):
    session: str
    state: SessionState
    ready: bool
    read_only: bool


class DeliveryResult(TypedDict):
    operation_id: str
    state: DeliveryState
    message_id: Optional[str]


class DeliveryLookup(TypedDict):
    receipt: Optional[DeliveryResult]
