"""Client-owned subscriptions rebound to each replacement session context."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Optional, Union

from .events import EVENT_NAMES

if TYPE_CHECKING:
    from .journal import EventJournal
    from .services import EventsService


@dataclass(eq=False)
class _Subscription:
    name: str
    callback: Callable[..., Any]
    remove: Optional[Callable[[], None]] = None


class ClientEvents:
    def __init__(self, namespace: str = "default") -> None:
        self.namespace = namespace
        self._entries: list[_Subscription] = []
        self._source: Optional[EventsService] = None

    def bind(self, source: EventsService) -> None:
        self.detach()
        self._source = source
        for entry in self._entries:
            entry.remove = source.on(entry.name, entry.callback)

    def detach(self) -> None:
        for entry in self._entries:
            if entry.remove is not None:
                entry.remove()
                entry.remove = None
        self._source = None

    def on(self, name: str, callback: Callable[..., Any]) -> Callable[[], None]:
        if name not in EVENT_NAMES or not callable(callback):
            raise ValueError("Expected a supported event and callable listener")
        entry = _Subscription(name, callback)
        self._entries.append(entry)
        if self._source is not None:
            entry.remove = self._source.on(name, callback)

        def unsubscribe() -> None:
            if entry in self._entries:
                self._entries.remove(entry)
                if entry.remove is not None:
                    entry.remove()
                    entry.remove = None

        return unsubscribe

    def on_message(self, callback: Callable[..., Any]) -> Callable[[], None]:
        return self.on("onMessage", callback)

    def on_any_message(self, callback: Callable[..., Any]) -> Callable[[], None]:
        return self.on("onAnyMessage", callback)

    def journal(
        self,
        path: Union[str, Path],
        *,
        namespace: Optional[str] = None,
        capacity: int = 10000,
        retention: float = 86400,
    ) -> EventJournal:
        """Attach a private durable journal, explicitly opting into message storage."""
        from .journal import EventJournal

        return EventJournal(
            self,
            path,
            namespace=self.namespace if namespace is None else namespace,
            capacity=capacity,
            retention=retention,
        )

    @property
    def stats(self) -> dict[str, int]:
        return self._source.stats if self._source is not None else {}
