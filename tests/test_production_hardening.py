"""Crash recovery, leased consumers, retained idempotency and operational boundaries."""

import asyncio
import json
import sqlite3
import subprocess
import sys
import threading
import time
from contextlib import asynccontextmanager
from dataclasses import replace
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from tests.helpers import eventually, ready_context
from WPP_Whatsapp import AsyncClient, DurableConsumer, SQLiteEventStore
from WPP_Whatsapp.core.admin import main
from WPP_Whatsapp.core.delivery import DeliveryTracker
from WPP_Whatsapp.core.delivery_models import DeliveryReceipt, DeliveryState, ExpectedMessage
from WPP_Whatsapp.core.delivery_store import SQLiteDeliveryStore
from WPP_Whatsapp.core.errors import (
    DeliveryUncertainError,
    OperationConflictError,
    SessionClosedError,
)
from WPP_Whatsapp.core.event_buffer import EventBuffer
from WPP_Whatsapp.core.media import prepare_media
from WPP_Whatsapp.core.metrics import process_snapshot, prometheus
from WPP_Whatsapp.core.services import ServiceHub
from WPP_Whatsapp.core.subscriptions import ClientEvents

KEY = "true_1@g.us_MESSAGE_2@lid"
EXPECTED = ExpectedMessage(KEY, "1@g.us", "chat")


@pytest.mark.asyncio
async def test_expected_key_is_committed_before_dispatch_and_reused_after_crash(tmp_path):
    path = tmp_path / "crashed.db"
    script = """
import asyncio, os, sys
from WPP_Whatsapp.core.delivery import DeliveryTracker
from WPP_Whatsapp.core.delivery_models import ExpectedMessage
async def run():
    tracker=DeliveryTracker(sys.argv[1], 'account')
    async def prepare(): return ExpectedMessage(sys.argv[2], '1@g.us', 'chat')
    async def crash(): os._exit(17)
    await tracker.send(crash, 'crashed', prepare=prepare, request_fingerprint='request')
asyncio.run(run())
"""
    result = subprocess.run(
        [sys.executable, "-c", script, str(path), KEY], capture_output=True, timeout=30
    )
    assert result.returncode == 17, result.stderr.decode()
    tracker = DeliveryTracker(path, "account")
    assert await tracker.expected_async("crashed") == EXPECTED
    assert tracker.get("crashed").state == DeliveryState.UNKNOWN
    call = AsyncMock()
    with pytest.raises(DeliveryUncertainError):
        await tracker.send(call, "crashed", request_fingerprint="request")
    call.assert_not_called()
    context = ready_context(
        getMessageById_=AsyncMock(return_value={"id": KEY, "fromMe": True, "type": "chat"})
    )
    context._delivery_tracker = tracker
    receipt = await ServiceHub(context).messages.recover("crashed")
    assert receipt == DeliveryReceipt("crashed", DeliveryState.CONFIRMED, KEY)
    await tracker.aclose()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "changed", [{"id": "true_1@g.us_OTHER"}, {"fromMe": False}, {"type": "image"}]
)
async def test_recovery_requires_exact_reserved_evidence(tmp_path, changed):
    tracker = DeliveryTracker(tmp_path / "ledger")
    tracker._store.claim(DeliveryReceipt("one", DeliveryState.PENDING))
    tracker._store.set_expected("one", EXPECTED)
    context = ready_context(
        getMessageById_=AsyncMock(
            return_value={"id": KEY, "fromMe": True, "type": "chat", **changed}
        )
    )
    context._delivery_tracker = tracker
    with pytest.raises(ValueError):
        await ServiceHub(context).messages.recover("one")
    assert tracker.get("one").state == DeliveryState.UNKNOWN
    await tracker.aclose()


@pytest.mark.asyncio
async def test_preparation_failure_cannot_dispatch_or_repeat(tmp_path):
    tracker = DeliveryTracker(tmp_path / "ledger")
    call = AsyncMock()
    with pytest.raises(OSError):
        await tracker.send(call, "one", prepare=AsyncMock(side_effect=OSError("disk full")))
    with pytest.raises(DeliveryUncertainError):
        await tracker.send(call, "one")
    call.assert_not_called()
    await tracker.aclose()


@pytest.mark.asyncio
async def test_send_result_with_different_key_remains_unknown(tmp_path):
    tracker = DeliveryTracker(tmp_path / "ledger")
    with pytest.raises(DeliveryUncertainError):
        await tracker.send(
            AsyncMock(return_value={"id": "other"}), "one", prepare=AsyncMock(return_value=EXPECTED)
        )
    assert tracker.get("one").state == DeliveryState.UNKNOWN
    await tracker.aclose()


