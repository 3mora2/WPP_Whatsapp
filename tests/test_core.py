import asyncio
import os
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import pytest
from playwright.async_api import Error

from WPP_Whatsapp import Whatsapp
from WPP_Whatsapp.core.bridge import JavascriptBridge
from WPP_Whatsapp.core.commands import COMMANDS
from WPP_Whatsapp.core.delivery import DeliveryTracker, DeliveryState
from WPP_Whatsapp.core.engine import AsyncBrowser
from WPP_Whatsapp.core.errors import (BridgeError, DeliveryUncertainError,
                                     EventQueueFullError, ProfileInUseError, SessionNotReadyError)
from WPP_Whatsapp.core.events import EventDispatcher, EventEmitter
from WPP_Whatsapp.core.lifecycle import Deadline, SessionLifecycle, SessionState
from WPP_Whatsapp.core.profiles import ProfileLease, session_directory
from WPP_Whatsapp.core.runtime_cache import RuntimeCache
from WPP_Whatsapp.core.services import ServiceHub
from WPP_Whatsapp.controllers.browser import ThreadsafeBrowser
from WPP_Whatsapp.api.helpers.wa_version import getWaJs
from tests.test_wajs_updates import response, release
from tests.helpers import eventually


def test_millisecond_deadline_is_monotonic_and_can_be_disabled():
    with patch('WPP_Whatsapp.core.lifecycle.time.monotonic', return_value=100):
        deadline = Deadline.milliseconds(180000)
        disabled = Deadline(0)
    with patch('WPP_Whatsapp.core.lifecycle.time.monotonic', return_value=279):
        assert not deadline.expired and deadline.remaining == 1
    with patch('WPP_Whatsapp.core.lifecycle.time.monotonic', return_value=281):
        assert deadline.expired and not disabled.expired


@pytest.mark.parametrize('value', [-1, float('inf'), float('nan'), '60'])
def test_invalid_deadlines_are_rejected(value):
    with pytest.raises(ValueError):
        Deadline(value)


def test_lifecycle_guard_and_closed_session_transitions():
    life = SessionLifecycle()
    with pytest.raises(SessionNotReadyError):
        life.transition(SessionState.READY)
    life.transition(SessionState.STARTING)
    life.transition(SessionState.SYNCING)
    life.transition(SessionState.READY)
    life.require_ready()
    life.transition(SessionState.CLOSING)
    with pytest.raises(Exception, match='closing'):
        life.transition(SessionState.READY)
    life.transition(SessionState.CLOSED)
    life.transition(SessionState.STARTING)


@pytest.mark.parametrize('name', ['../other', '/absolute', 'a/b', '..', '', 'c:\\x'])
def test_session_names_cannot_escape_directory(tmp_path, name):
    with pytest.raises(ValueError):
        session_directory(tmp_path, name)


def test_profile_lease_is_exclusive_and_reusable(tmp_path):
    first = ProfileLease(tmp_path).acquire()
    try:
        with pytest.raises(ProfileInUseError):
            ProfileLease(tmp_path).acquire()
    finally:
        first.release()
    second = ProfileLease(tmp_path).acquire()
    second.release()


def test_runtime_cache_detects_corruption(tmp_path):
    cache = RuntimeCache(tmp_path)
    url = 'https://example.test/runtime.js'
    cache.write(url, '// runtime')
    assert cache.read(url) == '// runtime'
    next(tmp_path.glob('*.js')).write_text('// changed')
    assert cache.read(url) is None


@pytest.mark.asyncio
async def test_latest_discovery_precedes_verified_cached_asset(tmp_path):
    session = Mock()
    session.get.side_effect = [response(release()), response(content='// runtime'), response(release())]
    manager = Mock(__aenter__=AsyncMock(return_value=session), __aexit__=AsyncMock(return_value=False))
    with patch('WPP_Whatsapp.api.helpers.wa_version.aiohttp.ClientSession', return_value=manager):
        assert (await getWaJs(cache_dir=tmp_path))['content'] == '// runtime'
        assert (await getWaJs(cache_dir=tmp_path))['content'] == '// runtime'
    assert len(session.get.call_args_list) == 3
    assert session.get.call_args_list[-1].args[0].endswith('/latest')


@pytest.mark.asyncio
async def test_bridge_binds_page_and_redacts_error_payload():
    page = object()
    transport = SimpleNamespace(page_evaluate=AsyncMock(side_effect=Error('secret message body')))
    bridge = JavascriptBridge(transport, page)
    key = next(iter(COMMANDS))
    with pytest.raises(BridgeError) as error:
        await bridge.call(key, {'body': 'private'})
    assert 'secret' not in str(error.value) and 'private' not in str(error.value)
    assert transport.page_evaluate.call_args.kwargs['page'] is page
    assert bridge.metrics['failures'] == 1


