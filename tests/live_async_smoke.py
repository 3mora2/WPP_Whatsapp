"""Read-only, native-async smoke test against an already signed-in profile.

Run only after closing any other library test using that profile.
Never sends messages, logs identifiers, or saves message bodies.
"""
import asyncio
import json
import logging
from pathlib import Path
import sys
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from WPP_Whatsapp import AsyncClient, SessionState  # noqa: E402


async def main():
    logging.getLogger('WPP_Whatsapp').setLevel(logging.WARNING)
    report = {'started': datetime.now(timezone.utc).isoformat(), 'sends_performed': 0}
    client = AsyncClient('live-smoke-81-84', token_directory=str(ROOT / 'tokens'), autoClose=0)
    try:
        await client.connect()
        report['native_owner_loop'] = client.browser.loop is asyncio.get_running_loop()
        report['state_ready'] = client.state == SessionState.READY
        context = client._context
        report['runtime'] = context.runtime_capabilities
        groups = await client.chats.list_chats({'onlyGroups': True, 'count': 100})
        # Library output shapes can differ; select through the current WA-JS
        # contract while exercising Python service history/lookup below.
        chat = await client.browser.page_evaluate('''async () => {
          const groups = await WPP.chat.list({onlyGroups:true,count:100});
          return groups.find(c => !c.unreadCount && c.lastReceivedKey &&
            c.groupMetadata?.groupType !== 'COMMUNITY')?.id.toString();
        }''', page=context.page)
        report['group_list_available'] = isinstance(groups, list)
        if not chat:
            raise RuntimeError('No already-read group is available')
        messages = await client.messages.get_messages(chat, {'count': 25})
        report['history_count'] = len(messages)
        report['all_ids_present'] = bool(messages) and all(isinstance(message.get('id'), str) and message['id'] for message in messages)
        retrieved = await client.messages.get_message(messages[0]['id'])
        report['lookup_matches'] = retrieved.get('id') == messages[0]['id']
        await client.reconnect()
        report['reconnect_ready'] = client.state == SessionState.READY
        report['reconnect_history_count'] = len(await client.messages.get_messages(chat, {'count': 5}))
    finally:
        await client.close()
        await client.close()
        report['closed'] = client.state == SessionState.CLOSED
        (ROOT / 'archive/architecture-live-async.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
        print(json.dumps(report), flush=True)


if __name__ == '__main__':
    asyncio.run(main())
