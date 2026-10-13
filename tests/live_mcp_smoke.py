"""Opt-in real-account MCP check; sends exactly one explicitly authorized text.

The operation ID is durable: rerunning verifies the same send without replay.
Reports contain counts/booleans only, never identifiers or message bodies.
"""

import argparse
import asyncio
import hashlib
import json
import logging
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from fastmcp import Client  # noqa: E402

from WPP_Whatsapp import AsyncClient  # noqa: E402
from WPP_Whatsapp.mcp import create_server  # noqa: E402


async def run(args):
    logging.getLogger("WPP_Whatsapp").setLevel(logging.WARNING)
    report = {
        "started": datetime.now(timezone.utc).isoformat(),
        "authorized_send": bool(args.recipient),
    }
    client = AsyncClient(
        args.session,
        token_directory=str(ROOT / "tokens"),
        autoClose=0,
        logQR=False,
        deliveryStore=str(ROOT / "tokens/.deliveries/live-mcp-development.sqlite3"),
    )
    media_directory = tempfile.TemporaryDirectory(prefix="mcp-live-media-", dir=ROOT / "archive")
    try:
        async with Client(
            create_server(client, media_root=media_directory.name), timeout=240
        ) as mcp:
            report["tool_count"] = len(await mcp.list_tools())
            print("Connecting saved test profile", flush=True)
            await mcp.call_tool("whatsapp_connect")
            report["ready"] = (await mcp.call_tool("whatsapp_status")).structured_content["ready"]
            print("WhatsApp ready", flush=True)
            groups = (
                await mcp.call_tool("whatsapp_list_chats", {"kind": "groups", "limit": 100})
            ).data
            context = client._context
            chat = await client.browser.page_evaluate(
                """async () => {
                const chats = await WPP.chat.list({onlyGroups: true, count: 100});
                return chats.find(c => !c.unreadCount && c.lastReceivedKey &&
                    c.groupMetadata?.groupType !== 'COMMUNITY')?.id.toString();
            }""",
                page=context.page,
            )
            if not chat:
                raise RuntimeError("No already-read group is available")
            report["group_count"] = len(groups)
            history = (
                await mcp.call_tool("whatsapp_get_messages", {"chat_id": chat, "limit": 25})
            ).data
            report["already_read_group_history_count"] = len(history)
            assert history and all(item.get("id") for item in history)
            found = (
                await mcp.call_tool("whatsapp_get_message", {"message_id": history[0]["id"]})
            ).data
            report["full_message_id_lookup_matches"] = found["id"] == history[0]["id"]
            typed = await client.typed.get_message(history[0]["id"])
            report["typed_lookup_matches"] = typed.id == history[0]["id"]
            group = await client.typed.get_group(chat)
            report["typed_group_matches"] = group.id == chat
            search = (
                await mcp.call_tool(
                    "whatsapp_search_messages",
                    {"chat_id": chat, "query": "اختبار", "scan_limit": 25},
                )
            ).data
            report["search_scanned"] = search["scanned"]
            if search["before_message_id"]:
                older = (
                    await mcp.call_tool(
                        "whatsapp_get_messages",
                        {
                            "chat_id": chat,
                            "limit": 25,
                            "before_message_id": search["before_message_id"],
                        },
                    )
                ).data
                report["older_page_count"] = len(older)
                report["search_cursor_pages_disjoint"] = not (
                    {item["id"] for item in history} & {item["id"] for item in older}
                )
                assert report["search_cursor_pages_disjoint"]
            image = next((message for message in history if message.get("type") == "image"), None)
            if image:
                media = (
                    await mcp.call_tool("whatsapp_download_media", {"message_id": image["id"]})
                ).data
                saved = Path(media_directory.name) / media["filename"]
                report["media_download_size"] = saved.stat().st_size
                report["media_download_hash_matches"] = (
                    hashlib.sha256(saved.read_bytes()).hexdigest() == media["sha256"]
                )
            report["diagnostics_ready"] = (await mcp.call_tool("whatsapp_diagnostics")).data[
                "ready"
            ]
            cursor = (await mcp.call_tool("whatsapp_subscribe_messages")).data["cursor"]
            report["event_subscription"] = True
            if args.recipient:
                chat_id = args.recipient if "@" in args.recipient else args.recipient + "@c.us"
                params = {
                    "chat_id": chat_id,
                    "text": "اختبار تكامل WPP_Whatsapp",
                    "operation_id": args.operation_id,
                }
                receipt = (await mcp.call_tool("whatsapp_send_text", params)).structured_content
                report["send_state"] = receipt["state"]
                report["send_has_id"] = bool(receipt["message_id"])
                if receipt["state"] != "confirmed":
                    raise RuntimeError(
                        "Send requires reconciliation; do not retry under a new operation ID"
                    )
                same = (await mcp.call_tool("whatsapp_send_text", params)).structured_content
                report["same_operation_receipt"] = same == receipt
                outgoing = (
                    await mcp.call_tool(
                        "whatsapp_get_message", {"message_id": receipt["message_id"]}
                    )
                ).data
                report["outgoing_message_verified"] = outgoing["id"] == receipt[
                    "message_id"
                ] and bool(outgoing["fromMe"])
                print("Authorized text confirmed and duplicate operation verified", flush=True)
            # Optional bounded wait for a fresh incoming group message to exercise #84.
            if args.wait_events:
                print("Waiting for a new incoming group message", flush=True)
                deadline = asyncio.get_running_loop().time() + args.wait_events
                while asyncio.get_running_loop().time() < deadline:
                    page = (await mcp.call_tool("whatsapp_get_events", {"after": cursor})).data
                    cursor = page["cursor"]
                    for event in page["events"]:
                        message = event["message"]
                        key = message.get("id", "")
                        if "@g.us_" not in key or message.get("fromMe"):
                            continue
                        lookup = (
                            await mcp.call_tool("whatsapp_get_message", {"message_id": key})
                        ).data
                        report["fresh_group_callback_full_id_lookup_matches"] = lookup["id"] == key
                        break
                    if report.get("fresh_group_callback_full_id_lookup_matches"):
                        break
                    await asyncio.sleep(2)
            report["runtime"] = context.runtime_capabilities
    finally:
        await client.close()
        media_directory.cleanup()
        report["closed"] = client.state.value == "closed"
        (ROOT / "archive/live-mcp-development.json").write_text(
            json.dumps(report, indent=2), encoding="utf-8"
        )
        print(json.dumps(report), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--session", default="live-smoke-81-84")
    parser.add_argument("--recipient", help="Explicitly authorized destination; omit for read-only")
    parser.add_argument("--operation-id", default="development-smoke-20261013")
    parser.add_argument("--wait-events", type=int, default=0)
    asyncio.run(run(parser.parse_args()))
