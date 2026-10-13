import asyncio
import base64
from io import BytesIO
import threading
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

from PIL import Image
import pytest

from WPP_Whatsapp.api.Whatsapp import Whatsapp
from WPP_Whatsapp.api.helpers.jsFunction import setInterval
from WPP_Whatsapp.api.helpers.decorators import async_to_sync
from WPP_Whatsapp.api.helpers.download_file import downloadFileToBase64
from WPP_Whatsapp.api.helpers.wa_version import getAvailableVersions, getLatestVersion, getPageContent
from WPP_Whatsapp.api.layers.ListenerLayer import ListenerLayer, HandelFunc
from WPP_Whatsapp.controllers.browser import ThreadsafeBrowser
from WPP_Whatsapp.controllers.initializer import Create
from WPP_Whatsapp.controllers.init_multi import MultiCreate
from WPP_Whatsapp.utils.batch_operations import BatchOperations, BatchStatus
from WPP_Whatsapp.utils.rate_limiter import RateLimiter
from tests.test_wajs_updates import response


def test_rate_limiter_can_be_created_without_a_current_loop():
    asyncio.run(asyncio.sleep(0))
    limiter = RateLimiter(calls=2, period=60)
    asyncio.run(limiter.acquire())
    assert limiter.remaining_calls == 1


@pytest.mark.parametrize('kwargs', [{'calls': 0}, {'period': 0}, {'delay_between_calls': -1}])
def test_invalid_rate_limiter_configuration(kwargs):
    with pytest.raises(ValueError):
        RateLimiter(**kwargs)


def test_ffmpeg_uses_path_and_cleans_temporary_files():
    from WPP_Whatsapp.utils.ffmpeg import get_ffmpeg_path, convertToMP4GIF
    with patch.dict('os.environ', {'FFMPEG_PATH': ''}), patch('shutil.which', return_value='ffmpeg-on-path'):
        assert get_ffmpeg_path() == 'ffmpeg-on-path'
    paths = []
    def convert(command, **kwargs):
        paths.append(Path(command[2]).parent)
        assert Path(command[2]).read_bytes() == b'input'
        Path(command[-1]).write_bytes(b'mp4-result')
    with patch('WPP_Whatsapp.utils.ffmpeg.get_ffmpeg_path', return_value='ffmpeg'), \
            patch('WPP_Whatsapp.utils.ffmpeg.subprocess.run', side_effect=convert):
        result = convertToMP4GIF(base64.b64encode(b'input').decode())
    assert base64.b64decode(result.split(',')[1]) == b'mp4-result'
    assert paths and not paths[0].exists()


@pytest.mark.asyncio
async def test_download_mime_parameters_are_normalized():
    reply = Mock(headers={'content-type': 'image/png; charset=utf-8'}, read=AsyncMock(return_value=b'png'))
    reply.raise_for_status = Mock()
    request = Mock(__aenter__=AsyncMock(return_value=reply), __aexit__=AsyncMock(return_value=False))
    session = Mock(get=Mock(return_value=request))
    manager = Mock(__aenter__=AsyncMock(return_value=session), __aexit__=AsyncMock(return_value=False))
    with patch('WPP_Whatsapp.api.helpers.download_file.aiohttp.ClientSession', return_value=manager):
        assert await downloadFileToBase64('https://example.test/image', ['image/png']) == 'data:image/png;base64,cG5n'


def test_async_to_sync_awaits_the_created_coroutine_once():
    loop = asyncio.new_event_loop()
    class Target:
        @async_to_sync
        async def work(self):
            return 'ok'
    obj = Target()
    obj.loop = loop
    try:
        assert obj.work() == 'ok'
    finally:
        loop.close()


