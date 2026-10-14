"""Fault boundaries for request identity, recovery, durable events and ACK evidence."""

import asyncio
import sqlite3
import subprocess
import sys
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import pytest

from tests.helpers import eventually, ready_context
from WPP_Whatsapp import AsyncClient
from WPP_Whatsapp.core.acknowledgements import AckObserver
from WPP_Whatsapp.core.delivery import DeliveryState, DeliveryTracker
from WPP_Whatsapp.core.delivery_store import SQLiteDeliveryStore
from WPP_Whatsapp.core.errors import (
    AcknowledgementTimeoutError,
    DeliveryUncertainError,
    OperationConflictError,
    OperationQueueFullError,
    RuntimeCompatibilityError,
)
from WPP_Whatsapp.core.event_store import SQLiteEventStore
from WPP_Whatsapp.core.lifecycle import SessionState
from WPP_Whatsapp.core.requests import fingerprint
from WPP_Whatsapp.core.services import ServiceHub
from WPP_Whatsapp.core.subscriptions import ClientEvents
from WPP_Whatsapp.core.work import WorkController


@pytest.mark.asyncio
@pytest.mark.parametrize("durable", [False, True])
async def test_request_identity_rejects_changes_before_dispatch(tmp_path, durable):
    path = tmp_path / "deliveries.db" if durable else None
    tracker = DeliveryTracker(path)
    call = AsyncMock(return_value={"id": "outgoing"})
    request = fingerprint("text", {"to": "first", "body": "private text"})
    receipt = await tracker.send(call, "one", request_fingerprint=request)
    assert await tracker.send(call, "one", request_fingerprint=request) == receipt
    for changed in ({"to": "second", "body": "private text"}, {"to": "first", "body": "other"}):
        with pytest.raises(OperationConflictError):
            await tracker.send(call, "one", request_fingerprint=fingerprint("text", changed))
    call.assert_awaited_once()
    await tracker.aclose()
    if durable:
        assert b"private text" not in path.read_bytes()
        reopened = DeliveryTracker(path)
        assert await reopened.send(call, "one", request_fingerprint=request) == receipt
        await reopened.aclose()


@pytest.mark.asyncio
async def test_legacy_schema_migrates_without_verifying_old_request(tmp_path):
    path = tmp_path / "old.db"
    with sqlite3.connect(path) as db:
        db.execute(SQLiteDeliveryStore.SCHEMA)
        db.execute("INSERT INTO deliveries VALUES ('default','old','confirmed','id',1)")
    tracker = DeliveryTracker(path)
    assert tracker.get("old").state == DeliveryState.CONFIRMED
    call = AsyncMock()
    with pytest.raises(OperationConflictError):
        await tracker.send(call, "old", request_fingerprint="new")
    call.assert_not_called()
    await tracker.aclose()


@pytest.mark.asyncio
async def test_two_trackers_claim_same_request_once(tmp_path):
    path = tmp_path / "shared.db"
    first, second = DeliveryTracker(path), DeliveryTracker(path)
    entered, release = asyncio.Event(), asyncio.Event()

    async def dispatch():
        entered.set()
        await release.wait()
        return {"id": "out"}

    pending = asyncio.create_task(first.send(dispatch, "same", request_fingerprint="A"))
    await entered.wait()
    try:
        with pytest.raises(DeliveryUncertainError):
            await second.send(AsyncMock(), "same", request_fingerprint="A")
        with pytest.raises(OperationConflictError):
            await second.send(AsyncMock(), "same", request_fingerprint="B")
    finally:
        release.set()
        await pending
        await first.aclose()
        await second.aclose()


