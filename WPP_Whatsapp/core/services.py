"""Composed services over one session context, with cached typed dispatch."""

from __future__ import annotations

import inspect
from functools import wraps
from typing import Any, Callable, Optional, Sequence

from .contracts import Callback, Operation, OperationContext
from .delivery import DeliveryReceipt, DeliveryTracker
from .events import EVENT_NAMES
from .service_registry import ServiceDefinition, service_definitions
from .service_registry import snake as snake

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
            return await self.deliveries.send(
                lambda: self._execute(operation, *args, **kwargs),
                operation_id,
                timeout=timeout
                if timeout is not None
                else self.context.options.get("operationTimeout", 60),
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

    @property
    def names(self) -> tuple[str, ...]:
        return tuple(self._services)


class SyncServices:
    def __init__(self, hub: ServiceHub) -> None:
        self.hub = hub
        self._services: dict[str, Any] = {}

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