@pytest.mark.asyncio
async def test_ordered_events_support_sync_async_and_error_isolation():
    emitter, delivered, errors = EventEmitter(), [], []
    async def async_callback(value):
        await asyncio.sleep(.001)
        delivered.append(value)
    emitter.on('message', lambda value: (_ for _ in ()).throw(ValueError('private')))
    emitter.on('message', async_callback)
    emitter.on('message', lambda value: delivered.append(value * 10))
    dispatcher = EventDispatcher(emitter, on_error=errors.append)
    await asyncio.gather(*(dispatcher.submit('message', i) for i in (1, 2, 3)))
    assert delivered == [1, 10, 2, 20, 3, 30]
    assert errors == ['ValueError'] * 3
    await dispatcher.close()


@pytest.mark.asyncio
async def test_event_overflow_and_deduplication_are_explicit():
    emitter, gate = EventEmitter(), asyncio.Event()
    emitter.on('onMessage', lambda message: None)
    async def blocked(message):
        await gate.wait()
    emitter.on('onMessage', blocked)
    dispatcher = EventDispatcher(emitter, maxsize=1)
    first = asyncio.create_task(dispatcher.submit('onMessage', {'id': '1'}))
    await asyncio.sleep(.01)
    second = asyncio.create_task(dispatcher.submit('onMessage', {'id': '2'}))
    await asyncio.sleep(.01)
    with pytest.raises(EventQueueFullError):
        await dispatcher.submit('onMessage', {'id': '3'})
    await dispatcher.submit('onMessage', {'id': '1'})
    gate.set()
    await asyncio.gather(first, second)
    assert dispatcher.stats['duplicates'] == 1 and dispatcher.stats['rejected'] == 1
    await dispatcher.close()


@pytest.mark.asyncio
async def test_delivery_receipt_deduplicates_across_restarts(tmp_path):
    path = tmp_path / 'delivery.db'
    tracker = DeliveryTracker(path)
    send = AsyncMock(return_value={'id': 'message'})
    receipt = await tracker.send(send, 'operation')
    assert receipt.state == DeliveryState.CONFIRMED
    tracker.close()
    reopened = DeliveryTracker(path)
    assert await reopened.send(send, 'operation') == receipt
    send.assert_awaited_once()
    reopened.close()
    assert b'message body' not in path.read_bytes()


@pytest.mark.asyncio
async def test_delivery_timeout_is_unknown_and_late_confirmation_is_recorded():
    tracker, gate, count = DeliveryTracker(), asyncio.Event(), []
    async def send():
        count.append(1)
        await gate.wait()
        return {'id': 'verified'}
    with pytest.raises(DeliveryUncertainError):
        await tracker.send(send, 'op', timeout=.01)
    assert tracker.get('op').state == DeliveryState.UNKNOWN
    with pytest.raises(DeliveryUncertainError):
        await tracker.send(send, 'op')
    gate.set()
    await eventually(lambda: tracker.get('op').state == DeliveryState.CONFIRMED)
    assert tracker.get('op').state == DeliveryState.CONFIRMED and count == [1]


@pytest.mark.asyncio
async def test_duplicate_durable_claims_cannot_send_twice(tmp_path):
    path = tmp_path / 'ledger.db'
    first, second = DeliveryTracker(path), DeliveryTracker(path)
    gate = asyncio.Event()
    async def send():
        await gate.wait()
        return {'id': 'message'}
    task = asyncio.create_task(first.send(send, 'same'))
    await asyncio.sleep(.01)
    with pytest.raises(DeliveryUncertainError):
        await second.send(send, 'same')
    gate.set()
    await task
    first.close()
    second.close()


@pytest.mark.asyncio
async def test_composed_services_use_owner_loop_and_track_send():
    life = SessionLifecycle()
    life.transition(SessionState.STARTING)
    life.transition(SessionState.READY)
    async def run(coro):
        return await coro
    context = SimpleNamespace(session='test', options={}, lifecycle=life,
                              ThreadsafeBrowser=SimpleNamespace(create_task=run),
                              sendText_=AsyncMock(return_value={'id': 'message'}))
    hub = ServiceHub(context)
    receipt = await hub.messages.send_text('123', 'private', operation_id='op')
    assert receipt.message_id == 'message'
    assert await hub.messages.send_text('123', 'private', operation_id='op') == receipt
    context.sendText_.assert_awaited_once()
    assert Whatsapp.__bases__ == (object,)


