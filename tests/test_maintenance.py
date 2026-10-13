"""Behavioral regressions for the extension surface and persistence boundary."""

import asyncio
import inspect
import logging
import threading
from unittest.mock import AsyncMock, Mock, patch

import pytest

from tests.helpers import ready_context
from WPP_Whatsapp import AsyncClient, Create, MultiCreate
from WPP_Whatsapp.core.delivery import DeliveryState, DeliveryTracker
from WPP_Whatsapp.core.delivery_store import MemoryDeliveryStore
from WPP_Whatsapp.core.errors import DeliveryUncertainError, SessionClosedError
from WPP_Whatsapp.core.events import EVENT_NAMES
from WPP_Whatsapp.core.options import validate_options
from WPP_Whatsapp.core.service_registry import ServiceDefinition, snake
from WPP_Whatsapp.core.services import ServiceHub, SyncServices


@pytest.mark.parametrize(
    "options",
    [
        {"deviceSyncTimeout": -1},
        {"operationTimeout": float("nan")},
        {"navigationTimeout": "3000"},
        {"runtimeReadyTimeout": float("inf")},
        {"eventQueueSize": 0},
        {"eventQueueSize": True},
        {"deliveryStore": ""},
        {"runtimeCacheDir": 123},
    ],
)
def test_invalid_known_options_fail_before_a_browser_is_constructed(options):
    with patch("WPP_Whatsapp.core.client.AsyncBrowser") as browser:
        with pytest.raises(ValueError):
            AsyncClient(**options)
    browser.assert_not_called()
    with patch("WPP_Whatsapp.controllers.initializer.ThreadsafeBrowser") as browser:
        with pytest.raises(ValueError):
            Create("invalid", **options)
    browser.assert_not_called()
    with patch("WPP_Whatsapp.controllers.init_multi.ThreadsafeBrowser") as browser:
        with pytest.raises(ValueError):
            MultiCreate(**options)
    browser.assert_not_called()


def test_extension_options_are_preserved_without_mutating_the_callers_mapping():
    original = {"deviceSyncTimeout": 0, "extensionOption": object(), "channel": "chrome"}
    validated = validate_options(original)
    assert validated == original and validated is not original
    validated["deviceSyncTimeout"] = 100
    assert original["deviceSyncTimeout"] == 0


def test_services_do_not_expose_lifecycle_methods_and_keep_inspectable_signatures():
    hub = ServiceHub(ready_context())
    for internal in ("close_async", "clear_all_interval", "after_page_script_injected"):
        assert not hasattr(hub.messages, internal)
    signature = inspect.signature(hub.messages.send_image)
    assert "self" not in signature.parameters
    assert "filePath" in signature.parameters
    assert signature.parameters["operation_id"].kind == inspect.Parameter.KEYWORD_ONLY
    assert hub.messages.send_image is hub.messages.send_image
    sync = SyncServices(hub)
    assert sync.messages is sync.messages
    assert sync.messages.send_image is sync.messages.send_image
    assert inspect.signature(sync.messages.send_image) == signature
    assert "groups" in dir(sync)


@pytest.mark.asyncio
async def test_declaring_a_service_extends_the_native_client_without_editing_dispatch():
    class Extension:
        async def getHTTPStatus_(self):
            return 204

    context = ready_context(getHTTPStatus_=AsyncMock(return_value=204))
    definition = ServiceDefinition("extension", (Extension,))
    client = AsyncClient()
    with (
        patch("WPP_Whatsapp.core.services.service_definitions", return_value=(definition,)),
        patch("WPP_Whatsapp.core.client.service_definitions", return_value=(definition,)),
    ):
        context.async_services = ServiceHub(context)
        client._context = context
        assert await client.extension.get_http_status() == 204
        assert "extension" in dir(client)
    assert snake("getWAJSVersion_") == "get_wajs_version"


def test_event_names_are_explicit_and_internal_handlers_are_rejected():
    context = ready_context(onMessage=Mock())
    events = ServiceHub(context).events
    events.on("onMessage", print)
    context.onMessage.assert_called_once_with(print)
    with pytest.raises(ValueError):
        events.on("onInterfaceChange_", print)
    assert "onMessage" in EVENT_NAMES


