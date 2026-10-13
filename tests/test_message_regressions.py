"""Offline regressions for GitHub #81 and #84; no WhatsApp session is used."""
import asyncio
import json
from pathlib import Path
import shutil
import subprocess
from unittest.mock import AsyncMock, Mock, patch

import pytest

from WPP_Whatsapp.api.Whatsapp import Whatsapp
from WPP_Whatsapp.api.helpers.wa_version import getWaJs
from WPP_Whatsapp.api.helpers.wapi import WAPI
from WPP_Whatsapp.api.layers.HostLayer import HostLayer
from WPP_Whatsapp.api.layers.ListenerLayer import ListenerLayer


@pytest.fixture
def client():
    obj = Whatsapp.__new__(Whatsapp)
    obj.ThreadsafeBrowser = Mock()
    obj.ThreadsafeBrowser.page_evaluate = AsyncMock(return_value=[])
    obj.page = Mock()
    return obj


@pytest.mark.parametrize('mapping,expected', [
    (None, '123@c.us'),
    ({}, '123@c.us'),
    ({'lid': None}, '123@c.us'),
    ({'lid': {}}, '123@c.us'),
    ({'lid': {'_serialized': '456@lid'}}, '456@lid'),
    ({'lid': '456@lid'}, '456@lid'),
    ({'phoneNumber': {'_serialized': '123@c.us'}}, '123@c.us'),
])
@pytest.mark.asyncio
async def test_sync_async_chat_mapping(client, mapping, expected):
    client.getPnLidEntry = Mock(return_value=mapping)
    client.getPnLidEntry_ = AsyncMock(return_value=mapping)
    assert await client.get_chat_id_('123') == expected
    assert client.get_chat_id('123') == expected


@pytest.mark.parametrize('chat_id', ['456@lid', '123-456@g.us', 'status@broadcast', '123@newsletter'])
@pytest.mark.asyncio
async def test_non_phone_ids_do_not_request_mapping(client, chat_id):
    client.getPnLidEntry_ = AsyncMock()
    assert await client.get_chat_id_(chat_id) == chat_id
    client.getPnLidEntry_.assert_not_called()


def test_fourteen_digit_phone():
    assert HostLayer.valid_chatId('12345678901234') == '12345678901234@c.us'


@pytest.mark.parametrize('method,args', [
    ('getMessages_', ('123',)),
    ('getAllMessagesInChat_', ('123',)),
    ('loadAndGetAllMessagesInChat_', ('123',)),
    ('loadEarlierMessages_', ('123',)),
    ('openChat_', ('123',)),
    ('openChatAt_', ('123', 'msg_id')),
])
@pytest.mark.asyncio
async def test_message_and_ui_methods_resolve_chat(client, method, args):
    client.getPnLidEntry_ = AsyncMock(return_value={'lid': {'_serialized': '456@lid'}})
    await getattr(client, method)(*args)
    call = client.ThreadsafeBrowser.page_evaluate.call_args
    arg = call.args[1]
    assert (arg['chatId'] if isinstance(arg, dict) else arg) == '456@lid'


@pytest.mark.asyncio
async def test_explicit_bundled_wajs_skips_network():
    with patch('WPP_Whatsapp.api.helpers.wa_version.aiohttp.ClientSession') as network:
        result = await getWaJs('bundled')
    network.assert_not_called()
    assert result['content'] == (Path(__file__).parents[1] / 'WPP_Whatsapp/js_lib/wppconnect-wa.js').read_text(encoding='utf-8')


@pytest.mark.asyncio
async def test_local_wajs_utf8(tmp_path):
    js = tmp_path / 'wppconnect-wa.js'
    js.write_text('// مرحبا', encoding='utf-8')
    assert await getWaJs(str(js)) == {'content': '// مرحبا'}


@pytest.mark.parametrize('version,url', [
    ('nightly', 'https://github.com/wppconnect-team/wa-js/releases/download/nightly/wppconnect-wa.js'),
    ('https://example.test/custom.js', 'https://example.test/custom.js'),
])
@pytest.mark.asyncio
async def test_explicit_wajs_downloads_and_http_errors(version, url):
    response = Mock()
    response.text = AsyncMock(return_value='// custom runtime')
    request = Mock()
    request.__aenter__ = AsyncMock(return_value=response)
    request.__aexit__ = AsyncMock(return_value=False)
    session = Mock()
    session.get.return_value = request
    manager = Mock()
    manager.__aenter__ = AsyncMock(return_value=session)
    manager.__aexit__ = AsyncMock(return_value=False)
    with patch('WPP_Whatsapp.api.helpers.wa_version.aiohttp.ClientSession', return_value=manager):
        assert await getWaJs(version) == {'content': '// custom runtime'}
        session.get.assert_called_once_with(url)
        response.raise_for_status.assert_called_once_with()
        response.raise_for_status.side_effect = RuntimeError('HTTP 404')
        with pytest.raises(RuntimeError, match='HTTP 404'):
            await getWaJs(version)


def test_wapi_single_source():
    js_dir = Path(__file__).parents[1] / 'WPP_Whatsapp/js_lib'
    assert WAPI == '\n'.join((js_dir / name).read_text(encoding='utf-8')
                            for name in ('wapi.js', 'message_compat.js'))


def test_javascript_message_regressions():
    node = shutil.which('node')
    if not node:
        pytest.skip('Node.js is required for the JavaScript regression harness')
    listener = ListenerLayer.__new__(ListenerLayer)
    listener.session = 'offline-test'
    listener.logger = Mock()
    listener.ThreadsafeBrowser = Mock()
    listener.ThreadsafeBrowser.page_evaluate = AsyncMock(return_value=True)
    listener.page = Mock()
    asyncio.run(listener._afterPageScriptInjectedListener())
    script = listener.ThreadsafeBrowser.page_evaluate.call_args.args[0]
    result = subprocess.run(
        [node, str(Path(__file__).parent / 'js/message_compat.cjs')],
        input=json.dumps(script), text=True, encoding='utf-8',
        capture_output=True, timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr
