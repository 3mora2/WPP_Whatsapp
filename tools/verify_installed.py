"""Isolated installed-wheel check. Run with python -I, never add the checkout path."""

import argparse
import asyncio
import importlib.metadata
import json
import tempfile
from pathlib import Path


async def verify(expected, mcp):
    import WPP_Whatsapp
    from WPP_Whatsapp import AsyncClient, Message
    from WPP_Whatsapp.core.commands import COMMANDS

    installed = Path(WPP_Whatsapp.__file__).resolve()
    assert "site-packages" in installed.parts, "Checkout imported instead of installed wheel"
    assert importlib.metadata.version("WPP_Whatsapp") == expected
    assert (installed.parent / "py.typed").is_file()
    if tuple(int(part) for part in expected.split(".")[:2]) >= (2, 4):
        assert (installed.parent / "core/service_types.pyi").is_file()
    assert Message.from_raw({"id": "false_1@g.us_KEY_2@lid"}).id.endswith("_2@lid")
    assert AsyncClient().diagnostics()["state"] == "new"
    result = {"version": expected, "isolated_install": True, "commands": len(COMMANDS)}
    if tuple(int(part) for part in expected.split(".")[:2]) >= (2, 4):
        from WPP_Whatsapp import DurableConsumer, SQLiteEventStore
        from WPP_Whatsapp.core.delivery import DeliveryTracker
        from WPP_Whatsapp.core.delivery_models import ExpectedMessage

        with tempfile.TemporaryDirectory(prefix="wpp-persistence-") as directory:
            path = Path(directory)
            journal = SQLiteEventStore(path / "events", "wheel", 10, 3600)
            journal.append({"message": {"id": "synthetic"}})
            worker = DurableConsumer(journal, "wheel-check")
            lease = (await worker.claim())["lease"]
            assert lease is not None
            await worker.ack(lease)
            journal.close()
            journal = SQLiteEventStore(path / "events", "wheel", 10, 3600)
            assert (await DurableConsumer(journal, "wheel-check").claim())["lease"] is None
            journal.close()
            tracker = DeliveryTracker(path / "ledger", "wheel")

            async def prepare():
                return ExpectedMessage("true_1@c.us_SYNTHETIC", "1@c.us", "chat")

            async def synthetic_send():
                assert await tracker.expected_async("wheel-check") == await prepare()
                return {"id": "true_1@c.us_SYNTHETIC"}

            receipt = await tracker.send(synthetic_send, "wheel-check", prepare=prepare)
            await tracker.aclose()
            reopened = DeliveryTracker(path / "ledger", "wheel")
            assert await reopened.get_async("wheel-check") == receipt
            await reopened.aclose()
            result["durable_feature_smoke"] = True
    if mcp:
        import sys

        from fastmcp import Client
        from fastmcp.client.transports import StdioTransport

        from WPP_Whatsapp.mcp import create_server

        with tempfile.TemporaryDirectory(prefix="wpp-wheel-") as directory:
            profile = Path(directory) / "unopened"
            transport = StdioTransport(
                command=sys.executable,
                args=[
                    "-I",
                    "-m",
                    "WPP_Whatsapp.mcp",
                    "--read-only",
                    "--token-directory",
                    str(profile),
                ],
                cwd=directory,
                keep_alive=False,
            )
            async with Client(transport, timeout=30) as client:
                tools = await client.list_tools()
                status = (await client.call_tool("whatsapp_status")).structured_content
                assert status["state"] == "new" and not status["ready"]
                result["read_only_tools"] = len(tools)
            async with Client(create_server(token_directory=str(profile))) as client:
                result["tools"] = len(await client.list_tools())
            assert not profile.exists(), "Startup created a browser profile"
            mutating = 6 if tuple(int(part) for part in expected.split(".")[:2]) >= (2, 4) else 5
            assert result["tools"] - result["read_only_tools"] == mutating
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", required=True)
    parser.add_argument("--mcp", action="store_true")
    args = parser.parse_args()
    print(json.dumps(asyncio.run(verify(args.version, args.mcp))))