@pytest.mark.asyncio
async def test_native_text_passes_persisted_key_without_mutating_caller_options(tmp_path):
    tracker = DeliveryTracker(tmp_path / "ledger")

    async def send(to, content, options=None):
        assert (await tracker.expected_async("one")).message_id == options["messageId"]
        return {"id": options["messageId"]}

    context = ready_context(
        sendText_=send,
        bridge=SimpleNamespace(call=AsyncMock(return_value={"id": KEY, "chatId": "1@g.us"})),
    )
    context._delivery_tracker = tracker
    options = {"quotedMsg": "quote"}
    messages = ServiceHub(context).messages
    receipt = await messages.send_text("1@g.us", "private body", options, operation_id="one")
    assert receipt.message_id == KEY and options == {"quotedMsg": "quote"}
    assert (
        await messages.send_text("1@g.us", "private body", options, operation_id="one") == receipt
    )
    context.bridge.call.assert_awaited_once()
    assert b"private body" not in (tmp_path / "ledger").read_bytes()
    await tracker.aclose()


@pytest.mark.asyncio
async def test_compaction_keeps_tombstone_namespace_and_unknown_operations(tmp_path):
    path = tmp_path / "ledger"
    tracker = DeliveryTracker(path, "one")
    await tracker.send(AsyncMock(return_value={"id": KEY}), "done", request_fingerprint="request")
    tracker._store.claim(DeliveryReceipt("pending", DeliveryState.PENDING))
    cutoff = time.time() + 1
    assert tracker._store.compact(cutoff, dry_run=True) == 1
    assert tracker._store.get("done").message_id == KEY
    assert tracker._store.compact(cutoff) == 1
    await tracker.aclose()
    reopened = DeliveryTracker(path, "one")
    call = AsyncMock()
    with pytest.raises(OperationConflictError, match="compacted"):
        await reopened.send(call, "done", request_fingerprint="request")
    assert reopened.get("pending").state == DeliveryState.UNKNOWN
    rows = await reopened.list_operations(limit=1)
    assert rows[0]["compacted"] and rows[0]["operation_id"] == "done"
    assert len(await reopened.list_operations(after="done")) == 1
    other = DeliveryTracker(path, "other")
    assert await other.list_operations() == []
    call.assert_not_called()
    await reopened.aclose()
    await other.aclose()


def journal(tmp_path, namespace="account", capacity=10):
    return SQLiteEventStore(tmp_path / "events", namespace, capacity, 3600)


def append(store, ident):
    store.append({"message": {"id": ident, "body": "private"}})


@pytest.mark.asyncio
async def test_consumer_ack_is_atomic_across_two_store_connections(tmp_path):
    first, second = journal(tmp_path), journal(tmp_path)
    append(first, "message")
    a, b = DurableConsumer(first, "worker"), DurableConsumer(second, "worker")
    claims = await asyncio.gather(a.claim(), b.claim())
    leases = [result["lease"] for result in claims if result["lease"]]
    assert len(leases) == 1
    await b.ack(leases[0])
    first.close()
    second.close()
    reopened = journal(tmp_path)
    assert (await DurableConsumer(reopened, "worker").claim())["lease"] is None
    # A separate consumer has an independent cursor.
    assert (await DurableConsumer(reopened, "other").claim())["lease"].sequence == 1
    reopened.close()


@pytest.mark.asyncio
async def test_expired_lease_retries_survives_retention_and_rejects_stale_ack(tmp_path):
    store = journal(tmp_path, capacity=1)
    append(store, "first")
    worker = DurableConsumer(store, "worker", lease_seconds=10)
    with patch("WPP_Whatsapp.core.consumers.time.time", return_value=100):
        first = (await worker.claim())["lease"]
    append(store, "second")  # Removes the original event, but its leased payload survives.
    with patch("WPP_Whatsapp.core.consumers.time.time", return_value=111):
        retry = (await worker.claim())["lease"]
        assert (
            retry.sequence == first.sequence and retry.event == first.event and retry.attempt == 2
        )
        with pytest.raises(ValueError, match="stale"):
            await worker.ack(first)
        await worker.renew(retry)
        await worker.ack(retry)
    assert (await worker.claim())["lease"].sequence == 2
    store.close()