@pytest.mark.asyncio
async def test_syncing_timeout_uses_milliseconds():
    client = Whatsapp.__new__(Whatsapp)
    client.isStarted = client.isLogged = True
    client.isInChat = client.isClosed = False
    client.options = {'deviceSyncTimeout': 10}
    client.page = Mock(is_closed=Mock(return_value=False))
    client.isInsideChat = AsyncMock(return_value=False)
    with patch('WPP_Whatsapp.core.lifecycle.time.monotonic', side_effect=[100, 100.02]):
        assert not await client.waitForInChat_()


@pytest.mark.skipif(os.getenv('RUN_WHATSAPP_BROWSER_TESTS') != '1' or os.getenv('CI') == 'true', reason='Opt-in native Chrome test')
@pytest.mark.asyncio
async def test_native_engine_and_sync_facade_close_owned_browsers(tmp_path):
    engine = AsyncBrowser()
    await engine.open(channel='chrome', headless=True, user_data_dir=str(tmp_path / 'async'))
    await engine.goto('data:text/html,<h1>native</h1>')
    assert await engine.page_evaluate('() => document.querySelector("h1").textContent') == 'native'
    assert await engine.wait_for_first_selectors('h2', 'h1', timeout=1) == 'h1'
    assert await engine.wait_for_first_selectors('h2', timeout=.01) is None
    with pytest.raises(ValueError):
        await engine.wait_for_first_selectors()
    await engine.close()
    await engine.close()
    browser = await asyncio.to_thread(ThreadsafeBrowser, channel='chrome', headless=True,
                                     user_data_dir=str(tmp_path / 'sync'))
    await browser.goto('data:text/html,<h1>sync</h1>')
    assert await browser.page_evaluate('() => document.querySelector("h1").textContent') == 'sync'
    assert await browser.wait_for_first_selectors('h2', 'h1', timeout=1) == 'h1'
    await asyncio.to_thread(browser.sync_close)
    assert not browser._runner.thread.is_alive()


@pytest.mark.skipif(os.getenv('RUN_WHATSAPP_BROWSER_TESTS') != '1' or os.getenv('CI') == 'true', reason='Opt-in native Chrome test')
@pytest.mark.asyncio
async def test_multi_session_close_isolated_and_profile_can_be_reopened(tmp_path):
    from WPP_Whatsapp import MultiCreate
    factory = await asyncio.to_thread(MultiCreate, channel='chrome', headless=True, install=False)
    try:
        with patch.object(Whatsapp, 'start', AsyncMock()):
            first, duplicate = await asyncio.gather(*(
                asyncio.to_thread(factory.start, 'first', folderNameToken=str(tmp_path), waitForLogin=False)
                for _ in range(2)))
            assert first is duplicate and len(factory.ThreadsafeBrowser.contexts) == 1
            second = await asyncio.to_thread(factory.start, 'second', folderNameToken=str(tmp_path), waitForLogin=False)
            await asyncio.to_thread(first.close)
            assert first.page.is_closed() and not second.page.is_closed()
            reopened = await asyncio.to_thread(factory.start, 'first', folderNameToken=str(tmp_path), waitForLogin=False)
            assert not reopened.page.is_closed()
    finally:
        await asyncio.to_thread(factory.close_all)
    assert not factory.ThreadsafeBrowser._runner.thread.is_alive()


@pytest.mark.skipif(os.getenv('RUN_WHATSAPP_BROWSER_TESTS') != '1' or os.getenv('CI') == 'true', reason='Opt-in native Chrome test')
@pytest.mark.asyncio
async def test_sync_callback_can_close_its_browser_without_executor_deadlock(tmp_path):
    import threading
    browser = await asyncio.to_thread(ThreadsafeBrowser, channel='chrome', headless=True,
                                     user_data_dir=str(tmp_path / 'callback-close'))
    completed = threading.Event()
    async def setup():
        client = Whatsapp('callback-close', browser, browser.page)
        def callback(message):
            client.close()
            completed.set()
        client.onMessage(callback)
        return client._event_dispatcher()
    pending = None
    try:
        dispatcher = await browser.create_task(setup())
        pending = asyncio.run_coroutine_threadsafe(dispatcher.submit('onMessage', {'id': 'synthetic'}), browser.loop)
        assert await asyncio.to_thread(completed.wait, 4)
        await asyncio.to_thread(browser._runner.thread.join, 4)
        assert not browser._runner.thread.is_alive()
    finally:
        await asyncio.to_thread(browser.sync_close)
        if pending and pending.done():
            try:
                pending.result()
            except BaseException:
                pass