@pytest.mark.asyncio
async def test_listener_sessions_are_isolated_and_disposable():
    clients = []
    for session in ['a', 'b']:
        listener = ListenerLayer.__new__(ListenerLayer)
        listener.session, listener.logger = session, Mock()
        ListenerLayer.__init__(listener)
        clients.append(listener)
    a, b = clients
    received_a, received_b = [], []
    dispose = a.on_message(received_a.append)
    b.on_message(received_b.append)
    bridge_a = HandelFunc('onMessage', 'a', Mock(), a._ListenerLayer__listenerEmitter)
    bridge_b = HandelFunc('onMessage', 'b', Mock(), b._ListenerLayer__listenerEmitter)
    bridge_a.handel_func({'id': 'a'})
    bridge_b.handel_func({'id': 'b'})
    assert received_a == [{'id': 'a'}] and received_b == [{'id': 'b'}]
    dispose()
    bridge_a.handel_func({'id': 'ignored'})
    assert received_a == [{'id': 'a'}]


@pytest.mark.asyncio
async def test_message_callback_runs_outside_browser_loop():
    listener = ListenerLayer.__new__(ListenerLayer)
    listener.session, listener.logger, listener.page = 'callback-thread', Mock(), Mock()
    ListenerLayer.__init__(listener)
    exposed = {}
    async def expose(name, callback, **kwargs):
        exposed[name] = callback
    listener.ThreadsafeBrowser = Mock(page_evaluate=AsyncMock(return_value=False),
                                     expose_function=AsyncMock(side_effect=expose))
    threads = []
    listener.onMessage(lambda msg: threads.append(threading.get_ident()))
    await listener._afterPageScriptInjectedListener()
    await exposed['onMessage']({'id': 'test'})
    assert len(threads) == 1 and threads[0] != threading.get_ident()


def test_filtered_participant_and_location_events():
    client = ListenerLayer.__new__(ListenerLayer)
    client.session, client.logger = 'filters', Mock()
    ListenerLayer.__init__(client)
    received = []
    dispose = client.onParticipantsChanged('1@g.us', received.append)
    emitter = client._ListenerLayer__listenerEmitter
    emitter.emit('onParticipantsChanged', {'groupId': '2@g.us'})
    emitter.emit('onParticipantsChanged', {'groupId': '1@g.us', 'author': '2@lid', 'participants': ['3@lid']})
    assert len(received) == 1 and received[0]['by'] == '2@lid' and received[0]['who'] == ['3@lid']
    dispose()
    received.clear()
    client.onLiveLocation(['2@lid'], received.append)
    emitter.emit('onLiveLocation', {'id': '3@lid'})
    emitter.emit('onLiveLocation', {'id': '2@lid'})
    assert received == [{'id': '2@lid'}]


@pytest.mark.asyncio
async def test_interval_runs_on_owning_loop_and_stops():
    calls = []
    interval = setInterval(asyncio.get_running_loop(), lambda: calls.append(1), .01)
    await asyncio.sleep(.03)
    interval.set()
    count = len(calls)
    await asyncio.sleep(.03)
    assert count > 0 and len(calls) == count
    assert interval.task.done()


def test_interval_cancelled_before_loop_starts_creates_no_task():
    loop = asyncio.new_event_loop()
    try:
        interval = setInterval(loop, lambda: None, 1)
        interval.set()
        loop.run_until_complete(asyncio.sleep(0))
        assert interval.task is None
    finally:
        loop.close()


@pytest.mark.asyncio
async def test_cross_loop_browser_calls_do_not_block_caller():
    worker = asyncio.new_event_loop()
    ready = threading.Event()
    def run():
        asyncio.set_event_loop(worker)
        ready.set()
        worker.run_forever()
    thread = threading.Thread(target=run)
    thread.start()
    ready.wait(2)
    browser = ThreadsafeBrowser.__new__(ThreadsafeBrowser)
    browser.loop = worker
    ticks = []
    async def work():
        await asyncio.sleep(.04)
        return threading.get_ident()
    async def heartbeat():
        for _ in range(3):
            await asyncio.sleep(.005)
            ticks.append(1)
    try:
        result, _ = await asyncio.gather(browser.create_task(work()), heartbeat())
        assert result == thread.ident and len(ticks) == 3
    finally:
        worker.call_soon_threadsafe(worker.stop)
        thread.join(2)
        worker.close()