@pytest.mark.asyncio
async def test_fail_backoff_exhaustion_and_dead_letter_are_durable(tmp_path):
    store = journal(tmp_path)
    append(store, "bad")
    append(store, "next")
    worker = DurableConsumer(store, "worker", max_attempts=2, retry_delay=5)
    with patch("WPP_Whatsapp.core.consumers.time.time", return_value=100):
        first = (await worker.claim())["lease"]
        await worker.fail(first)
        assert (await worker.claim())["lease"] is None
    store.close()
    store = journal(tmp_path)
    worker = DurableConsumer(store, "worker", max_attempts=2, retry_delay=5)
    with patch("WPP_Whatsapp.core.consumers.time.time", return_value=106):
        second = (await worker.claim())["lease"]
        assert second.attempt == 2
        await worker.fail(second)
        letters = await worker.dead_letters()
        assert letters[0]["category"] == "handler_failed" and letters[0]["attempts"] == 2
        assert (await worker.claim())["lease"].sequence == 2
    store.close()


@pytest.mark.asyncio
async def test_crash_exhaustion_advances_and_retention_gap_is_persisted(tmp_path):
    store = journal(tmp_path, capacity=1)
    append(store, "first")
    append(store, "second")
    worker = DurableConsumer(store, "worker", max_attempts=1, lease_seconds=10)
    with patch("WPP_Whatsapp.core.consumers.time.time", return_value=100):
        result = await worker.claim()
        assert result["lost"] == result["lost_total"] == 1
    with patch("WPP_Whatsapp.core.consumers.time.time", return_value=111):
        result = await worker.claim()
        assert result["lease"] is None and result["lost_total"] == 1
        assert (await worker.dead_letters())[0]["category"] == "lease_expired"
    store.close()
    reopened = journal(tmp_path, capacity=1)
    assert (await DurableConsumer(reopened, "worker", max_attempts=1).claim())["lost_total"] == 1
    reopened.close()


@pytest.mark.asyncio
async def test_leases_cannot_cross_account_or_consumer(tmp_path):
    one, other = journal(tmp_path), journal(tmp_path, "other")
    append(one, "same")
    append(other, "same")
    worker = DurableConsumer(one, "worker")
    lease = (await worker.claim())["lease"]
    for candidate in (DurableConsumer(other, "worker"), DurableConsumer(one, "different")):
        await candidate.claim()
        with pytest.raises(ValueError):
            await candidate.ack(lease)
    with pytest.raises(ValueError):
        await worker.ack(replace(lease, token="x" * 32))
    await worker.ack(lease)
    one.close()
    other.close()


@pytest.mark.asyncio
async def test_core_journal_detaches_and_cursor_survives_restart(tmp_path):
    events = ClientEvents()
    async with events.journal(tmp_path / "events", namespace="account") as history:
        await history._receive({"id": "full_group_id", "body": "test", "base64": "omit"})
        consumer = history.consumer("application")
        lease = (await consumer.claim())["lease"]
        assert "base64" not in lease.event["message"]
        await consumer.ack(lease)
    assert not events._entries
    async with events.journal(tmp_path / "events", namespace="account") as history:
        assert (await history.consumer("application").claim())["lease"] is None


def test_admin_preview_preserves_metadata_and_apply_reserves_ids(tmp_path, capsys):
    path = tmp_path / "ledger"
    store = SQLiteDeliveryStore(path, "account")
    store.save(DeliveryReceipt("one", DeliveryState.CONFIRMED, KEY))
    store.close()
    args = ["--store", str(path), "--namespace", "account"]
    main(args + ["compact", "--older-than-days", "0"])
    assert json.loads(capsys.readouterr().out) == {"count": 1, "applied": False}
    main(args + ["inspect", "one"])
    assert json.loads(capsys.readouterr().out)["receipt"]["message_id"] == KEY
    main(args + ["compact", "--older-than-days", "0", "--apply"])
    assert json.loads(capsys.readouterr().out)["applied"]
    main(args + ["list"])
    assert json.loads(capsys.readouterr().out)[0]["compacted"]


@pytest.mark.asyncio
async def test_metrics_are_numeric_identifier_free_and_exclude_unowned_browsers():
    result = await AsyncClient().metrics()
    assert result["process"]["python_rss_bytes"] > 0
    assert result["process"]["owned_browser_processes"] == 0
    text = prometheus({**result, "commands": {"private-message\nspoof": {"calls": 4}}})
    assert "private-message" not in text and "spoof" not in text
    assert "python_rss_bytes" in text and KEY not in text
    # PID reuse cannot attribute another process to this browser.
    assert process_snapshot({1: -1})["owned_browser_processes"] == 0