@pytest.mark.asyncio
async def test_actual_process_crash_never_replays_claim(tmp_path):
    path = tmp_path / "crash.db"
    script = """
import os, sys
from WPP_Whatsapp.core.delivery_store import SQLiteDeliveryStore
from WPP_Whatsapp.core.delivery_models import DeliveryReceipt, DeliveryState
store=SQLiteDeliveryStore(sys.argv[1])
store.claim_request(DeliveryReceipt('crashed',DeliveryState.PENDING), 'request')
os._exit(17)
"""
    result = subprocess.run(
        [sys.executable, "-c", script, str(path)], capture_output=True, timeout=30
    )
    assert result.returncode == 17, result.stderr.decode()
    tracker = DeliveryTracker(path)
    assert tracker.get("crashed").state == DeliveryState.UNKNOWN
    call = AsyncMock()
    with pytest.raises(DeliveryUncertainError):
        await tracker.send(call, "crashed", request_fingerprint="request")
    call.assert_not_called()
    await tracker.aclose()


def test_event_store_is_lazy_deduplicated_namespaced_and_resumable(tmp_path):
    path = tmp_path / "private/events.db"
    first = SQLiteEventStore(path, "first", 2, 3600)
    assert not path.exists()

    def event(ident):
        return {"message": {"id": ident, "body": "test"}, "truncated": False}

    first.append(event("full_group_id_participant"))
    first.append(event("full_group_id_participant"))
    assert first.sequence == 1
    cursor = first.read(0, 10)["cursor"]
    first.close()
    reopened = SQLiteEventStore(path, "first", 2, 3600)
    reopened.append(event("second"))
    assert reopened.read(cursor, 10)["events"][0]["message"]["id"] == "second"
    reopened.append(event("third"))
    assert reopened.read(0, 10)["lost"] == 1
    other = SQLiteEventStore(path, "other", 2, 3600)
    assert other.read(0, 10)["events"] == []
    other.close()
    reopened.close()


def test_retention_keeps_sequence_and_reports_pruned_gap(tmp_path):
    path = tmp_path / "events.db"
    store = SQLiteEventStore(path, "account", 5, 3600)
    store.append({"message": {"id": "old"}})
    with sqlite3.connect(path) as db:
        db.execute("UPDATE events SET created=0")
    assert store.read(0, 10) == {"events": [], "lost": 1, "cursor": 1}
    store.close()
    reopened = SQLiteEventStore(path, "account", 5, 3600)
    reopened.append({"message": {"id": "new"}})
    assert reopened.sequence == 2
    reopened.close()


@pytest.mark.asyncio
async def test_service_normalizes_request_defaults():
    calls = []

    async def send(to, content, options=None):
        calls.append((to, content, options))
        return {"id": "result"}

    context = ready_context(sendText_=send)
    messages = ServiceHub(context).messages
    first = await messages.send_text("chat", "text", operation_id="same")
    assert (
        await messages.send_text(to="chat", content="text", options={}, operation_id="same")
        == first
    )
    with pytest.raises(OperationConflictError):
        await messages.send_text("other", "text", operation_id="same")
    assert len(calls) == 1
    await messages.deliveries.aclose()


@pytest.mark.asyncio
async def test_client_subscriptions_rebind_without_duplicates():
    listeners = [[], []]

    def source(index):
        def on(name, callback):
            listeners[index].append((name, callback))
            return lambda: listeners[index].remove((name, callback))

        return SimpleNamespace(on=on, stats={})

    events = ClientEvents()
    remove = events.on_message(AsyncMock())
    events.bind(source(0))
    events.bind(source(1))
    assert not listeners[0] and len(listeners[1]) == 1
    remove()
    remove()
    assert not listeners[1]


@pytest.mark.asyncio
async def test_recovery_is_bounded_and_never_calls_sends():
    client = AsyncClient(reconnectAttempts=3, reconnectInitialDelay=0, reconnectMaxDelay=0)
    client._recover_once = AsyncMock(side_effect=OSError("network"))
    client._recovery.schedule()
    task = client._recovery.task
    client._recovery.schedule()
    assert client._recovery.task is task
    await task
    assert client._recover_once.await_count == 3
    assert client.diagnostics()["recovery"]["exhausted"] == 1
    client._recovery.schedule()
    assert client._recovery.task is task  # Repeated outage events cannot reset the budget.
    await client.close()