@pytest.mark.asyncio
async def test_bulk_uses_async_methods_and_preserves_input_order():
    active, maximum = 0, 0
    async def send(to, text, options):
        nonlocal active, maximum
        active += 1
        maximum = max(maximum, active)
        await asyncio.sleep(.02 if to == 'a' else .001)
        active -= 1
        return {'id': to}
    client = SimpleNamespace(sendText_=send, sendText=Mock(side_effect=AssertionError('sync API used')))
    batch = BatchOperations(client)
    result = await batch.send_bulk_text([{'to': 'a', 'content': 'x'}, {'to': 'b', 'content': 'y'}], concurrency=2)
    assert maximum == 2 and result.successful == 2
    assert [item['to'] for item in result.results] == ['a', 'b']


@pytest.mark.asyncio
async def test_bulk_empty_member_selection_does_not_send_to_entire_group():
    client = SimpleNamespace(getGroupMembers_=AsyncMock(), sendText_=AsyncMock())
    result = await BatchOperations(client).send_bulk_to_group('1@g.us', 'hi', member_ids=[])
    assert result.total == 0
    client.getGroupMembers_.assert_not_called()
    client.sendText_.assert_not_called()


@pytest.mark.asyncio
async def test_bulk_invalid_input_is_rejected_before_sending():
    client = SimpleNamespace(sendText_=AsyncMock())
    batch = BatchOperations(client)
    with pytest.raises(ValueError):
        await batch.send_bulk_text([{'to': 'a', 'content': 'x'}, {'to': 'b'}])
    with pytest.raises(ValueError):
        await batch.send_bulk_text([], concurrency=0)
    client.sendText_.assert_not_called()


@pytest.mark.asyncio
async def test_bulk_records_failures_once_and_progress_exceptions_propagate():
    client = SimpleNamespace(sendText_=AsyncMock(side_effect=[{'id': 'a'}, ValueError('send failed')]))
    result = await BatchOperations(client).send_bulk_text([{'to': 'a', 'content': 'x'}, {'to': 'b', 'content': 'y'}])
    assert result.successful == result.failed == 1 and result.status == BatchStatus.PARTIAL
    client.sendText_ = AsyncMock(return_value={'id': 'a'})
    with pytest.raises(RuntimeError, match='progress failed'):
        await BatchOperations(client).send_bulk_text([{'to': 'a', 'content': 'x'}],
            on_progress=Mock(side_effect=RuntimeError('progress failed')))
    assert client.sendText_.await_count == 1


@pytest.mark.asyncio
async def test_ptt_retains_data_and_reply_id():
    client = Whatsapp.__new__(Whatsapp)
    client.page = Mock()
    client.ThreadsafeBrowser = Mock(page_evaluate=AsyncMock(return_value={'id': 'voice'}))
    data = 'data:audio/ogg;base64,AA=='
    await client.sendPtt_('123', data, quotedMessageId='reply')
    arg = client.ThreadsafeBrowser.page_evaluate.call_args.args[1]
    assert arg['base64'] == data and arg['quotedMessageId'] == 'reply'
    assert arg['to'] == '123@c.us'


@pytest.mark.asyncio
async def test_image_options_and_file_options_are_preserved():
    client = Whatsapp.__new__(Whatsapp)
    client.page = Mock()
    client.ThreadsafeBrowser = Mock(page_evaluate=AsyncMock(return_value={'id': 'media'}))
    options = {'quotedMsg': 'reply', 'messageId': 'custom'}
    await client.sendFile_('123', 'data:application/pdf;base64,AA==', options, 'caption')
    assert options == {'quotedMsg': 'reply', 'messageId': 'custom'}
    arg = client.ThreadsafeBrowser.page_evaluate.call_args.args[1]
    assert arg['options']['type'] == 'auto-detect'
    await client.sendImage_('123', 'data:image/png;base64,AA==', options={'foo': 'bar'})
    assert client.ThreadsafeBrowser.page_evaluate.call_args.args[1]['options'] == {'foo': 'bar'}


