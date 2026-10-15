from __future__ import annotations

import asyncio
import inspect
import threading
from collections import OrderedDict

from .errors import EventQueueFullError, SessionClosedError

CALLBACK_THREAD = threading.local()
EVENT_NAMES = (
    "onMessage",
    "onAnyMessage",
    "onMessageEdit",
    "onAck",
    "onNotificationMessage",
    "onParticipantsChanged",
    "onStateChange",
    "onStreamChange",
    "onStreamModeChanged",
    "onStreamInfoChanged",
    "onIncomingCall",
    "onInterfaceChange",
    "onPresenceChanged",
    "onLiveLocation",
    "onAddedToGroup",
    "onRevokedMessage",
    "onReactionMessage",
    "onPollResponse",
    "onBackendEvent",
    "onUpdateLabel",
    "onOrderStatusUpdate",
    "onNewChat",
)


class EventEmitter:
    def __init__(self):
        self._listeners = {}
        self._lock = threading.RLock()

    def on(self, event, callback):
        if not callable(callback):
            raise TypeError("Event callback must be callable")
        with self._lock:
            self._listeners.setdefault(event, []).append(callback)

    def listeners(self, event):
        with self._lock:
            return list(self._listeners.get(event, ()))

    def listener_count(self, event):
        return len(self.listeners(event))

    def remove_listener(self, event, callback):
        with self._lock:
            callbacks = self._listeners.get(event, [])
            if callback in callbacks:
                callbacks.remove(callback)

    def remove_all_listeners(self):
        with self._lock:
            self._listeners.clear()

    def emit(self, event, *args, **kwargs):
        for callback in self.listeners(event):
            result = callback(*args, **kwargs)
            if inspect.isawaitable(result):
                if inspect.iscoroutine(result):
                    result.close()
                raise RuntimeError("Async callbacks require the async dispatcher")

    async def emit_async(self, event, args, kwargs, on_error):
        for callback in self.listeners(event):
            try:
                if inspect.iscoroutinefunction(callback):
                    await callback(*args, **kwargs)
                else:
                    owner = asyncio.get_running_loop()

                    def invoke(callback=callback, owner=owner):
                        previous = getattr(CALLBACK_THREAD, "owner", None)
                        CALLBACK_THREAD.owner = owner
                        try:
                            return callback(*args, **kwargs)
                        finally:
                            CALLBACK_THREAD.owner = previous

                    result = await asyncio.to_thread(invoke)
                    if inspect.isawaitable(result):
                        await result
            except Exception as error:
                on_error(type(error).__name__)


class EventDispatcher:
    """Ordered session queue. Overflow is explicit; payloads are never logged."""

    def __init__(self, emitter, maxsize=256, on_error=None):
        if not isinstance(maxsize, int) or isinstance(maxsize, bool) or maxsize < 1:
            raise ValueError("eventQueueSize must be a positive integer")
        self.emitter = emitter
        self.queue: asyncio.Queue = asyncio.Queue(maxsize=maxsize)
        self.closed = False
        self.seen = OrderedDict()
        self.on_error = on_error or (lambda error_type: None)
        self.stats = {"delivered": 0, "rejected": 0, "duplicates": 0, "callback_errors": 0}
        self.worker = None

    def _error(self, error_type):
        self.stats["callback_errors"] += 1
        try:
            self.on_error(error_type)
        except Exception:
            pass

    async def submit(self, event, *args, **kwargs):
        if self.closed:
            raise SessionClosedError("Event dispatcher is closed")
        key = None
        if event in ("onMessage", "onAnyMessage") and args and isinstance(args[0], dict):
            message_id = args[0].get("id")
            if isinstance(message_id, str) and message_id:
                key = (event, message_id)
                if key in self.seen:
                    self.stats["duplicates"] += 1
                    return
        future = asyncio.get_running_loop().create_future()
        try:
            self.queue.put_nowait((event, args, kwargs, future))
        except asyncio.QueueFull:
            self.stats["rejected"] += 1
            raise EventQueueFullError("Session event queue is full") from None
        if key:
            self.seen[key] = None
            if len(self.seen) > 4096:
                self.seen.popitem(last=False)
        if self.worker is None or self.worker.done():
            self.worker = asyncio.create_task(self._run())
        await asyncio.shield(future)

    async def _run(self):
        while not self.queue.empty():
            event, args, kwargs, future = self.queue.get_nowait()
            try:
                await self.emitter.emit_async(event, args, kwargs, self._error)
                self.stats["delivered"] += 1
            finally:
                if not future.done():
                    future.set_result(None)
                self.queue.task_done()

    async def close(self, drain=False, timeout=10):
        self.closed = True
        worker = self.worker
        if worker is not None and worker is not asyncio.current_task():
            if drain:
                try:
                    await asyncio.wait_for(asyncio.shield(worker), timeout)
                except asyncio.TimeoutError:
                    worker.cancel()
            else:
                worker.cancel()
            try:
                await worker
            except asyncio.CancelledError:
                pass
        while not self.queue.empty():
            *_, future = self.queue.get_nowait()
            if not future.done():
                future.set_result(None)
            self.queue.task_done()
        self.seen.clear()
