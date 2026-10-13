"""Manual, read-only WhatsApp regression test using the real library.

Run: .venv/Scripts/python.exe -u tests/live_whatsapp_smoke.py
Scan the QR code in the new browser, then arrange an incoming group message.
No messages are sent; reports contain counts and checks, never message bodies.
"""
import argparse
import hashlib
import json
import logging
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from WPP_Whatsapp import Create  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--session', default='live-smoke-81-84')
    parser.add_argument('--chat', help='Optional group chat ID for the history test')
    args = parser.parse_args()
    output = ROOT / 'archive/live-whatsapp-report.json'
    output.parent.mkdir(exist_ok=True)
    lock = threading.RLock()
    report = {'started': datetime.now(timezone.utc).isoformat(), 'stage': 'opening_browser',
              'history': [], 'incoming_groups': [], 'sends_performed': 0}

    def save():
        with lock:
            temporary = output.with_suffix('.tmp')
            temporary.write_text(json.dumps(report, indent=2), encoding='utf-8')
            temporary.replace(output)

    def emit(value):
        print(json.dumps(value), flush=True)
        save()

    logging.getLogger('WPP_Whatsapp').setLevel(logging.WARNING)
    save()
    factory = Create(session=args.session, folderNameToken=str(ROOT / 'tokens'),
                     waitForLogin=False, autoClose=0, logQR=False,
                     headless=False, version=None, wa_js_version=None,
                     close_already_profile=False, check_open_dir=True)
    client = factory.start()
    browser = client.ThreadsafeBrowser
    report['stage'] = 'waiting_for_login'
    emit({'stage': report['stage'], 'report': str(output)})

    async def ready():
        return await browser.page_evaluate('''() => ({
          wpp: Boolean(window.WPP), ready: Boolean(window.WPP?.isReady),
          registered: window.WPP?.conn.isRegistered(),
          mainLoaded: window.WPP?.conn.isMainLoaded(),
          mainReady: window.WPP?.conn.isMainReady(),
          listener: Boolean(window.onMessage?.exposed),
          bridge: Boolean(window.WAPI?._wppWhatsappReady),
          whatsapp: window.Debug?.VERSION, wajs: window.WPP?.version
        })''', page=client.page)

    while not client.isClosed:
        state = browser.run_threadsafe(ready(), timeout_=15)
        if state != report.get('readiness'):
            report['readiness'] = state
            emit({'readiness': state})
        if all(state.get(key) for key in ('ready', 'registered', 'mainReady', 'listener', 'bridge')):
            break
        time.sleep(2)
    if client.isClosed:
        report['stage'] = 'closed_before_login'
        emit({'stage': report['stage']})
        return

    listener_started = time.time()
    async def runtime():
        return await browser.page_evaluate('''() => ({wajs:WPP.version,
          whatsapp:window.Debug?.VERSION, bridge:WAPI._wppWhatsappReady})''', page=client.page)
    report['runtime'] = browser.run_threadsafe(runtime(), timeout_=15)
    report['stage'] = 'testing'
    emit({'stage': 'logged_in', 'runtime': report['runtime']})

    def incoming(message):
        group = message.get('isGroupMsg') or '@g.us' in str(message.get('chatId') or message.get('from'))
        if not group:
            return
        timestamp = message.get('timestamp') or message.get('t')
        # Ignore historical messages delivered during initial account sync.
        if not isinstance(timestamp, (int, float)) or timestamp < listener_started - 5:
            return
        message_id = message.get('id')
        entry = {'received_at': datetime.now(timezone.utc).isoformat(),
                 'id_present': isinstance(message_id, str) and bool(message_id),
                 'group_key': '@g.us_' in str(message_id), 'incoming': True}
        if entry['id_present']:
            entry['id_sha256'] = hashlib.sha256(message_id.encode()).hexdigest()
            try:
                retrieved = client.getMessageById(message_id, timeout=30)
                entry['lookup_by_callback_id'] = bool(retrieved and retrieved.get('id') == message_id)
            except Exception as error:
                entry['lookup_by_callback_id'] = False
                entry['lookup_error_type'] = type(error).__name__
        with lock:
            report['incoming_groups'].append(entry)
            report['issue_84_passed'] = any(m['id_present'] and m['group_key'] and
                                          m.get('lookup_by_callback_id') for m in report['incoming_groups'])
        emit({'incoming_group_callback': entry, 'issue_84_passed': report['issue_84_passed']})

    client.onMessage(incoming)
    emit({'listener_registered': True, 'waiting_for': 'real incoming group message'})

    async def choose_chat():
        return await browser.page_evaluate('''async () => {
          const groups = await WPP.chat.list({onlyGroups:true,count:100});
          const candidates = groups.filter(c => !c.unreadCount && c.lastReceivedKey &&
            c.groupMetadata?.groupType !== 'COMMUNITY');
          candidates.sort((a,b) => (b.t || 0) - (a.t || 0));
          return candidates.slice(0, 5).map(c => c.id.toString());
        }''', page=client.page)

    candidates = [args.chat] if args.chat else browser.run_threadsafe(choose_chat(), timeout_=30)
    chat_id = None
    report['candidate_checks'] = []
    for candidate in candidates:
        # Reproduce #81: open an already-read group, then fetch its history.
        try:
            client.openChat(candidate, timeout=30)
            time.sleep(2)
            sample = client.getMessages(candidate, {'count': 50}, timeout=60)
            report['candidate_checks'].append({'count': len(sample), 'opened': True})
            if sample:
                chat_id = candidate
                break
        except Exception as error:
            report['candidate_checks'].append({'error_type': type(error).__name__})
        save()
    if chat_id:
        report['history_chat_sha256'] = hashlib.sha256(chat_id.encode()).hexdigest()
        checks = [
            ('getMessages', lambda: client.getMessages(chat_id, {'count': 50}, timeout=90)),
            ('getAllMessagesInChat', lambda: client.getAllMessagesInChat(chat_id, True, False, timeout=90)),
            ('loadEarlierMessages', lambda: client.loadEarlierMessages(chat_id, timeout=90)),
            ('loadAndGetAllMessagesInChat', lambda: client.loadAndGetAllMessagesInChat(chat_id, True, False, timeout=90)),
        ]
        for name, call in checks:
            try:
                messages = call()
                entry = {'method': name, 'success': isinstance(messages, list),
                         'count': len(messages) if isinstance(messages, list) else None,
                         'all_ids_present': all(isinstance(m.get('id'), str) and bool(m['id'])
                                                for m in messages) if isinstance(messages, list) else False}
            except Exception as error:
                entry = {'method': name, 'success': False, 'error_type': type(error).__name__}
                print(f'{name} failed: {type(error).__name__}', flush=True)
            with lock:
                report['history'].append(entry)
            emit(entry)
        report['issue_81_passed'] = all(r['success'] and r['all_ids_present'] and
            (r['method'] == 'loadEarlierMessages' or r['count'] > 0) for r in report['history'])
    else:
        report['issue_81_passed'] = False
        report['history_blocker'] = 'No already-read group found; restart with --chat GROUP_ID'
    report['stage'] = 'waiting_for_group_message'
    emit({'issue_81_passed': report['issue_81_passed'], 'stage': report['stage']})

    while not client.isClosed:
        if report.get('issue_81_passed') and report.get('issue_84_passed') and report['stage'] != 'verified':
            report['stage'] = 'verified'
            emit({'stage': 'verified', 'issue_81_passed': True, 'issue_84_passed': True})
        time.sleep(2)
    report['stage'] = 'browser_closed'
    emit({'stage': report['stage']})


if __name__ == '__main__':
    main()