@pytest.mark.asyncio
async def test_opening_second_ledger_does_not_downgrade_the_active_owner(tmp_path):
    path = tmp_path / "ledger.db"
    tracker = DeliveryTracker(path)
    started, gate = asyncio.Event(), asyncio.Event()

    async def execute():
        started.set()
        await gate.wait()
        return {"id": "confirmed"}

    task = asyncio.create_task(tracker.send(execute, "active"))
    await started.wait()
    observer = DeliveryTracker(path)
    try:
        assert tracker.get("active").state == DeliveryState.PENDING
        assert observer.get("active").state == DeliveryState.UNKNOWN
        assert tracker.get("active").state == DeliveryState.PENDING
        gate.set()
        await task
        assert observer.get("active").state == DeliveryState.CONFIRMED
    finally:
        gate.set()
        await task
        await tracker.aclose()
        await observer.aclose()


@pytest.mark.asyncio
async def test_blocking_storage_does_not_block_the_event_loop_and_cancelled_claim_never_sends():
    class BlockingStore(MemoryDeliveryStore):
        blocking = True

        def claim(self, receipt):
            started.set()
            gate.wait(2)
            return super().claim(receipt)

    started, gate = threading.Event(), threading.Event()
    tracker, send = DeliveryTracker(store=BlockingStore()), AsyncMock(return_value={"id": "unused"})
    task = asyncio.create_task(tracker.send(send, "cancel-before-dispatch"))
    assert await asyncio.to_thread(started.wait, 1)
    # This tick could not execute if the storage claim blocked the owner loop.
    await asyncio.sleep(0)
    assert not task.done()
    task.cancel()
    gate.set()
    with pytest.raises(asyncio.CancelledError):
        await task
    send.assert_not_called()
    assert tracker.get("cancel-before-dispatch").state == DeliveryState.FAILED
    await tracker.aclose()


@pytest.mark.asyncio
async def test_storage_failure_after_dispatch_is_uncertain_and_never_replays():
    class BrokenStore(MemoryDeliveryStore):
        def save(self, receipt):
            raise OSError("private filesystem path")

    tracker = DeliveryTracker(store=BrokenStore())
    send = AsyncMock(return_value={"id": "sent"})
    with pytest.raises(DeliveryUncertainError) as error:
        await tracker.send(send, "disk-error")
    assert "private" not in str(error.value)
    assert tracker.get("disk-error").state == DeliveryState.UNKNOWN
    with pytest.raises(DeliveryUncertainError):
        await tracker.send(send, "disk-error")
    send.assert_awaited_once()
    await tracker.aclose()


@pytest.mark.asyncio
async def test_closed_tracker_rejects_new_sends_and_keeps_unresolved_results_unknown():
    tracker = DeliveryTracker()
    gate, started = asyncio.Event(), asyncio.Event()

    async def execute():
        started.set()
        await gate.wait()
        return {"id": "completed-after-close"}

    task = asyncio.create_task(tracker.send(execute, "closing"))
    await started.wait()
    await tracker.aclose()
    await tracker.aclose()
    assert tracker.get("closing").state == DeliveryState.UNKNOWN
    send = AsyncMock()
    with pytest.raises(SessionClosedError):
        await tracker.send(send, "new")
    send.assert_not_called()
    gate.set()
    with pytest.raises(DeliveryUncertainError):
        await task


def test_library_logging_does_not_configure_the_application_root_logger():
    from importlib import reload

    from WPP_Whatsapp.api import const

    before = tuple(logging.getLogger().handlers)
    with patch("logging.basicConfig") as configure, patch("os.mkdir") as mkdir:
        reload(const)
    configure.assert_not_called()
    mkdir.assert_not_called()
    assert tuple(logging.getLogger().handlers) == before
    assert sum(isinstance(handler, logging.NullHandler) for handler in const.Logger.handlers) == 1


def test_factory_accepts_partial_and_callable_callbacks(tmp_path):
    from functools import partial

    callback = partial(lambda prefix, **values: None, "qr")

    class Loading:
        def __call__(self, percent, message):
            pass

    loading = Loading()
    factory = Create(
        "callbacks", folderNameToken=str(tmp_path), catchQR=callback, onLoadingScreen=loading
    )
    assert factory.catchQR is callback and factory.onLoadingScreen is loading


@pytest.mark.asyncio
async def test_interval_awaits_async_callable_objects_and_cancels_cleanly():
    from WPP_Whatsapp.api.helpers.jsFunction import setInterval

    received = asyncio.Event()

    class Callback:
        async def __call__(self):
            received.set()

    interval = setInterval(asyncio.get_running_loop(), Callback(), 60)
    try:
        await asyncio.wait_for(received.wait(), 1)
    finally:
        interval.set()
        if interval.task is not None:
            await asyncio.gather(interval.task, return_exceptions=True)
