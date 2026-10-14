"""Composed services over one session context, with cached typed dispatch."""

from __future__ import annotations

import asyncio
import inspect
from contextlib import AsyncExitStack
from functools import wraps
from typing import Any, Callable, Optional, Sequence

from .acknowledgements import Acknowledgement, AckObserver, AckTarget, wait_for_ack
from .contracts import Callback, Operation, OperationContext
from .delivery import DeliveryReceipt, DeliveryTracker
from .events import EVENT_NAMES
from .media import DEFAULT_MAX_BYTES, Progress, download_to, prepare_media, send_prepared
from .models import TypedServices
from .requests import fingerprint
from .service_registry import ServiceDefinition, service_definitions
from .service_registry import snake as snake
from .work import controller

UNTRACKED_SENDS = frozenset({"send_seen", "send_reaction_to_message"})


class Service:
    def __init__(
        self,
        context: OperationContext,
        layers: Sequence[type] = (),
        *,
        definition: Optional[ServiceDefinition] = None,
    ) -> None:
        self.context = context
        definition = definition or ServiceDefinition(type(self).__name__, tuple(layers))
        self._definitions = definition.operations()
        self.operations = {name: function.__name__ for name, function in self._definitions.items()}
        self._bound_operations: dict[str, Operation] = {}

    def __dir__(self) -> list[str]:
        return sorted(set(super().__dir__()) | self.operations.keys())

    async def _execute(self, operation: str, *args: Any, **kwargs: Any) -> Any:
        async def on_owner() -> Any:
            self.context.lifecycle.require_ready()
            async with controller(self.context).slot(send=operation.startswith(("send", "reply"))):
                self.context.lifecycle.require_ready()
                return await getattr(self.context, operation)(*args, **kwargs)

        return await self.context.ThreadsafeBrowser.create_task(on_owner())

    def _bind(self, name: str, operation: str) -> Operation:
        async def execute(*args: Any, **kwargs: Any) -> Any:
            return await self._execute(operation, *args, **kwargs)

        return execute

    def __getattr__(self, name: str) -> Operation:
        if name in self._bound_operations:
            return self._bound_operations[name]
        if name not in self.operations:
            raise AttributeError(name)
        source = self._definitions[name]
        bound = wraps(source)(self._bind(name, self.operations[name]))
        signature = inspect.signature(source)
        parameters = list(signature.parameters.values())[1:]  # Bound context replaces self.
        if isinstance(self, MessagesService) and self._tracked(name):
            extra = [
                inspect.Parameter(key, inspect.Parameter.KEYWORD_ONLY, default=None)
                for key in ("operation_id", "timeout")
                if key not in signature.parameters
            ]
            position = next(
                (
                    index
                    for index, parameter in enumerate(parameters)
                    if parameter.kind == inspect.Parameter.VAR_KEYWORD
                ),
                len(parameters),
            )
            parameters[position:position] = extra
        bound.__name__ = name
        bound.__signature__ = signature.replace(parameters=parameters)
        self._bound_operations[name] = bound
        return bound


