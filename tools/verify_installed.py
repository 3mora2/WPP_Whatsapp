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
    assert Message.from_raw({"id": "false_1@g.us_KEY_2@lid"}).id.endswith("_2@lid")
    assert AsyncClient().diagnostics()["state"] == "new"
    result = {"version": expected, "isolated_install": True, "commands": len(COMMANDS)}
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
            assert result["tools"] - result["read_only_tools"] == 5
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", required=True)
    parser.add_argument("--mcp", action="store_true")
    args = parser.parse_args()
    print(json.dumps(asyncio.run(verify(args.version, args.mcp))))
