"""Explicit opt-in: send one synthetic image and document, verify lookup/download.

Only run with an authorized recipient. Stable operation IDs prevent replay on
reruns. Reports omit recipients, IDs, paths and message contents.
"""

import argparse
import asyncio
import hashlib
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from fastmcp import Client  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402

from WPP_Whatsapp import AsyncClient  # noqa: E402
from WPP_Whatsapp.mcp import create_server  # noqa: E402


async def main(args):
    logging.getLogger("WPP_Whatsapp").setLevel(logging.WARNING)
    directory = ROOT / "archive/live-media-assets"
    directory.mkdir(parents=True, exist_ok=True)
    image_path, document_path = directory / "test.png", directory / "test.txt"
    image = Image.new("RGB", (512, 256), "white")
    drawing = ImageDraw.Draw(image)
    drawing.rectangle((16, 16, 496, 240), outline="#2663d8", width=4)
    drawing.text((36, 110), "WPP_Whatsapp - media integration test", fill="black")
    image.save(image_path)
    document_path.write_bytes(
        b"WPP_Whatsapp media integration test.\nSynthetic test document; no private data.\n"
    )
    client = AsyncClient(
        args.session,
        token_directory=str(ROOT / "tokens"),
        autoClose=0,
        logQR=False,
        deliveryStore=str(ROOT / "tokens/.deliveries/live-mcp-development.sqlite3"),
    )
    report = {"started": datetime.now(timezone.utc).isoformat(), "media": {}}
    try:
        async with Client(create_server(client, media_root=str(directory)), timeout=240) as mcp:
            print("Connecting saved test profile", flush=True)
            await mcp.call_tool("whatsapp_connect")
            recipient = args.recipient if "@" in args.recipient else args.recipient + "@c.us"
            for kind, path, tool in (
                ("image", image_path, "whatsapp_send_image"),
                ("document", document_path, "whatsapp_send_file"),
            ):
                if args.document_only and kind != "document":
                    continue
                operation = args.operation_prefix + "-" + kind
                params = {"chat_id": recipient, "filename": path.name, "operation_id": operation}
                receipt = (await mcp.call_tool(tool, params)).structured_content
                result = report["media"][kind] = {
                    "state": receipt["state"],
                    "has_id": bool(receipt["message_id"]),
                }
                print(f"{kind}: {receipt['state']}", flush=True)
                if receipt["state"] != "confirmed":
                    raise RuntimeError(
                        "Uncertain media delivery; do not resend under another operation ID"
                    )
                same = (await mcp.call_tool(tool, params)).structured_content
                result["duplicate_receipt_matches"] = same == receipt
                message = (
                    await mcp.call_tool(
                        "whatsapp_get_message", {"message_id": receipt["message_id"]}
                    )
                ).data
                result["outgoing_lookup_matches"] = message["id"] == receipt["message_id"] and bool(
                    message["fromMe"]
                )
                result["message_type"] = message.get("type")
                assert result["duplicate_receipt_matches"] and result["outgoing_lookup_matches"]
                downloaded = (
                    await mcp.call_tool(
                        "whatsapp_download_media", {"message_id": receipt["message_id"]}
                    )
                ).data
                target = directory / downloaded["filename"]
                result["downloaded_bytes"] = target.stat().st_size
                result["download_hash_matches"] = (
                    hashlib.sha256(target.read_bytes()).hexdigest() == downloaded["sha256"]
                )
                if kind == "document":
                    result["roundtrip_bytes_match"] = target.read_bytes() == path.read_bytes()
                    assert result["roundtrip_bytes_match"]
                else:
                    with Image.open(target) as received:
                        result["download_is_valid_image"] = (
                            received.width > 0 and received.height > 0
                        )
                assert result["download_hash_matches"]
                target.unlink()
            report["runtime"] = client._context.runtime_capabilities
    finally:
        await client.close()
        report["closed"] = client.state.value == "closed"
        (ROOT / "archive/live-mcp-media-2.2.0.json").write_text(
            json.dumps(report, indent=2), encoding="utf-8"
        )
        print(json.dumps(report), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--recipient", required=True, help="Explicitly authorized destination")
    parser.add_argument("--session", default="live-smoke-81-84")
    parser.add_argument("--operation-prefix", default="release-2.2-media-check")
    parser.add_argument(
        "--document-only", action="store_true", help="Send/verify only the document"
    )
    asyncio.run(main(parser.parse_args()))