class MessagesService(Service):
    def _ack_observer(self) -> AckObserver:
        observer = getattr(self.context, "_ack_observer", None)
        if observer is None:
            observer = self.context._ack_observer = AckObserver(self.context)
        return observer

    async def delivery_status(self, operation_id: str) -> Acknowledgement:
        async def status():
            self.context.lifecycle.require_ready()
            observer = self._ack_observer()
            receipt = await self.deliveries.get_async(operation_id)
            if receipt is None:
                raise ValueError("Unknown delivery operation")
            ident = receipt.message_id
            if ident is not None:
                message = await self.get_message(ident)
                if message and message.get("id") == ident and message.get("fromMe"):
                    await observer.observe({"id": ident, "ack": message.get("ack")})
            ack = observer.values.get(ident)
            return {
                "operation_id": operation_id,
                "message_id": ident,
                "ack": ack,
                "delivered": ack is not None and ack >= 2,
                "read": ack is not None and ack >= 3,
                "played": ack is not None and ack >= 4,
            }

        return await self.context.ThreadsafeBrowser.create_task(status())

    async def wait_for_delivery(
        self, operation_id: str, *, target: AckTarget = "delivered", timeout: float = 30
    ) -> Acknowledgement:
        return await self.context.ThreadsafeBrowser.create_task(
            wait_for_ack(self, operation_id, target, timeout)
        )

    @staticmethod
    def _tracked(name: str) -> bool:
        return (name.startswith("send_") and name not in UNTRACKED_SENDS) or name == "reply"

    def _bind(self, name: str, operation: str) -> Operation:
        if not self._tracked(name):
            return super()._bind(name, operation)

        async def tracked(
            *args: Any,
            operation_id: Optional[str] = None,
            timeout: Optional[float] = None,
            **kwargs: Any,
        ) -> DeliveryReceipt:
            return await self._send(operation, args, kwargs, operation_id, timeout)

        return tracked

    @property
    def deliveries(self) -> DeliveryTracker:
        tracker = getattr(self.context, "_delivery_tracker", None)
        if tracker is None:
            tracker = DeliveryTracker(
                self.context.options.get("deliveryStore"), self.context.session
            )
            self.context._delivery_tracker = tracker
        return tracker

    async def _send(
        self,
        operation: str,
        args: tuple,
        kwargs: dict,
        operation_id: Optional[str],
        timeout: Optional[float],
    ) -> DeliveryReceipt:
        async def send() -> DeliveryReceipt:
            self.context.lifecycle.require_ready()
            # Bind defaults so positional/keyword spelling identifies the same request.
            method = getattr(self.context, operation)
            try:
                signature = inspect.signature(method)
            except (TypeError, ValueError):
                # Callable adapters may not expose a valid inspect signature.
                # Use the authoritative legacy declaration, never repr(arguments).
                source = next(
                    value for value in self._definitions.values() if value.__name__ == operation
                )
                signature = inspect.signature(source)
                signature = signature.replace(parameters=list(signature.parameters.values())[1:])
            arguments = signature.bind(*args, **kwargs)
            arguments.apply_defaults()
            request = fingerprint(operation, arguments.arguments)
            return await self.deliveries.send(
                lambda: self._execute(operation, *args, **kwargs),
                operation_id,
                timeout=timeout
                if timeout is not None
                else self.context.options.get("operationTimeout", 60),
                request_fingerprint=request,
            )

        return await self.context.ThreadsafeBrowser.create_task(send())

    async def send_text(
        self,
        to: str,
        content: str,
        options: Optional[dict] = None,
        *,
        operation_id: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> DeliveryReceipt:
        return await self._send(
            "sendText_", (to, content, options or {}), {}, operation_id, timeout
        )

    async def get_message(self, message_id: str) -> dict:
        return await self.get_message_by_id(message_id)

    async def send_media(
        self,
        to: str,
        source: str,
        *,
        kind: str = "document",
        caption: str = "",
        quoted_message_id: Optional[str] = None,
        operation_id: Optional[str] = None,
        timeout: Optional[float] = None,
        max_bytes: int = DEFAULT_MAX_BYTES,
        progress: Optional[Progress] = None,
    ) -> DeliveryReceipt:
        """Tracked, bounded file send. Timeout never triggers an automatic resend.

        An immutable bounded copy identifies the request. Once adopted by the
        reserved send it stays alive until dispatch finishes, even after timeout.
        """
        if kind not in {"document", "image", "video", "audio"}:
            raise ValueError("Unsupported media kind")

        async def on_owner():
            self.context.lifecycle.require_ready()
            stack = AsyncExitStack()
            adopted = False
            work = controller(self.context)
            try:
                await stack.enter_async_context(work.slot())
                media = await stack.enter_async_context(prepare_media(source, max_bytes=max_bytes))
                request = fingerprint(
                    "media",
                    {
                        "to": to,
                        "kind": kind,
                        "caption": caption,
                        "quoted": quoted_message_id,
                        "sha256": media.sha256,
                        "filename": media.filename,
                        "mimetype": media.mimetype,
                    },
                )

                async def dispatch():
                    nonlocal adopted
                    adopted = True
                    try:
                        await work.pace_send()
                        self.context.lifecycle.require_ready()
                        return await send_prepared(
                            self.context,
                            to,
                            media,
                            kind=kind,
                            caption=caption,
                            quoted_message_id=quoted_message_id,
                            progress=progress,
                        )
                    finally:
                        await stack.aclose()

                return await self.deliveries.send(
                    dispatch,
                    operation_id,
                    timeout=timeout if timeout is not None else 120,
                    request_fingerprint=request,
                )
            finally:
                # A shielded task may be scheduled when its caller is cancelled.
                await asyncio.sleep(0)
                if not adopted:
                    await stack.aclose()

        return await self.context.ThreadsafeBrowser.create_task(on_owner())

    async def search(
        self,
        chat_id: str,
        query: str,
        *,
        count: int = 100,
        before_message_id: Optional[str] = None,
    ) -> dict:
        """Search one bounded history page locally, returning the next scan cursor."""
        if not isinstance(query, str) or not query.strip():
            raise ValueError("Search query must not be blank")
        if type(count) is not int or not 1 <= count <= 200:
            raise ValueError("Search count must be between 1 and 200")
        options = {"count": count}
        if before_message_id is not None:
            options.update(id=before_message_id, direction="before")
        messages = await self.get_messages(chat_id, options)
        needle = query.casefold()
        # WA-JS can append lastReceivedKey after its history query; ordering is
        # not a reliable cursor contract. Pick the oldest timestamp when present.
        dated = [(item.get("timestamp", item.get("t")), item) for item in messages]
        dated = [(stamp, item) for stamp, item in dated if type(stamp) in (int, float)]
        oldest = (
            min(dated, key=lambda pair: pair[0])[1] if dated else (messages[0] if messages else {})
        )
        return {
            "messages": [
                item for item in messages if needle in str(item.get("body") or "").casefold()
            ],
            "scanned": len(messages),
            "before_message_id": oldest.get("id"),
        }

    async def download_media_to(
        self,
        message_id: str,
        destination: str,
        *,
        max_bytes: int = DEFAULT_MAX_BYTES,
        progress: Optional[Progress] = None,
    ) -> dict:
        async def on_owner():
            self.context.lifecycle.require_ready()
            async with controller(self.context).slot():
                self.context.lifecycle.require_ready()
                return await download_to(
                    self.context, message_id, destination, max_bytes=max_bytes, progress=progress
                )

        return await self.context.ThreadsafeBrowser.create_task(on_owner())

    async def reconcile(self, operation_id: str, message_id: str) -> DeliveryReceipt:
        async def record() -> DeliveryReceipt:
            message = await self.get_message(message_id)
            if not message or message.get("id") != message_id or not message.get("fromMe"):
                raise ValueError("Reconciliation requires a verified outgoing message")
            return await self.deliveries.reconcile_async(operation_id, message_id)

        return await self.context.ThreadsafeBrowser.create_task(record())


class EventsService:
    def __init__(self, context: OperationContext) -> None:
        self.context = context

    def on_message(self, callback: Callback) -> Callable[[], None]:
        return self.context.onMessage(callback)

    def on_any_message(self, callback: Callback) -> Callable[[], None]:
        return self.context.onAnyMessage(callback)

    def on(self, name: str, callback: Callback) -> Callable[[], None]:
        if name not in EVENT_NAMES:
            raise ValueError("Unknown event")
        return getattr(self.context, name)(callback)

    @property
    def stats(self) -> dict[str, int]:
        dispatcher = getattr(self.context, "_dispatcher", None)
        return dict(dispatcher.stats) if dispatcher else {}


class ServiceHub:
    def __init__(self, context: OperationContext) -> None:
        self.context = context
        self._services: dict[str, Any] = {"events": EventsService(context)}
        for definition in service_definitions():
            service_type = MessagesService if definition.name == "messages" else Service
            service = service_type(context, definition=definition)
            self._services[definition.name] = service
            setattr(self, definition.name, service)
        self.events = self._services["events"]
        self.typed = TypedServices(self)

    @property
    def names(self) -> tuple[str, ...]:
        return tuple(self._services)


class SyncServices:
    def __init__(self, hub: ServiceHub) -> None:
        self.hub = hub
        self._services: dict[str, Any] = {}

    @property
    def typed(self):
        if "typed" not in self._services:
            self._services["typed"] = SyncService(self.hub.typed)
        return self._services["typed"]

    def __dir__(self) -> list[str]:
        return sorted(set(super().__dir__()) | set(self.hub.names))

    def __getattr__(self, name: str) -> Any:
        if name not in self.hub.names:
            raise AttributeError(name)
        if name not in self._services:
            service = getattr(self.hub, name)
            self._services[name] = (
                service if isinstance(service, EventsService) else SyncService(service)
            )
        return self._services[name]


class SyncService:
    def __init__(self, service: Service) -> None:
        self.service = service
        self._operations: dict[str, Callable[..., Any]] = {}

    def __dir__(self) -> list[str]:
        return dir(self.service)

    def __getattr__(self, name: str) -> Any:
        method = getattr(self.service, name)
        if not callable(method):
            return method
        if name not in self._operations:

            @wraps(method)
            def execute(*args: Any, **kwargs: Any) -> Any:
                return self.service.context.ThreadsafeBrowser.run_threadsafe(
                    method(*args, **kwargs), timeout_=None
                )

            self._operations[name] = execute
        return self._operations[name]
