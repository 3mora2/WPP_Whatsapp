"""Conservative send tracking independent of the persistence backend."""

from __future__ import annotations

import asyncio
import math
import threading
import uuid
from typing import Any, Awaitable, Callable, Optional

from .delivery_models import DeliveryReceipt as DeliveryReceipt
from .delivery_models import DeliveryState as DeliveryState
from .delivery_store import DeliveryStore, MemoryDeliveryStore, SQLiteDeliveryStore
from .errors import BridgeError, DeliveryUncertainError, SessionClosedError


def message_id_from_result(result: Any) -> Optional[str]:
    """Accept only complete IDs returned by the send operation."""
    value = result.get("id") if isinstance(result, dict) else result
    if isinstance(value, dict):
        value = value.get("_serialized")
    return value if isinstance(value, str) and value else None


class DeliveryTracker:
    """Reserved IDs are never replayed, including after cancellation or restart.

    SQLite I/O during sends runs in a worker. get()/close() are synchronous
    inspection/compatibility methods; async clients should use aclose().
    """

    def __init__(
        self, path=None, namespace: str = "default", *, store: Optional[DeliveryStore] = None
    ) -> None:
        if path is not None and store is not None:
            raise ValueError("Specify either a delivery path or a store")
        self.namespace = namespace
        self.records: dict[str, DeliveryReceipt] = {}
        self._store = (
            store
            if store is not None
            else (
                SQLiteDeliveryStore(path, namespace) if path is not None else MemoryDeliveryStore()
            )
        )
        self._lock = threading.RLock()
        self._active: set[str] = set()
        self._closed = False

    def get(self, operation_id: str) -> Optional[DeliveryReceipt]:
        with self._lock:
            receipt = (
                self.records.get(operation_id) if self._closed else self._store.get(operation_id)
            )
            # Only this tracker knows which claims are still executing. Opening
            # another tracker must not overwrite an active owner's persisted state.
            if (
                receipt
                and receipt.state == DeliveryState.PENDING
                and operation_id not in self._active
            ):
                receipt = DeliveryReceipt(operation_id, DeliveryState.UNKNOWN)
            if receipt:
                self.records[operation_id] = receipt
            return receipt

    async def _io(self, call: Callable[..., Any], *args: Any) -> Any:
        return await asyncio.to_thread(call, *args) if self._store.blocking else call(*args)

    def _claim(
        self, ident: str, request_fingerprint: Optional[str] = None
    ) -> Optional[DeliveryReceipt]:
        with self._lock:
            if self._closed:
                raise SessionClosedError("Delivery tracker is closed")
            pending = DeliveryReceipt(ident, DeliveryState.PENDING)
            previous = (
                self._store.claim_request(pending, request_fingerprint)
                if request_fingerprint is not None
                else self._store.claim(pending)
            )
            if previous is None:
                self._active.add(ident)
                self.records[ident] = pending
            return previous

    def _record(self, receipt: DeliveryReceipt) -> DeliveryReceipt:
        with self._lock:
            if self._closed:
                return self.records.get(
                    receipt.operation_id,
                    DeliveryReceipt(receipt.operation_id, DeliveryState.UNKNOWN),
                )
            try:
                self._store.save(receipt)
            except Exception:
                self.records[receipt.operation_id] = DeliveryReceipt(
                    receipt.operation_id, DeliveryState.UNKNOWN
                )
                raise DeliveryUncertainError(receipt.operation_id) from None
            self.records[receipt.operation_id] = receipt
            return receipt

    async def _save(
        self, ident: str, state: DeliveryState, message_id: Optional[str] = None
    ) -> DeliveryReceipt:
        if not self._store.blocking:
            return self._record(DeliveryReceipt(ident, state, message_id))
        # Cancellation cannot interrupt a durable commit after dispatch.
        return await asyncio.shield(
            self._io(self._record, DeliveryReceipt(ident, state, message_id))
        )

    async def _reserve(
        self, ident: str, request_fingerprint: Optional[str] = None
    ) -> Optional[DeliveryReceipt]:
        if not self._store.blocking:
            return self._claim(ident, request_fingerprint)
        claim = asyncio.create_task(self._io(self._claim, ident, request_fingerprint))
        try:
            return await asyncio.shield(claim)
        except asyncio.CancelledError:
            previous = await claim
            if previous is None:
                await self._save(ident, DeliveryState.FAILED)  # Dispatch has not started.
                with self._lock:
                    self._active.discard(ident)
            raise

    async def send(
        self,
        call: Callable[[], Awaitable[Any]],
        operation_id: Optional[str] = None,
        timeout: Optional[float] = None,
        *,
        request_fingerprint: Optional[str] = None,
    ) -> DeliveryReceipt:
        if timeout is not None and (
            not isinstance(timeout, (int, float)) or not math.isfinite(timeout) or timeout < 0
        ):
            raise ValueError("timeout must be finite and nonnegative")
        ident = uuid.uuid4().hex if operation_id is None else operation_id
        if not isinstance(ident, str) or not ident or len(ident) > 128:
            raise ValueError("operation_id must be a nonempty string of at most 128 characters")
        previous = await self._reserve(ident, request_fingerprint)
        if previous is not None:
            if previous.state == DeliveryState.CONFIRMED:
                return previous
            raise DeliveryUncertainError(ident)
        if self._closed:
            raise SessionClosedError("Delivery tracker is closed")

        async def invoke() -> Any:
            return await call()

        execution = asyncio.create_task(invoke())
        execution.add_done_callback(lambda task: self._completed(ident, task))
        try:
            result = (
                await asyncio.wait_for(asyncio.shield(execution), timeout)
                if timeout
                else await asyncio.shield(execution)
            )
        except asyncio.CancelledError:
            await self._save(ident, DeliveryState.UNKNOWN)
            execution.add_done_callback(lambda task: self._late_completed(ident, task))
            raise
        except (asyncio.TimeoutError, TimeoutError, BridgeError, SessionClosedError) as error:
            state = (
                DeliveryState.FAILED
                if isinstance(error, BridgeError) and not error.dispatched
                else DeliveryState.UNKNOWN
            )
            await self._save(ident, state)
            if state == DeliveryState.UNKNOWN:
                execution.add_done_callback(lambda task: self._late_completed(ident, task))
                raise DeliveryUncertainError(ident) from None
            raise
        except Exception:
            await self._save(ident, DeliveryState.FAILED)
            raise
        message_id = message_id_from_result(result)
        if message_id is None:
            await self._save(ident, DeliveryState.UNKNOWN)
            raise DeliveryUncertainError(ident)
        receipt = await self._save(ident, DeliveryState.CONFIRMED, message_id)
        if receipt.state != DeliveryState.CONFIRMED:
            raise DeliveryUncertainError(ident)
        return receipt

    def _completed(self, ident: str, task: asyncio.Task) -> None:
        with self._lock:
            self._active.discard(ident)
        if not task.cancelled():
            task.exception()

    def _late_completed(self, ident: str, task: asyncio.Task) -> None:
        if task.cancelled():
            return
        try:
            message_id = message_id_from_result(task.result())
        except BaseException:
            return  # Consume failures even if the original caller timed out.
        if message_id is not None and not self._closed:
            update = asyncio.create_task(self._confirm_late(ident, message_id))
            update.add_done_callback(lambda done: None if done.cancelled() else done.exception())

    async def _confirm_late(self, ident: str, message_id: str) -> None:
        previous = await self._io(self.get, ident)
        if previous and previous.state == DeliveryState.UNKNOWN:
            await self._save(ident, DeliveryState.CONFIRMED, message_id)

    def reconcile(self, operation_id: str, message_id: str) -> DeliveryReceipt:
        with self._lock:
            if self._closed:
                raise SessionClosedError("Delivery tracker is closed")
            previous = self.get(operation_id)
            if previous is None or previous.state not in (
                DeliveryState.UNKNOWN,
                DeliveryState.PENDING,
            ):
                raise ValueError("Only a pending or unknown operation can be reconciled")
            if not isinstance(message_id, str) or not message_id:
                raise ValueError("A verified message ID is required")
            return self._record(DeliveryReceipt(operation_id, DeliveryState.CONFIRMED, message_id))

    def close(self) -> None:
        with self._lock:
            if self._closed:
                return
            try:
                for ident in self._active:
                    self._record(DeliveryReceipt(ident, DeliveryState.UNKNOWN))
            finally:
                self._closed = True
                self._store.close()

    async def aclose(self) -> None:
        await self._io(self.close)

    async def get_async(self, operation_id: str) -> Optional[DeliveryReceipt]:
        """Inspect persisted metadata without blocking an async owner's loop."""
        return await self._io(self.get, operation_id)

    async def reconcile_async(self, operation_id: str, message_id: str) -> DeliveryReceipt:
        return await self._io(self.reconcile, operation_id, message_id)
