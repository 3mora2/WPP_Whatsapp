"""Latest-release downloads, fallback, explicit selection and pagination."""
import asyncio
from unittest.mock import AsyncMock, Mock, patch

import aiohttp
import pytest

from WPP_Whatsapp.api.helpers.wa_version import (
    getWaJs, WA_JS_RELEASES_URL, WA_JS_NIGHTLY_URL,
)


def release(tag='v4.6.1', **kwargs):
    return {'tag_name': tag, 'assets': [{'name': 'wppconnect-wa.js',
            'browser_download_url': f'https://example.test/{tag}.js'}], **kwargs}


def response(payload=None, content='// runtime', error=None, content_type='text/javascript'):
    obj = Mock()
    obj.json = AsyncMock(return_value=payload)
    obj.text = AsyncMock(return_value=content)
    obj.raise_for_status.side_effect = error
    obj.content_type = content_type
    manager = Mock()
    manager.__aenter__ = AsyncMock(return_value=obj)
    manager.__aexit__ = AsyncMock(return_value=False)
    return manager


@pytest.fixture
def network():
    session = Mock()
    manager = Mock()
    manager.__aenter__ = AsyncMock(return_value=session)
    manager.__aexit__ = AsyncMock(return_value=False)
    with patch('WPP_Whatsapp.api.helpers.wa_version.aiohttp.ClientSession', return_value=manager):
        yield session


@pytest.mark.parametrize('version', [None, 'latest'])
@pytest.mark.asyncio
async def test_latest_is_downloaded_before_bundled(network, version):
    network.get.side_effect = [response(release()), response(content='// newest')]
    with patch('WPP_Whatsapp.api.helpers.wa_version._bundled_wajs') as bundled:
        assert await getWaJs(version) == {'content': '// newest'}
        bundled.assert_not_called()
    assert [c.args[0] for c in network.get.call_args_list] == [
        WA_JS_RELEASES_URL + '/latest', 'https://example.test/v4.6.1.js']


@pytest.mark.parametrize('error', [
    aiohttp.ClientConnectionError('offline'), asyncio.TimeoutError(),
    aiohttp.ClientResponseError(Mock(real_url='https://example.test'), (), status=403),
])
@pytest.mark.parametrize('failure_stage', ['metadata', 'download'])
@pytest.mark.asyncio
async def test_network_failures_use_bundled(network, error, failure_stage):
    network.get.side_effect = ([response(release())] if failure_stage == 'download' else []) + [error]
    with patch('WPP_Whatsapp.api.helpers.wa_version._bundled_wajs', return_value={'content': '// offline'}) as bundled:
        assert await getWaJs() == {'content': '// offline'}
        bundled.assert_called_once_with()


@pytest.mark.parametrize('metadata', [None, [], {}, release(assets=[]), release(assets=42),
                                      release(prerelease=True), release(draft=True)])
@pytest.mark.asyncio
async def test_unusable_latest_metadata_falls_back(network, metadata):
    network.get.return_value = response(metadata)
    with patch('WPP_Whatsapp.api.helpers.wa_version._bundled_wajs', return_value={'content': '// offline'}):
        assert await getWaJs() == {'content': '// offline'}
    assert network.get.call_count == 1


@pytest.mark.parametrize('content,content_type', [
    ('', 'text/javascript'), ('   ', 'text/plain'),
    ('<!DOCTYPE html><html>Error</html>', 'text/plain'),
    ('<html>Error</html>', 'text/html'), ('{"error": "rate limit"}', 'application/json'),
])
@pytest.mark.asyncio
async def test_invalid_download_falls_back(network, content, content_type):
    network.get.side_effect = [response(release()), response(content=content, content_type=content_type)]
    with patch('WPP_Whatsapp.api.helpers.wa_version._bundled_wajs', return_value={'content': '// offline'}):
        assert await getWaJs() == {'content': '// offline'}


@pytest.mark.asyncio
async def test_overall_timeout_falls_back():
    async def stalled(_):
        await asyncio.sleep(60)
    with patch('WPP_Whatsapp.api.helpers.wa_version._remote_wajs', side_effect=stalled), \
            patch('WPP_Whatsapp.api.helpers.wa_version.WA_JS_FETCH_TIMEOUT', .01), \
            patch('WPP_Whatsapp.api.helpers.wa_version._bundled_wajs', return_value={'content': '// offline'}):
        assert await getWaJs() == {'content': '// offline'}


@pytest.mark.asyncio
async def test_explicit_constraint_selects_highest_matching_asset(network):
    network.get.side_effect = [response([
        release('nightly'), release('v4.6.1', assets=[]), release('v4.5.0'),
        release('v4.5.2'), release('v5.0.0'), release('v4.5.9', draft=True),
    ]), response()]
    await getWaJs('^4.5.0')
    assert network.get.call_args.args[0] == 'https://example.test/v4.5.2.js'


@pytest.mark.asyncio
async def test_old_explicit_version_uses_next_page(network):
    network.get.side_effect = [response([release('v4.6.1')] * 100),
                               response([release('v3.19.3')]), response()]
    await getWaJs('3.19.3')
    assert network.get.call_args_list[1].kwargs['params']['page'] == 2
    assert network.get.call_args.args[0] == 'https://example.test/v3.19.3.js'


@pytest.mark.asyncio
async def test_unavailable_explicit_version_is_not_substituted(network):
    network.get.return_value = response([release()])
    with pytest.raises(ValueError, match='No WA-JS release'):
        await getWaJs('1.0.0')
    assert network.get.call_count == 1


@pytest.mark.parametrize('version,url', [('nightly', WA_JS_NIGHTLY_URL),
                                       ('https://example.test/custom.js', 'https://example.test/custom.js')])
@pytest.mark.asyncio
async def test_explicit_failures_do_not_fall_back(network, version, url):
    network.get.side_effect = aiohttp.ClientConnectionError('offline')
    with pytest.raises(aiohttp.ClientConnectionError):
        await getWaJs(version)
    network.get.assert_called_once_with(url)


@pytest.mark.asyncio
async def test_cancellation_propagates():
    with patch('WPP_Whatsapp.api.helpers.wa_version._remote_wajs', side_effect=asyncio.CancelledError()):
        with pytest.raises(asyncio.CancelledError):
            await getWaJs()
