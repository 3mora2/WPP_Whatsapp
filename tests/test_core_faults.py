import asyncio
import inspect
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import pytest

from WPP_Whatsapp import AsyncClient, Whatsapp
from WPP_Whatsapp.api.layers.HostLayer import HostLayer
from WPP_Whatsapp.core.bridge import JavascriptBridge
from WPP_Whatsapp.core.commands import COMMANDS
from WPP_Whatsapp.core.delivery import DeliveryTracker, DeliveryState
from WPP_Whatsapp.core.errors import (BridgeError, DeliveryUncertainError, RuntimeCompatibilityError,
                                     SessionClosedError, SessionNotReadyError)
from WPP_Whatsapp.core.events import EventDispatcher, EventEmitter
from WPP_Whatsapp.core.lifecycle import SessionLifecycle, SessionState
from WPP_Whatsapp.core.services import ServiceHub
from tests.helpers import eventually, ready_context


async def direct(task):
    return await task


@pytest.mark.asyncio
async def test_cancelled_send_remains_unknown_and_cannot_be_replayed():
    tracker, gate, started = DeliveryTracker(), asyncio.Event(), asyncio.Event()
    async def execute():
        started.set()
        await gate.wait()
        return {'id': 'completed-after-cancellation'}
    task = asyncio.create_task(tracker.send(execute, 'cancelled'))
    await started.wait()
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert tracker.get('cancelled').state == DeliveryState.UNKNOWN
    with pytest.raises(DeliveryUncertainError):
        await tracker.send(execute, 'cancelled')
    gate.set()
    await eventually(lambda: tracker.get('cancelled').state == DeliveryState.CONFIRMED)
    assert tracker.get('cancelled').state == DeliveryState.CONFIRMED


@pytest.mark.asyncio
@pytest.mark.parametrize('error,state,exception', [
    (BridgeError('send', dispatched=False), DeliveryState.FAILED, BridgeError),
    (BridgeError('send'), DeliveryState.UNKNOWN, DeliveryUncertainError),
    (SessionClosedError(), DeliveryState.UNKNOWN, DeliveryUncertainError),
    (ValueError('invalid local input'), DeliveryState.FAILED, ValueError),
])
async def test_delivery_distinguishes_local_failures_and_uncertain_dispatch(error, state, exception):
    tracker = DeliveryTracker()
    send = AsyncMock(side_effect=error)
    with pytest.raises(exception):
        await tracker.send(send, 'id')
    assert tracker.get('id').state == state
    with pytest.raises(DeliveryUncertainError):
        await tracker.send(send, 'id')
    send.assert_awaited_once()


@pytest.mark.asyncio
async def test_missing_message_id_is_not_reported_as_confirmed():
    tracker = DeliveryTracker()
    with pytest.raises(DeliveryUncertainError) as error:
        await tracker.send(AsyncMock(return_value={'ack': 1}), 'missing-id')
    assert error.value.operation_id == 'missing-id'
    assert tracker.get('missing-id').state == DeliveryState.UNKNOWN


@pytest.mark.asyncio
@pytest.mark.parametrize('ident', ['', 'x' * 129, 123])
async def test_invalid_operation_id_does_not_dispatch(ident):
    send = AsyncMock()
    with pytest.raises(ValueError):
        await DeliveryTracker().send(send, ident)
    send.assert_not_called()


@pytest.mark.asyncio
async def test_durable_ledgers_isolate_sessions_and_refresh_confirmations(tmp_path):
    path = tmp_path / 'ledger.db'
    first, observer, other = DeliveryTracker(path, 'one'), DeliveryTracker(path, 'one'), DeliveryTracker(path, 'two')
    try:
        send = AsyncMock(return_value={'id': 'one-message'})
        await first.send(send, 'same')
        assert (await observer.send(send, 'same')).message_id == 'one-message'
        await other.send(send, 'same')
        assert send.await_count == 2
    finally:
        first.close()
        observer.close()
        other.close()


@pytest.mark.asyncio
async def test_all_message_senders_use_delivery_tracking_without_affecting_presence():
    context = ready_context(sendImage_=AsyncMock(return_value={'id': 'image'}), sendSeen_=AsyncMock(return_value=True))
    service = ServiceHub(context).messages
    receipt = await service.send_image('chat', 'data', operation_id='image-op')
    assert (await service.send_image('chat', 'data', operation_id='image-op')) == receipt
    context.sendImage_.assert_awaited_once()
    assert await service.send_seen('chat') is True


@pytest.mark.asyncio
async def test_service_blocks_operations_until_ready_and_reconciliation_requires_outgoing_message():
    context = ready_context(getMessageById_=AsyncMock(return_value={'id': 'incoming', 'fromMe': False}))
    service = ServiceHub(context).messages
    with pytest.raises(ValueError, match='outgoing'):
        await service.reconcile('operation', 'incoming')
    context.lifecycle.transition(SessionState.RECONNECTING)
    with pytest.raises(SessionNotReadyError):
        await service.get_message('incoming')


@pytest.mark.asyncio
async def test_dispatcher_close_completes_waiters_and_is_idempotent():
    emitter, started, gate = EventEmitter(), asyncio.Event(), asyncio.Event()
    async def blocked(value):
        started.set()
        await gate.wait()
    emitter.on('event', blocked)
    dispatcher = EventDispatcher(emitter)
    first = asyncio.create_task(dispatcher.submit('event', 1))
    await started.wait()
    second = asyncio.create_task(dispatcher.submit('event', 2))
    await asyncio.sleep(0)
    await dispatcher.close()
    await asyncio.wait_for(asyncio.gather(first, second), 1)
    await dispatcher.close()
    with pytest.raises(SessionClosedError):
        await dispatcher.submit('event', 3)


@pytest.mark.asyncio
async def test_incompatible_latest_runtime_reloads_once_before_bundled_fallback():
    client = HostLayer.__new__(HostLayer)
    client.logger, client.session, client.wa_js_version, client.options = Mock(), 'test', None, {}
    client.page = Mock(reload=AsyncMock())
    client._evaluate_js = AsyncMock(return_value=False)
    client._onLoadingScreen = AsyncMock()
    client._inject_runtime = AsyncMock(side_effect=[RuntimeCompatibilityError(), None])
    client.ThreadsafeBrowser = SimpleNamespace(create_task=direct, page_wait_for_function=AsyncMock(), add_script_tag=AsyncMock())
    with patch('WPP_Whatsapp.api.layers.HostLayer.getWaJs', AsyncMock(return_value={'content': '// latest'})), \
         patch('WPP_Whatsapp.api.helpers.wa_version._bundled_wajs', return_value={'content': '// bundled'}):
        assert await client.inject_api()
    assert [call.args[0]['content'] for call in client._inject_runtime.call_args_list] == ['// latest', '// bundled']
    client.page.reload.assert_awaited_once()
    assert not client._runtime_reloading


@pytest.mark.asyncio
async def test_explicit_runtime_never_silently_falls_back():
    client = HostLayer.__new__(HostLayer)
    client.logger, client.session, client.wa_js_version, client.options = Mock(), 'test', '4.6.1', {}
    client.page = Mock(reload=AsyncMock())
    client._evaluate_js = AsyncMock(return_value=False)
    client._inject_runtime = AsyncMock(side_effect=RuntimeCompatibilityError())
    client.ThreadsafeBrowser = SimpleNamespace(page_wait_for_function=AsyncMock())
    with patch('WPP_Whatsapp.api.layers.HostLayer.getWaJs', AsyncMock(return_value={'content': '// explicit'})):
        with pytest.raises(RuntimeCompatibilityError):
            await client.inject_api()
    client.page.reload.assert_not_called()


@pytest.mark.asyncio
async def test_runtime_capabilities_must_be_present_before_operations():
    bridge = JavascriptBridge(SimpleNamespace(page_evaluate=AsyncMock(return_value={'ready': True, 'history': False})), object())
    with pytest.raises(RuntimeCompatibilityError):
        await bridge.capabilities()
    with pytest.raises(BridgeError) as error:
        await bridge.call('unknown-command')
    assert not error.value.dispatched