def test_explicit_zero_auto_close_does_not_start_a_timer():
    client = Whatsapp.__new__(Whatsapp)
    client.autoClose = 60
    client.startAutoClose(0)
    assert not hasattr(client, 'autoCloseInterval')


@pytest.mark.asyncio
async def test_animated_sticker_conversion_keeps_animation():
    images = [Image.new('RGB', (16, 16), color) for color in ('red', 'blue')]
    output = BytesIO()
    images[0].save(output, format='GIF', save_all=True, append_images=images[1:], duration=100, loop=0)
    data = 'data:image/gif;base64,' + base64.b64encode(output.getvalue()).decode()
    client = Whatsapp.__new__(Whatsapp)
    client.sendImageAsSticker_ = AsyncMock(return_value={'id': 'sticker'})
    await client.sendImageAsStickerGif_('123', data)
    converted = client.sendImageAsSticker_.call_args.args[1]
    with Image.open(BytesIO(base64.b64decode(converted.split(',')[1]))) as result:
        assert result.format == 'WEBP' and result.n_frames == 2


@pytest.mark.asyncio
async def test_version_listing_filters_non_html_and_reports_missing_version():
    session = Mock()
    session.get.return_value = response([{'name': 'README.md'}, {'name': 'not-a-version.html'}, {'name': '2.3000.1.html'}])
    assert [v.raw for v in await getAvailableVersions(session)] == ['2.3000.1']
    assert await getLatestVersion(session) == '2.3000.1'
    with pytest.raises(ValueError, match='Version not available'):
        await getLatestVersion(session, '<2.0.0')
    session.get.return_value = response([])
    with pytest.raises(ValueError, match='Version not available'):
        await getLatestVersion(session)


@pytest.mark.asyncio
async def test_page_content_fetches_version_list_once():
    page_response = response(content='<html>pinned</html>')
    session = Mock()
    session.get.side_effect = [response([{'name': '2.3000.1.html'}]), page_response]
    manager = Mock(__aenter__=AsyncMock(return_value=session), __aexit__=AsyncMock(return_value=False))
    with patch('WPP_Whatsapp.api.helpers.wa_version.aiohttp.ClientSession', return_value=manager):
        assert await getPageContent() == '<html>pinned</html>'
    assert session.get.call_count == 2


def test_factory_state_callback_handles_closed_or_absent_client():
    creator = Create.__new__(Create)
    creator.client, creator.waitLoginPromise, creator.onStateChange = None, None, Mock()
    creator._onStateChange('CLOSED')
    creator.onStateChange.assert_called_once_with('CLOSED')


def test_factory_context_manager_returns_started_client():
    creator = Create.__new__(Create)
    creator.start, creator.sync_close = Mock(return_value='client'), Mock()
    with creator as client:
        assert client == 'client'
    creator.sync_close.assert_called_once_with()


@pytest.mark.asyncio
async def test_multi_factory_constructs_without_initial_page_or_browser():
    browser = Mock()
    browser.page, browser.browser = None, None
    browser.loop = asyncio.get_running_loop()
    with patch('WPP_Whatsapp.controllers.init_multi.ThreadsafeBrowser', return_value=browser):
        creator = MultiCreate()
    assert creator.loop is browser.loop
    context = Mock(close=AsyncMock())
    client = Mock(_shutdown_session=AsyncMock())
    creator.Sessions['a'] = {'client': client, 'context': context, 'state': 'CONNECTED'}
    browser.create_task = AsyncMock(side_effect=lambda task: task)
    async def run(task):
        return await task
    browser.create_task.side_effect = run
    browser.close = AsyncMock()
    await creator.close_all_()
    client._shutdown_session.assert_awaited_once()
    context.close.assert_awaited_once()
    assert creator.Sessions['a']['state'] == 'CLOSED' and client.isClosed