@pytest.mark.asyncio
async def test_recovery_stops_on_incompatibility_and_close_cancels_wait():
    client = AsyncClient(reconnectAttempts=3, reconnectInitialDelay=0)
    client._recover_once = AsyncMock(side_effect=RuntimeCompatibilityError())
    client._recovery.schedule()
    await client._recovery.task
    assert client._recover_once.await_count == 1 and client._recovery.blocked
    delayed = AsyncClient(reconnectAttempts=3, reconnectInitialDelay=30)
    delayed._recover_once = AsyncMock()
    delayed._recovery.schedule()
    await delayed.close()
    delayed._recover_once.assert_not_called()
    assert delayed.state == SessionState.CLOSED


@pytest.mark.asyncio
async def test_bounded_admission_recovers_after_cancellation():
    work = WorkController({"maxConcurrentOperations": 1, "maxPendingOperations": 2})
    entered, release = asyncio.Event(), asyncio.Event()

    async def occupy():
        async with work.slot():
            entered.set()
            await release.wait()

    first = asyncio.create_task(occupy())
    await entered.wait()
    waiting = asyncio.create_task(occupy())
    await eventually(lambda: work.stats["waiting"] == 1)
    with pytest.raises(OperationQueueFullError):
        async with work.slot():
            pytest.fail("Overflow was admitted")
    waiting.cancel()
    with pytest.raises(asyncio.CancelledError):
        await waiting
    release.set()
    await first
    assert work.stats == {"active": 0, "waiting": 0, "rejected": 1, "completed": 1}


@pytest.mark.asyncio
async def test_ack_evidence_waits_without_resending_and_handles_peer_signal():
    listeners = []

    def on_ack(callback):
        listeners.append(callback)
        return lambda: listeners.remove(callback)

    context = ready_context(
        onAck=on_ack,
        sendText_=AsyncMock(return_value={"id": "out"}),
        getMessageById_=AsyncMock(return_value={"id": "out", "fromMe": True, "ack": 1}),
    )
    service = ServiceHub(context).messages
    await service.send_text("chat", "text", operation_id="one")
    assert not (await service.delivery_status("one"))["delivered"]
    waiting = asyncio.create_task(service.wait_for_delivery("one", target="read", timeout=1))
    await eventually(lambda: bool(listeners))
    await listeners[0]({"id": "out", "ack": 5})
    assert not (await service.delivery_status("one"))["read"]
    await listeners[0]({"id": {"_serialized": "out"}, "ack": 3})
    result = await waiting
    assert result["read"] and result["delivered"] and not result["played"]
    context.sendText_.assert_awaited_once()
    with pytest.raises(AcknowledgementTimeoutError):
        await service.wait_for_delivery("one", target="played", timeout=0.02)
    await context._ack_observer.close()
    assert not listeners
    await service.deliveries.aclose()


@pytest.mark.asyncio
async def test_ack_negative_and_unknown_values_are_not_success():
    observer = AckObserver(SimpleNamespace(onAck=lambda callback: lambda: None))
    for value in (-7, -3, 0, 5, True, "3"):
        await observer.observe({"id": "out", "ack": value})
    assert observer.values["out"] == 0
    await observer.close()


@pytest.mark.asyncio
async def test_media_identity_checks_bytes_and_owns_admission_until_late_completion(tmp_path):
    path = tmp_path / "document.txt"
    path.write_bytes(b"original")
    context = ready_context()
    service = ServiceHub(context).messages
    started, release = asyncio.Event(), asyncio.Event()
    staged = []

    async def send(context, to, media, **kwargs):
        staged.append(media.path)
        started.set()
        await release.wait()
        assert media.path.read_bytes() == b"original"
        return {"id": "media-id"}

    with patch("WPP_Whatsapp.core.services.send_prepared", side_effect=send) as dispatch:
        with pytest.raises(DeliveryUncertainError):
            await service.send_media("chat", path, operation_id="file", timeout=0.01)
        assert started.is_set() and context._work_controller.stats["active"] == 1
        path.write_bytes(b"changed")
        with pytest.raises(OperationConflictError):
            await service.send_media("chat", path, operation_id="file")
        assert staged[0].exists()
        release.set()
        await eventually(lambda: service.deliveries.get("file").state == DeliveryState.CONFIRMED)
        assert not staged[0].exists() and context._work_controller.stats["active"] == 0
        dispatch.assert_awaited_once()
    await service.deliveries.aclose()