@pytest.mark.asyncio
async def test_journal_close_waits_for_append_but_not_dispatcher_lifetime(tmp_path):
    history = ClientEvents().journal(tmp_path / "events")
    entered, release, keep_dispatcher = asyncio.Event(), asyncio.Event(), asyncio.Event()

    async def append_pending(message):
        entered.set()
        await release.wait()

    history.buffer.append = append_pending

    async def dispatcher():
        await history._receive({"id": "test"})
        await keep_dispatcher.wait()

    await history.__aenter__()
    worker = asyncio.create_task(dispatcher())
    await entered.wait()
    closing = asyncio.create_task(history.__aexit__(None, None, None))
    await asyncio.sleep(0)
    assert not closing.done()
    release.set()
    try:
        await asyncio.wait_for(closing, 1)
        assert not worker.done()
    finally:
        keep_dispatcher.set()
        await worker


@pytest.mark.asyncio
async def test_recovery_repeat_returns_confirmed_receipt_without_another_lookup(tmp_path):
    tracker = DeliveryTracker(tmp_path / "ledger")
    tracker._store.claim(DeliveryReceipt("one", DeliveryState.PENDING))
    tracker._store.set_expected("one", EXPECTED)
    context = ready_context(
        getMessageById_=AsyncMock(return_value={"id": KEY, "fromMe": True, "type": "chat"})
    )
    context._delivery_tracker = tracker
    service = ServiceHub(context).messages
    first = await service.recover("one")
    assert await service.recover("one") == first
    context.getMessageById_.assert_awaited_once()
    await tracker.aclose()


@pytest.mark.asyncio
async def test_client_journal_defaults_isolate_account_namespaces(tmp_path):
    first, second = AsyncClient("first"), AsyncClient("second")
    async with (
        first.events.journal(tmp_path / "events") as a,
        second.events.journal(tmp_path / "events") as b,
    ):
        await a._receive({"id": "one"})
        assert (await b.read())["events"] == []
        assert (await a.consumer("worker").claim())["lease"] is not None
        assert (await b.consumer("worker").claim())["lease"] is None


@pytest.mark.asyncio
async def test_post_dispatch_conversion_error_keeps_evidence_and_cannot_be_compacted(tmp_path):
    tracker = DeliveryTracker(tmp_path / "ledger")
    with pytest.raises(DeliveryUncertainError):
        await tracker.send(
            AsyncMock(side_effect=ValueError("result conversion failed")),
            "one",
            prepare=AsyncMock(return_value=EXPECTED),
        )
    assert tracker.get("one").state == DeliveryState.UNKNOWN
    assert await tracker.expected_async("one") == EXPECTED
    assert tracker._store.compact(time.time() + 10) == 0
    await tracker.aclose()


def test_event_pages_count_internal_retention_gaps_without_skipping_loss(tmp_path):
    store = journal(tmp_path)
    for number in range(1, 5):
        append(store, str(number))
    # Wall-clock corrections can leave a newer sequence with an older timestamp.
    with sqlite3.connect(tmp_path / "events") as db:
        db.execute("UPDATE events SET created=0 WHERE sequence=2")
    first = store.read(0, 2)
    assert [event["sequence"] for event in first["events"]] == [1, 3]
    assert first["lost"] == 1 and first["cursor"] == 3
    assert store.read(first["cursor"], 2)["lost"] == 0
    store.close()


@pytest.mark.asyncio
async def test_media_snapshot_survives_timeout_during_key_preparation(tmp_path):
    source = tmp_path / "input.txt"
    source.write_text("immutable", encoding="utf-8")
    captured = []
    entered, release = asyncio.Event(), asyncio.Event()

    @asynccontextmanager
    async def capture(*args, **kwargs):
        async with prepare_media(*args, **kwargs) as media:
            captured.append(media.path)
            yield media

    async def allocate(command, arguments):
        entered.set()
        await release.wait()
        return {"id": KEY, "chatId": "1@g.us"}

    async def dispatch(context, to, media, **kwargs):
        assert media.path.read_text(encoding="utf-8") == "immutable"
        assert kwargs["expected_id"] == KEY
        return {"id": KEY}

    context = ready_context(bridge=SimpleNamespace(call=allocate))
    context.options["deliveryStore"] = str(tmp_path / "ledger")
    service = ServiceHub(context).messages
    with (
        patch("WPP_Whatsapp.core.services.prepare_media", capture),
        patch("WPP_Whatsapp.core.services.send_prepared", dispatch),
    ):
        with pytest.raises(DeliveryUncertainError):
            await service.send_media("1@g.us", str(source), operation_id="slow-key", timeout=0.02)
        assert entered.is_set() and captured[0].exists()
        assert context._work_controller.stats["active"] == 1
        release.set()
        await eventually(
            lambda: service.deliveries.get("slow-key").state == DeliveryState.CONFIRMED
        )
    assert not captured[0].exists() and context._work_controller.stats["active"] == 0
    await service.deliveries.aclose()


