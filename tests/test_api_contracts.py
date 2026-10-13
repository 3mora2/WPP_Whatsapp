"""Source-backed API names plus executable argument/return contract checks."""
import ast
import asyncio
import inspect
import json
from pathlib import Path
import re
import shutil
import subprocess
from unittest.mock import AsyncMock, Mock

import pytest

from WPP_Whatsapp.api.Whatsapp import Whatsapp
from WPP_Whatsapp.core.commands import COMMANDS

ROOT = Path(__file__).parents[1]
CONTRACT = json.loads((Path(__file__).parent / 'fixtures/upstream_contract.json').read_text())


def test_upstream_public_method_coverage():
    methods = {name for names in CONTRACT['public_methods'].values() for name in names}
    assert not (methods - set(dir(Whatsapp)))


def test_all_wajs_calls_exist_in_upstream():
    missing = []
    for path in (ROOT / 'WPP_Whatsapp').rglob('*.py'):
        if path.name == 'wapi.py':
            continue
        for ns, method in re.findall(r'WPP\.(\w+)\.(\w+)\s*\(', path.read_text(encoding='utf-8')):
            if ns not in ('whatsapp', 'loader') and method not in CONTRACT['exports'].get(ns, []):
                missing.append(f'{path.name}: WPP.{ns}.{method}')
    assert not missing
    for source in COMMANDS.values():
        for ns, method in re.findall(r'WPP\.(\w+)\.(\w+)\s*\(', source):
            assert ns in ('whatsapp', 'loader') or method in CONTRACT['exports'].get(ns, []), (ns, method)


def test_sync_wrappers_match_async_signatures():
    for path in (ROOT / 'WPP_Whatsapp/api').rglob('*.py'):
        if path.name == 'wapi.py':
            continue
        for call in ast.walk(ast.parse(path.read_text(encoding='utf-8'))):
            if not (isinstance(call, ast.Call) and isinstance(call.func, ast.Attribute)
                    and call.func.attr == 'run_threadsafe' and call.args):
                continue
            target = call.args[0]
            args = call.args[1:]
            if isinstance(target, ast.Call):
                args, target = target.args, target.func
            if (isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name)
                    and target.value.id == 'self' and hasattr(Whatsapp, target.attr)
                    and not any(isinstance(a, ast.Starred) for a in args)):
                inspect.signature(getattr(Whatsapp, target.attr)).bind(object(), *([None] * len(args)))


def test_api_browser_calls_target_the_session_page():
    operations = {'page_evaluate', 'page_evaluate_sync', 'page_wait_for_function',
                  'page_wait_for_selector', 'page_wait_for_function_sync', 'expose_function', 'add_script_tag', 'goto'}
    for path in (ROOT / 'WPP_Whatsapp/api').rglob('*.py'):
        if path.name == 'wapi.py':
            continue
        for call in ast.walk(ast.parse(path.read_text(encoding='utf-8'))):
            if isinstance(call, ast.Call) and isinstance(call.func, ast.Attribute) and call.func.attr in operations:
                assert any(k.arg == 'page' for k in call.keywords), f'{path.name}:{call.lineno}'


def test_all_browser_expressions_are_javascript():
    node = shutil.which('node')
    if not node:
        pytest.fail('Node.js is required for JavaScript contract validation')
    expressions = [{'location': key, 'expr': source} for key, source in COMMANDS.items()]
    for path in (ROOT / 'WPP_Whatsapp').rglob('*.py'):
        if path.name == 'wapi.py':
            continue
        for call in ast.walk(ast.parse(path.read_text(encoding='utf-8'))):
            if (isinstance(call, ast.Call) and isinstance(call.func, ast.Attribute)
                    and call.func.attr in ('page_evaluate', 'page_evaluate_sync',
                                          'page_wait_for_function', 'page_wait_for_function_sync')
                    and call.args and isinstance(call.args[0], ast.Constant)
                    and isinstance(call.args[0].value, str)):
                expressions.append({'location': f'{path.name}:{call.lineno}', 'expr': call.args[0].value})
    script = r"""
      const fs = require('fs'); const failures = [];
      for (const item of JSON.parse(fs.readFileSync(0, 'utf8'))) {
        try { new Function(`return (${item.expr.replace(/;\s*$/, '')});`); }
        catch (error) { failures.push(item.location + ': ' + error.message); }
      }
      process.stdout.write(JSON.stringify(failures));
    """
    result = subprocess.run([node, '-e', script], input=json.dumps(expressions),
                            text=True, capture_output=True, timeout=30)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == []


class ExecutingBridge:
    def __init__(self):
        self.calls = []

    async def page_evaluate(self, expr, arg=None, page=None):
        node = shutil.which('node')
        assert node, 'Node.js is required for executable API contracts'
        result = await asyncio.to_thread(subprocess.run,
            [node, str(Path(__file__).parent / 'js/api_contract.cjs')],
            input=json.dumps({'expr': expr, 'arg': arg}), text=True, capture_output=True, timeout=20)
        assert result.returncode == 0, result.stderr
        payload = json.loads(result.stdout)
        self.calls.extend(payload['calls'])
        return payload.get('value')


CASES = [
    ('getProducts_', ['biz@c.us', 10], 'catalog.getProducts', ['biz@c.us', 10]),
    ('getProductById_', ['biz@c.us', 'p1'], 'catalog.getProductById', ['biz@c.us', 'p1']),
    ('getCollections_', ['biz@c.us', 10, 20], 'catalog.getCollections', ['biz@c.us', 10, 20]),
    ('createCollection_', ['set', ['p1']], 'catalog.createCollection', ['set', ['p1']]),
    ('delProducts_', [['p1']], 'catalog.delProducts', [['p1']]),
    ('editProduct_', ['p1', {'name': 'new'}], 'catalog.editProduct', ['p1', {'name': 'new'}]),
    ('deleteCollection_', ['c1'], 'catalog.deleteCollection', ['c1']),
    ('editCollection_', ['c1', {'collectionName': 'new'}], 'catalog.editCollection', ['c1', {'collectionName': 'new'}]),
    ('addProductImage_', ['p1', 'data:image/png;base64,AA=='], 'catalog.addProductImage', ['p1', 'data:image/png;base64,AA==']),
    ('changeProductImage_', ['p1', 'data:image/png;base64,AA=='], 'catalog.changeProductImage', ['p1', 'data:image/png;base64,AA==']),
    ('removeProductImage_', ['p1', 1], 'catalog.removeProductImage', ['p1', 1]),
    ('setProductVisibility_', ['p1', False], 'catalog.setProductVisibility', ['p1', False]),
    ('updateCartEnabled_', [False], 'catalog.updateCartEnabled', [False]),
    ('getBusinessProfilesProducts_', ['123'], 'WAPI.getBusinessProfilesProducts', ['123']),
    ('getBusinessProfile_', ['123@c.us'], 'contact.getBusinessProfile', ['123@c.us']),
    ('createCommunity_', ['name', 'desc', ['1@g.us']], 'community.create', ['name', 'desc', ['1@g.us']]),
    ('promoteCommunityParticipant_', ['1@g.us', '2@c.us'], 'community.promoteParticipants', ['1@g.us', ['2@c.us']]),
    ('demoteCommunityParticipant_', ['1@g.us', ['2@c.us']], 'community.demoteParticipants', ['1@g.us', ['2@c.us']]),
    ('createNewsletter_', ['name', {'description': 'desc'}], 'newsletter.create', ['name', {'description': 'desc'}]),
    ('editNewsletter_', ['1@newsletter', {'name': 'new'}], 'newsletter.edit', ['1@newsletter', {'name': 'new'}]),
    ('getProfileName_', [], 'profile.getMyProfileName', []),
    ('setProfileName_', ['name'], 'profile.setMyProfileName', ['name']),
    ('getProfileStatus_', [], 'profile.getMyStatus', []),
    ('setProfileStatus_', ['about'], 'profile.setMyStatus', ['about']),
    ('editBusinessProfile_', [{'description': 'desc'}], 'profile.editBusinessProfile', [{'description': 'desc'}]),
    ('setProfilePic_', ['data:image/png;base64,AA=='], 'profile.setMyProfilePicture', ['data:image/png;base64,AA==']),
    ('setGroupIcon_', ['1@g.us', 'data:image/png;base64,AA=='], 'group.setIcon', ['1@g.us', 'data:image/png;base64,AA==']),
    ('setMessagesAdminsOnly_', ['1@g.us', True], 'group.setProperty', ['1@g.us', 'announcement', True]),
    ('approveGroupMembershipRequest_', ['1@g.us', ['2@lid']], 'group.approve', ['1@g.us', ['2@lid']]),
    ('rejectGroupMembershipRequest_', ['1@g.us', ['2@lid']], 'group.reject', ['1@g.us', ['2@lid']]),
    ('promoteParticipant_', ['1@g.us', ['2@lid']], 'group.promoteParticipants', ['1@g.us', ['2@lid']]),
    ('demoteParticipant_', ['1@g.us', ['2@lid']], 'group.demoteParticipants', ['1@g.us', ['2@lid']]),
    ('addNewLabel_', ['name', {'labelColor': 5}], 'labels.addNewLabel', ['name', {'labelColor': 5}]),
    ('getLabelById_', ['1'], 'labels.getLabelById', ['1']),
    ('deleteLabel_', ['1'], 'labels.deleteLabel', ['1']),
    ('deleteAllLabels_', [], 'labels.deleteAllLabels', []),
    ('addOrRemoveLabels_', [['1@c.us'], [{'labelId': '1', 'type': 'add'}]], 'labels.addOrRemoveLabels', [['1@c.us'], [{'labelId': '1', 'type': 'add'}]]),
    ('getListMutes_', ['all'], 'WAPI.getListMute', ['all']),
    ('getAllChatsWithMessages_', [False], 'WAPI.getAllChatsWithMessages', [False]),
    ('sendMute_', ['123', 5, 'hours'], 'WAPI.sendMute', ['123@c.us', 5, 'hours']),
    ('setLimit_', ['maxMediaSize', 123], 'conn.setLimit', ['maxMediaSize', 123]),
    ('sendPixKey_', ['123', {'key': 'abc'}], 'chat.sendPixKeyMessage', ['123@c.us', {'key': 'abc'}, {'waitForAck': True}]),
    ('sendPollMessage_', ['123', 'question', ['yes', 'no']], 'chat.sendCreatePollMessage', ['123@c.us', 'question', ['yes', 'no'], {}]),
    ('sendOrderMessage_', ['123', [{'type': 'custom', 'name': 'item', 'price': 200, 'qnt': 1}]], 'chat.sendChargeMessage', ['123@c.us', [{'type': 'custom', 'name': 'item', 'price': 200, 'qnt': 1}], {}]),
    ('sendOrderMessage_', ['123', [{'productId': 'p1', 'quantity': 2}]], 'chat.sendChargeMessage', ['123@c.us', [{'id': 'p1', 'qnt': 2, 'type': 'product'}], {}]),
    ('sendImageFromBase64_', ['123', 'data:image/png;base64,AA==', '', '', None, None, None, {'quotedMsg': 'reply'}], 'chat.sendFileMessage', ['123@c.us', 'data:image/png;base64,AA==', {'quotedMsg': 'reply', 'type': 'image', 'waitForAck': True, 'detectMentioned': True}]),
    ('sendLocation_', ['123', {'lat': 12, 'lng': 30, 'title': 'here'}], 'chat.sendLocationMessage', ['123@c.us', {'lat': 12, 'lng': 30, 'title': 'here'}]),
    ('createList_', ['Family', ['123'], 3], 'lists.create', ['Family', ['123@c.us'], 3]),
    ('getAllLists_', [], 'lists.list', []),
    ('addChatsToList_', ['1', ['123']], 'lists.addChats', ['1', ['123@c.us']]),
    ('removeChatsFromList_', ['1', ['123']], 'lists.removeChats', ['1', ['123@c.us']]),
    ('renameList_', ['1', 'new'], 'lists.rename', ['1', 'new']),
    ('deleteList_', ['1'], 'lists.remove', ['1']),
    ('getMessagesFromRowId_', [{'minRowId': 123, 'limit': 5}], 'indexdb.getMessagesFromRowId', [{'minRowId': 123, 'limit': 5}]),
    ('getAutoDownloadSettings_', [], 'conn.getAutoDownloadSettings', []),
    ('setAutoDownloadSettings_', [{'photos': False}], 'conn.setAutoDownloadSettings', [{'photos': False}]),
    ('sendReactionToMessage_', ['msg', False], 'chat.sendReactionToMessage', ['msg', False]),
    ('markPlayed_', ['msg'], 'chat.markPlayed', ['msg']),
    ('stopRecording_', ['123'], 'chat.markIsPaused', ['123@c.us']),
]


@pytest.mark.parametrize('method,args,api,expected', CASES, ids=[c[0] for c in CASES])
@pytest.mark.asyncio
async def test_executable_argument_and_result_contract(method, args, api, expected):
    client = Whatsapp.__new__(Whatsapp)
    bridge = ExecutingBridge()
    client.ThreadsafeBrowser = bridge
    client.page = Mock()
    client.logger = Mock()
    client.session = 'contract-test'
    result = await getattr(client, method)(*args)
    assert any(c == {'name': api, 'args': expected} for c in bridge.calls), bridge.calls
    assert result is not None, f'{method} discarded its result'