@pytest.mark.asyncio
async def test_native_client_closes_after_startup_failure():
    client = AsyncClient()
    browser = SimpleNamespace(open=AsyncMock(), close=AsyncMock(), page=Mock(), loop=asyncio.get_running_loop())
    context = SimpleNamespace(start=AsyncMock(side_effect=RuntimeError('startup')), _shutdown_session=AsyncMock(), options={}, onStateChange=Mock())
    with patch('WPP_Whatsapp.core.client.AsyncBrowser', return_value=browser), \
         patch('WPP_Whatsapp.core.client.session_directory', return_value='test-profile'), \
         patch('WPP_Whatsapp.api.Whatsapp.Whatsapp', return_value=context):
        with pytest.raises(RuntimeError, match='startup'):
            await client.connect()
    browser.close.assert_awaited_once()
    context._shutdown_session.assert_awaited_once()
    assert client.state == SessionState.FAILED
    await client.close()
    assert client.state == SessionState.CLOSED


def test_every_registered_command_is_referenced_and_legacy_surface_is_preserved():
    from pathlib import Path
    import ast
    references = set()
    for path in (Path(__file__).parents[1] / 'WPP_Whatsapp').rglob('*.py'):
        for call in ast.walk(ast.parse(path.read_text(encoding='utf-8'))):
            if (isinstance(call, ast.Call) and isinstance(call.func, ast.Attribute)
                    and (call.func.attr in ('_evaluate_js', '_evaluate_js_sync')
                         or (call.func.attr == 'call' and isinstance(call.func.value, ast.Name)
                             and call.func.value.id == 'bridge'))
                    and call.args and isinstance(call.args[0], ast.Constant)):
                references.add(call.args[0].value)
    assert references == set(COMMANDS)
    assert inspect.iscoroutinefunction(Whatsapp.sendText_)
    assert callable(Whatsapp.sendText) and callable(Whatsapp.onMessage)


@pytest.mark.asyncio
async def test_concurrent_connect_only_opens_one_native_browser():
    client = AsyncClient(wait_for_login=False)
    browser = SimpleNamespace(open=AsyncMock(), close=AsyncMock(), page=Mock(), loop=asyncio.get_running_loop())
    context = SimpleNamespace(start=AsyncMock(), _shutdown_session=AsyncMock(), options={},
                              onStateChange=Mock(), isClosed=False)
    with patch('WPP_Whatsapp.core.client.AsyncBrowser', return_value=browser), \
         patch('WPP_Whatsapp.core.client.session_directory', return_value='test-profile'), \
         patch('WPP_Whatsapp.api.Whatsapp.Whatsapp', return_value=context):
        first, second = await asyncio.gather(client.connect(), client.connect())
    assert first is second is client
    browser.open.assert_awaited_once()
    context.start.assert_awaited_once()
    await client.close()


@pytest.mark.asyncio
async def test_native_connection_events_block_services_during_reconnect():
    client = AsyncClient()
    context = ready_context(isAuthenticated=AsyncMock(return_value=True), isInsideChat=AsyncMock(return_value=True))
    context.isClosed = False
    client._context = context
    await client._connection_changed('DISCONNECTED')
    assert client.state == SessionState.RECONNECTING
    await client._connection_changed('CONNECTED')
    assert client.state == SessionState.READY
    await client._connection_changed('UNPAIRED')
    assert client.state == SessionState.WAITING_QR


@pytest.mark.asyncio
async def test_cancelled_legacy_async_start_waits_for_launch_before_cleanup():
    import threading
    from WPP_Whatsapp import Create
    factory = Create.__new__(Create)
    started, release = threading.Event(), threading.Event()
    order = []
    def launch():
        started.set()
        release.wait(2)
        order.append('owned')
    async def close():
        order.append('closed')
    factory._Create__create, factory.close = launch, close
    task = asyncio.create_task(factory.create())
    assert await asyncio.to_thread(started.wait, 1)
    task.cancel()
    await asyncio.sleep(0)
    release.set()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert order == ['owned', 'closed']
