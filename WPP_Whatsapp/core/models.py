"""Opt-in immutable views. Unknown upstream fields remain available through raw."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any, Mapping, Optional


def identifier(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, Mapping) and isinstance(value.get("_serialized"), str):
        return value["_serialized"]
    raise ValueError("Expected a complete serialized WhatsApp identifier")


@dataclass(frozen=True)
class Message:
    id: str
    body: Optional[str]
    from_me: Optional[bool]
    timestamp: Optional[float]
    type: Optional[str]
    _raw: dict = field(repr=False, compare=False)

    @classmethod
    def from_raw(cls, value: Mapping[str, Any]) -> Message:
        stamp = value.get("timestamp", value.get("t"))
        return cls(
            identifier(value.get("id")),
            value.get("body") if isinstance(value.get("body"), str) else None,
            value.get("fromMe") if isinstance(value.get("fromMe"), bool) else None,
            float(stamp)
            if isinstance(stamp, (int, float)) and not isinstance(stamp, bool)
            else None,
            value.get("type") if isinstance(value.get("type"), str) else None,
            deepcopy(dict(value)),
        )

    @property
    def raw(self) -> dict:
        return deepcopy(self._raw)


@dataclass(frozen=True)
class Chat:
    id: str
    name: Optional[str]
    is_group: bool
    _raw: dict = field(repr=False, compare=False)

    @classmethod
    def from_raw(cls, value: Mapping[str, Any]) -> Chat:
        key = identifier(value.get("id"))
        name = value.get("name", value.get("formattedTitle"))
        return cls(
            key,
            name if isinstance(name, str) else None,
            key.endswith("@g.us"),
            deepcopy(dict(value)),
        )

    @property
    def raw(self) -> dict:
        return deepcopy(self._raw)


@dataclass(frozen=True)
class GroupMember:
    id: str
    is_admin: Optional[bool]
    is_super_admin: Optional[bool]
    _raw: dict = field(repr=False, compare=False)

    @classmethod
    def from_raw(cls, value: Mapping[str, Any]) -> GroupMember:
        return cls(
            identifier(value.get("id")),
            value.get("isAdmin") if isinstance(value.get("isAdmin"), bool) else None,
            value.get("isSuperAdmin") if isinstance(value.get("isSuperAdmin"), bool) else None,
            deepcopy(dict(value)),
        )

    @property
    def raw(self) -> dict:
        return deepcopy(self._raw)


@dataclass(frozen=True)
class Group:
    id: str
    name: Optional[str]
    description: Optional[str]
    owner_id: Optional[str]
    participants: tuple[GroupMember, ...]
    _raw: dict = field(repr=False, compare=False)

    @classmethod
    def from_raw(cls, value: Mapping[str, Any]) -> Group:
        chat = Chat.from_raw(value)
        if not chat.is_group:
            raise ValueError("Expected a group chat")
        metadata = value.get("groupMetadata") or {}
        owner = metadata.get("owner")
        description = metadata.get("desc")
        return cls(
            chat.id,
            chat.name,
            description if isinstance(description, str) else None,
            identifier(owner) if owner else None,
            tuple(GroupMember.from_raw(item) for item in metadata.get("participants", [])),
            deepcopy(dict(value)),
        )

    @property
    def raw(self) -> dict:
        return deepcopy(self._raw)


class TypedServices:
    """Stable, explicit common reads over the complete raw service API."""

    def __init__(self, hub):
        self._hub = hub
        self.context = hub.context

    async def get_message(self, message_id: str) -> Optional[Message]:
        value = await self._hub.messages.get_message(message_id)
        return Message.from_raw(value) if value else None

    async def get_messages(self, chat_id: str, options: Optional[dict] = None) -> list[Message]:
        return [
            Message.from_raw(item)
            for item in await self._hub.messages.get_messages(chat_id, options)
        ]

    async def list_chats(self, options: Optional[dict] = None) -> list[Chat]:
        return [Chat.from_raw(item) for item in await self._hub.chats.list_chats(options)]

    async def get_group_members(self, group_id: str) -> list[GroupMember]:
        return [
            GroupMember.from_raw(item)
            for item in await self._hub.groups.get_group_members(group_id)
        ]

    async def get_group(self, group_id: str) -> Optional[Group]:
        value = await self._hub.chats.get_chat_by_id(group_id)
        return Group.from_raw(value) if value else None
