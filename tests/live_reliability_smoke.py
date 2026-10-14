"""Opt-in real-account recovery/ACK reads. Never sends or logs message contents.

Close other library tests using this profile first. --force-page-close closes
only this script's own page to exercise automatic recovery.
"""

import argparse
import asyncio
import json
import logging
import sys
from importlib.metadata import version
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from WPP_Whatsapp import AsyncClient, SessionState  # noqa: E402


async def run(args):
    logging.getLogger("WPP_Whatsapp").setLevel(logging.WARNING)
    report = {"version": version("WPP_Whatsapp"), "sends_performed": 0}
    client = AsyncClient(
        args.session,
        token_directory=str(ROOT / "tokens"),
        autoClose=0,
        logQR=False,
        reconnectAttempts=2,
        reconnectInitialDelay=0.2,
        reconnectAttemptTimeout=45,
        deliveryStore=str(args.delivery_store),
    )
    remove = client.events.on_message(lambda message: None)
    try:
        await asyncio.wait_for(client.connect(), 120)
        report["ready"] = client.state == SessionState.READY
        context = client._context
        chat = await client.browser.page_evaluate(
            """async () => {
            const groups = await WPP.chat.list({onlyGroups:true,count:100});
            return groups.find(c => !c.unreadCount && c.lastReceivedKey &&
                c.groupMetadata?.groupType !== 'COMMUNITY')?.id.toString();
        }""",
            page=context.page,
        )
        if not chat:
            raise RuntimeError("No already-read group is available")
        messages = await client.messages.get_messages(chat, {"count": 25})
        report["history_count"] = len(messages)
        report["complete_ids"] = bool(messages) and all(
            isinstance(m.get("id"), str) and m["id"] for m in messages
        )
        retrieved = await client.messages.get_message(messages[0]["id"])
        report["lookup_matches"] = retrieved.get("id") == messages[0]["id"]
        assert report["complete_ids"] and report["lookup_matches"]
        if args.force_page_close:
            source = client.events._source
            await client.browser.page.close()

            async def recovered():
                while (
                    not client.diagnostics()["recovery"]["successes"]
                    or client.state != SessionState.READY
                ):
                    await asyncio.sleep(0.1)

            await asyncio.wait_for(recovered(), 100)
            report["recovery"] = client.diagnostics()["recovery"]
            report["subscriptions_rebound"] = client.events._source is not source
            report["history_after_recovery"] = len(
                await client.messages.get_messages(chat, {"count": 5})
            )
            assert report["subscriptions_rebound"] and report["history_after_recovery"]
        if args.existing_operation:
            status = await client.messages.delivery_status(args.existing_operation)
            report["existing_ack"] = status["ack"]
            report["existing_delivered"] = status["delivered"]
            report["existing_read"] = status["read"]
            await client.messages.wait_for_delivery(
                args.existing_operation, target="server", timeout=5
            )
            report["ack_wait_without_send"] = True
    finally:
        remove()
        await client.close()
        report["closed"] = client.state == SessionState.CLOSED
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(json.dumps(report), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--session", default="live-smoke-81-84")
    parser.add_argument("--force-page-close", action="store_true")
    parser.add_argument(
        "--existing-operation", help="Already recorded operation to inspect; never sent again"
    )
    parser.add_argument(
        "--delivery-store",
        type=Path,
        default=ROOT / "tokens/.deliveries/live-mcp-development.sqlite3",
    )
    parser.add_argument("--report", type=Path, default=ROOT / "archive/reliability-live-2.3.0.json")
    asyncio.run(run(parser.parse_args()))