@pytest.mark.asyncio
async def test_pacing_applies_once_and_does_not_delay_reads():
    context = ready_context(
        sendText_=AsyncMock(return_value={"id": "out"}),
        getMessageById_=AsyncMock(return_value={"id": "out"}),
    )
    hub = ServiceHub(context)
    work = context._work_controller = WorkController({})
    work.limiter = AsyncMock()
    await hub.messages.send_text("chat", "text", operation_id="one")
    await hub.messages.send_text("chat", "text", operation_id="one")
    await hub.messages.get_message("out")
    work.limiter.acquire.assert_awaited_once()
    context.sendText_.assert_awaited_once()
    await hub.messages.deliveries.aclose()


@pytest.mark.asyncio
async def test_ack_timeout_includes_a_stalled_lookup():
    from WPP_Whatsapp.core.acknowledgements import wait_for_ack

    gate = asyncio.Event()
    service = SimpleNamespace(
        _ack_observer=lambda: SimpleNamespace(closed=False),
        delivery_status=AsyncMock(side_effect=lambda operation: gate.wait()),
    )

    async def stalled(operation):
        await gate.wait()

    service.delivery_status = stalled
    with pytest.raises(AcknowledgementTimeoutError):
        await wait_for_ack(service, "one", "read", 0.01)


@pytest.mark.asyncio
async def test_recovery_skips_reopening_an_already_recovered_transport():
    client = AsyncClient(reconnectAttempts=2, reconnectInitialDelay=0)
    client._state = SessionState.READY
    client._recover_once = AsyncMock()
    client._recovery.schedule()
    await client._recovery.task
    client._recover_once.assert_not_called()
    await client.close()


@pytest.mark.parametrize(
    "options",
    [
        {"reconnectAttempts": True},
        {"reconnectInitialDelay": True},
        {"sendRateCalls": -1},
        {"eventRetentionSeconds": 0},
        {"sendRatePeriod": float("inf")},
        {"maxPendingOperations": 1},
        {"maxConcurrentOperations": 0},
        {"eventStore": ""},
    ],
)
def test_reliability_settings_reject_invalid_values_before_startup(options):
    with pytest.raises(ValueError):
        AsyncClient(**options)


@pytest.mark.asyncio
async def test_page_close_recovers_when_legacy_handler_already_closed_context(tmp_path):
    page = Mock()
    handlers = {}
    page.on.side_effect = lambda name, callback: handlers.update({name: callback})
    browser = SimpleNamespace(page=page, open=AsyncMock(), close=AsyncMock())
    context = ready_context(
        start=AsyncMock(), _shutdown_session=AsyncMock(), onStateChange=Mock(), isClosed=False
    )
    context.async_services = ServiceHub(context)
    client = AsyncClient(wait_for_login=False, user_data_dir=tmp_path, reconnectAttempts=1)
    client._recovery.schedule = Mock()
    with (
        patch("WPP_Whatsapp.core.client.AsyncBrowser", return_value=browser),
        patch("WPP_Whatsapp.api.Whatsapp.Whatsapp", return_value=context),
    ):
        await client.connect()
        context.isClosed = True
        context.lifecycle.transition(SessionState.CLOSED)
        handlers["close"]()
        await eventually(lambda: client._recovery.schedule.called)
        client._recovery.schedule.assert_called_once()
        await client.close()
        handlers["close"]()
        await asyncio.sleep(0)
        client._recovery.schedule.assert_called_once()


@pytest.mark.asyncio
async def test_download_admission_releases_on_cancellation(tmp_path):
    service = ServiceHub(ready_context()).messages
    entered, release = asyncio.Event(), asyncio.Event()

    async def download(*args, **kwargs):
        entered.set()
        await release.wait()

    with patch("WPP_Whatsapp.core.services.download_to", side_effect=download):
        task = asyncio.create_task(service.download_media_to("existing", tmp_path / "file"))
        await entered.wait()
        assert service.context._work_controller.stats["active"] == 1
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        assert service.context._work_controller.stats["active"] == 0