@pytest.mark.asyncio
async def test_media_preparation_commit_failure_releases_snapshot_and_admission(tmp_path):
    class BrokenStore(SQLiteDeliveryStore):
        def set_expected(self, operation_id, expected):
            raise OSError("Injected key commit failure")

    source = tmp_path / "input.txt"
    source.write_text("test", encoding="utf-8")
    captured = []

    @asynccontextmanager
    async def capture(*args, **kwargs):
        async with prepare_media(*args, **kwargs) as media:
            captured.append(media.path)
            yield media

    context = ready_context(
        bridge=SimpleNamespace(call=AsyncMock(return_value={"id": KEY, "chatId": "1@g.us"}))
    )
    context._delivery_tracker = DeliveryTracker(store=BrokenStore(tmp_path / "ledger"))
    service = ServiceHub(context).messages
    dispatch = AsyncMock()
    with (
        patch("WPP_Whatsapp.core.services.prepare_media", capture),
        patch("WPP_Whatsapp.core.services.send_prepared", dispatch),
    ):
        with pytest.raises(OSError):
            await service.send_media("1@g.us", str(source), operation_id="disk-full")
    dispatch.assert_not_called()
    assert not captured[0].exists() and context._work_controller.stats["active"] == 0
    await service.deliveries.aclose()


@pytest.mark.asyncio
async def test_cancelled_callback_finishes_accepted_journal_write_before_close(tmp_path):
    buffer = EventBuffer(path=tmp_path / "events")
    entered, release = asyncio.Event(), threading.Event()
    original = buffer.store.append
    loop = asyncio.get_running_loop()

    def delayed(event):
        loop.call_soon_threadsafe(entered.set)
        assert release.wait(5)
        original(event)

    buffer.store.append = delayed
    appending = asyncio.create_task(buffer.append({"id": "persist-before-close"}))
    await entered.wait()
    appending.cancel()
    await asyncio.sleep(0)
    try:
        assert not appending.done()
    finally:
        release.set()
    with pytest.raises(asyncio.CancelledError):
        await appending
    assert buffer.store.read(0, 10)["events"][0]["message"]["id"] == "persist-before-close"
    await buffer.close()


@pytest.mark.asyncio
async def test_closed_tracker_reads_evicted_metadata_without_reopening_for_writes(tmp_path):
    path = tmp_path / "ledger with spaces.db"
    tracker = DeliveryTracker(path, "account")
    with tracker._store._connection as db:
        db.executemany(
            "INSERT INTO deliveries(namespace,id,state,message_id,updated) VALUES(?,?,?,?,?)",
            [("account", f"{index:04}", "confirmed", KEY, 1) for index in range(1100)],
        )
    for index in range(1100):
        assert tracker.get(f"{index:04}") is not None
    assert "0000" not in tracker.records and len(tracker.records) == 1000
    await tracker.aclose()
    receipt = await tracker.get_async("0000")
    assert receipt.message_id == KEY
    assert (await tracker.list_operations(limit=1))[0]["operation_id"] == "0000"
    assert tracker._store._closed
    with pytest.raises(SessionClosedError):
        # Closed tracker cannot dispatch, even though inspection is available.
        await tracker.send(AsyncMock(), "new")


@pytest.mark.asyncio
async def test_text_dispatch_uses_the_reserved_canonical_chat_and_original_request_identity(
    tmp_path,
):
    key = "true_canonical@lid_KEY"
    dispatches = []

    async def send(to, content, options=None):
        assert to == "canonical@lid" and options["messageId"] == key
        dispatches.append(to)
        return {"id": key}

    context = ready_context(
        sendText_=send,
        bridge=SimpleNamespace(call=AsyncMock(return_value={"id": key, "chatId": "canonical@lid"})),
    )
    context.options["deliveryStore"] = str(tmp_path / "ledger")
    service = ServiceHub(context).messages
    first = await service.send_text("phone@c.us", "text", operation_id="alias")
    assert await service.send_text("phone@c.us", "text", operation_id="alias") == first
    assert dispatches == ["canonical@lid"]
    await service.deliveries.aclose()
