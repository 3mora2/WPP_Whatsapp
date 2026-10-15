"""Exercise real MCP schemas/transports with deterministic WhatsApp operations."""

import asyncio
import os
import socket
import subprocess
import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

pytest.importorskip("fastmcp", reason="Install the mcp extra on Python 3.10+")

from fastmcp import Client
from fastmcp.client.transports import StdioTransport
from fastmcp.exceptions import ToolError

from tests.helpers import eventually, ready_context
from WPP_Whatsapp.core.lifecycle import SessionState
from WPP_Whatsapp.core.services import ServiceHub
from WPP_Whatsapp.mcp import create_server

ROOT = Path(__file__).parents[1]
GROUP_ID = "120000000000@g.us"
MESSAGE_ID = "false_120000000000@g.us_AAA_123456789@c.us"


class FakeClient:
    def __init__(self):
        self.session = "mcp-test"
        self.state = SessionState.NEW
        self.context = ready_context(
            getMessages_=AsyncMock(return_value=[{"id": MESSAGE_ID}]),
            getMessageById_=AsyncMock(return_value={"id": MESSAGE_ID, "fromMe": True}),
            listChats_=AsyncMock(return_value=[{"id": GROUP_ID}]),
            getContact_=AsyncMock(return_value={"id": "123456789@c.us"}),
            getGroupMembers_=AsyncMock(return_value=[{"id": "123456789@c.us"}]),
            sendText_=AsyncMock(return_value={"id": "true_123456789@c.us_SENT"}),
        )
        hub = ServiceHub(self.context)
        self.messages, self.chats, self.groups = hub.messages, hub.chats, hub.groups
        self.connect = AsyncMock(side_effect=self._connect)
        self.close = AsyncMock(side_effect=self._close)
        self.reconnect = AsyncMock(side_effect=self._connect)

    async def _connect(self):
        self.state = SessionState.READY
        return self

    async def _close(self):
        self.state = SessionState.CLOSED
        if hasattr(self.context, "_delivery_tracker"):
            await self.context._delivery_tracker.aclose()


@pytest.mark.asyncio
async def test_schema_discovery_lazy_start_and_readiness():
    fake = FakeClient()
    async with Client(create_server(fake)) as client:
        tools = {tool.name: tool for tool in await client.list_tools()}
        assert len(tools) == 29
        assert all("ctx" not in tool.input_schema.get("properties", {}) for tool in tools.values())
        assert tools["whatsapp_get_messages"].annotations.read_only_hint is True
        assert tools["whatsapp_send_text"].annotations.idempotent_hint is True
        assert "operation_id" in tools["whatsapp_send_text"].input_schema["required"]
        assert set(tools["whatsapp_status"].output_schema["required"]) == {
            "session",
            "state",
            "ready",
            "read_only",
        }
        assert set(tools["whatsapp_send_text"].output_schema["required"]) == {
            "operation_id",
            "state",
            "message_id",
        }
        status = await client.call_tool("whatsapp_status")
        assert (
            status.structured_content["state"] == "new"
            and status.structured_content["ready"] is False
        )
        fake.connect.assert_not_awaited()
        with pytest.raises(ToolError, match="finish login"):
            await client.call_tool("whatsapp_get_messages", {"chat_id": GROUP_ID})
        fake.context.getMessages_.assert_not_awaited()
        assert (await client.call_tool("whatsapp_connect")).structured_content["ready"] is True
        absent = await client.call_tool("whatsapp_get_delivery", {"operation_id": "not-found"})
        assert absent.structured_content == {"receipt": None}
    fake.close.assert_not_awaited()  # The caller owns an injected client.


@pytest.mark.asyncio
async def test_owned_client_is_lazy_configured_and_closed_even_on_failed_connect(tmp_path):
    fake = FakeClient()
    fake.connect.side_effect = RuntimeError("secret credential")
    with patch("WPP_Whatsapp.mcp.server.AsyncClient", return_value=fake) as constructor:
        server = create_server(token_directory=str(tmp_path / "private"))
        constructor.assert_not_called()
        assert not (tmp_path / "private").exists()
        async with Client(server) as client:
            constructor.assert_called_once()
            settings = constructor.call_args.kwargs
            assert settings["wait_for_login"] is False and settings["logQR"] is False
            assert settings["autoClose"] == 0 and settings["deliveryStore"].endswith("mcp.sqlite3")
            with pytest.raises(ToolError, match="RuntimeError") as error:
                await client.call_tool("whatsapp_connect")
            assert "secret credential" not in str(error.value)
        fake.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_history_pagination_and_complete_message_ids_pass_through():
    fake = FakeClient()
    await fake.connect()
    async with Client(create_server(fake)) as client:
        messages = await client.call_tool(
            "whatsapp_get_messages",
            {"chat_id": GROUP_ID, "limit": 25, "before_message_id": MESSAGE_ID},
        )
        assert messages.data == [{"id": MESSAGE_ID}]
        fake.context.getMessages_.assert_awaited_once_with(
            GROUP_ID, {"count": 25, "id": MESSAGE_ID, "direction": "before"}
        )
        result = await client.call_tool("whatsapp_get_message", {"message_id": MESSAGE_ID})
        assert result.data["id"] == MESSAGE_ID
        fake.context.getMessageById_.assert_awaited_once_with(MESSAGE_ID)
        await client.call_tool(
            "whatsapp_list_chats", {"limit": 15, "kind": "groups", "before_chat_id": GROUP_ID}
        )
        fake.context.listChats_.assert_awaited_once_with(
            {"count": 15, "onlyGroups": True, "id": GROUP_ID, "direction": "before"}
        )
        await client.call_tool("whatsapp_get_contact", {"contact_id": "123456789@c.us"})
        fake.context.getContact_.assert_awaited_once_with("123456789@c.us")
        await client.call_tool("whatsapp_get_group_members", {"group_id": GROUP_ID})
        fake.context.getGroupMembers_.assert_awaited_once_with(GROUP_ID)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "arguments",
    [
        {"chat_id": GROUP_ID, "limit": 0},
        {"chat_id": GROUP_ID, "limit": 201},
        {"chat_id": GROUP_ID, "limit": True},
        {"chat_id": ""},
        {"chat_id": "   "},
    ],
)
async def test_invalid_reads_never_reach_whatsapp(arguments):
    fake = FakeClient()
    await fake.connect()
    async with Client(create_server(fake)) as client:
        with pytest.raises(ToolError):
            await client.call_tool("whatsapp_get_messages", arguments)
    fake.context.getMessages_.assert_not_awaited()


@pytest.mark.asyncio
async def test_send_receipts_and_retries_use_real_tracker_without_replay():
    fake = FakeClient()
    await fake.connect()
    async with Client(create_server(fake)) as client:
        arguments = {"chat_id": "123456789@c.us", "text": "synthetic", "operation_id": "one-send"}
        first = await client.call_tool("whatsapp_send_text", arguments)
        second = await client.call_tool("whatsapp_send_text", arguments)
        assert first.structured_content == second.structured_content
        assert first.structured_content["state"] == "confirmed"
        fake.context.sendText_.assert_awaited_once_with("123456789@c.us", "synthetic", {})
        assert (
            await client.call_tool("whatsapp_get_delivery", {"operation_id": "one-send"})
        ).structured_content["receipt"] == first.structured_content
        await client.call_tool("whatsapp_disconnect")
        assert (
            await client.call_tool("whatsapp_get_delivery", {"operation_id": "one-send"})
        ).structured_content["receipt"] == first.structured_content
    await fake.close()


@pytest.mark.asyncio
async def test_unknown_send_is_not_replayed_and_can_be_reconciled():
    fake = FakeClient()
    await fake.connect()
    fake.context.sendText_.return_value = None
    async with Client(create_server(fake)) as client:
        arguments = {"chat_id": GROUP_ID, "text": "synthetic", "operation_id": "uncertain"}
        for _ in range(2):
            result = await client.call_tool("whatsapp_send_text", arguments)
            assert result.structured_content == {
                "operation_id": "uncertain",
                "state": "unknown",
                "message_id": None,
            }
        fake.context.sendText_.assert_awaited_once()
        receipt = await client.call_tool(
            "whatsapp_reconcile_delivery", {"operation_id": "uncertain", "message_id": MESSAGE_ID}
        )
        assert (
            receipt.structured_content["state"] == "confirmed"
            and receipt.structured_content["message_id"] == MESSAGE_ID
        )
        fake.context.getMessageById_.assert_awaited_once_with(MESSAGE_ID)
    await fake.close()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "overrides",
    [
        {"operation_id": ""},
        {"operation_id": " "},
        {"operation_id": "a" * 129},
        {"chat_id": " "},
        {"text": ""},
    ],
)
async def test_invalid_sends_never_dispatch(overrides):
    fake = FakeClient()
    await fake.connect()
    args = {"chat_id": GROUP_ID, "text": "synthetic", "operation_id": "invalid-test", **overrides}
    async with Client(create_server(fake)) as client:
        with pytest.raises(ToolError):
            await client.call_tool("whatsapp_send_text", args)
    fake.context.sendText_.assert_not_awaited()
    await fake.close()


@pytest.mark.asyncio
async def test_sqlite_receipt_survives_server_restart_without_resend(tmp_path):
    for iteration in range(2):
        fake = FakeClient()
        fake.context.options["deliveryStore"] = str(tmp_path / "delivery.sqlite3")
        await fake.connect()
        async with Client(create_server(fake)) as client:
            result = await client.call_tool(
                "whatsapp_send_text",
                {"chat_id": GROUP_ID, "text": "synthetic", "operation_id": "durable"},
            )
            assert result.structured_content["state"] == "confirmed"
        assert fake.context.sendText_.await_count == (1 if iteration == 0 else 0)
        await fake.close()


@pytest.mark.asyncio
async def test_send_timeout_is_unknown_and_late_confirmation_is_visible():
    fake = FakeClient()
    fake.context.options["operationTimeout"] = 0.01
    finish = asyncio.Event()

    async def delayed(*args):
        await finish.wait()
        return {"id": MESSAGE_ID}

    fake.context.sendText_.side_effect = delayed
    await fake.connect()
    try:
        async with Client(create_server(fake)) as client:
            args = {"chat_id": GROUP_ID, "text": "synthetic", "operation_id": "late"}
            result = await client.call_tool("whatsapp_send_text", args)
            assert result.structured_content["state"] == "unknown"
            retry = await client.call_tool("whatsapp_send_text", args)
            assert retry.structured_content["state"] == "unknown"
            fake.context.sendText_.assert_awaited_once()
            finish.set()
            await eventually(
                lambda: fake.messages.deliveries.get("late").state.value == "confirmed"
            )
            result = await client.call_tool("whatsapp_get_delivery", {"operation_id": "late"})
            assert (
                result.structured_content["receipt"]["state"] == "confirmed"
                and result.structured_content["receipt"]["message_id"] == MESSAGE_ID
            )
    finally:
        finish.set()
        await fake.close()


@pytest.mark.asyncio
async def test_read_only_omits_mutations_and_errors_do_not_expose_payloads(caplog):
    fake = FakeClient()
    await fake.connect()
    fake.context.getMessages_.side_effect = RuntimeError("private-message secret-token")
    async with Client(create_server(fake, read_only=True)) as client:
        tools = {tool.name for tool in await client.list_tools()}
        assert "whatsapp_send_text" not in tools and "whatsapp_reconcile_delivery" not in tools
        with pytest.raises(ToolError) as error:
            await client.call_tool("whatsapp_get_messages", {"chat_id": GROUP_ID})
        assert "private-message" not in str(error.value) and "secret-token" not in caplog.text


@pytest.mark.asyncio
async def test_disconnect_waits_for_active_read_and_reconnect_is_explicit():
    fake = FakeClient()
    await fake.connect()
    started, finish = asyncio.Event(), asyncio.Event()

    async def read(*args):
        started.set()
        await finish.wait()
        return []

    fake.context.getMessages_.side_effect = read
    async with Client(create_server(fake)) as client:
        pending = asyncio.create_task(
            client.call_tool("whatsapp_get_messages", {"chat_id": GROUP_ID})
        )
        await asyncio.wait_for(started.wait(), 2)
        close = asyncio.create_task(client.call_tool("whatsapp_disconnect"))
        await asyncio.sleep(0.01)
        fake.close.assert_not_awaited()
        finish.set()
        await asyncio.wait_for(asyncio.gather(pending, close), 2)
        assert fake.state == SessionState.CLOSED
        assert (await client.call_tool("whatsapp_reconnect")).structured_content["ready"] is True


@pytest.mark.asyncio
async def test_real_stdio_server_discovery_and_status_without_browser(tmp_path):
    transport = StdioTransport(
        command=sys.executable,
        args=[
            "-m",
            "WPP_Whatsapp.mcp",
            "--read-only",
            "--token-directory",
            str(tmp_path / "profile"),
        ],
        cwd=str(ROOT),
        keep_alive=False,
    )
    async with Client(transport, timeout=15) as client:
        assert len(await client.list_tools()) == 23
        result = await client.call_tool("whatsapp_status")
        assert result.structured_content == {
            "session": "mcp",
            "state": "new",
            "ready": False,
            "read_only": True,
        }
    assert not (tmp_path / "profile").exists()


@pytest.mark.asyncio
async def test_real_http_server_discovery_and_status_without_browser(tmp_path):
    import httpx2

    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "WPP_Whatsapp.mcp",
            "--transport",
            "http",
            "--port",
            str(port),
            "--read-only",
            "--token-directory",
            str(tmp_path / "profile"),
        ],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
    )

    async def ready():
        async with httpx2.AsyncClient() as probe:
            for _ in range(100):
                if process.poll() is not None:
                    raise RuntimeError("HTTP server exited during startup")
                try:
                    await probe.get(f"http://127.0.0.1:{port}/", timeout=0.2)
                    return
                except httpx2.TransportError:
                    await asyncio.sleep(0.1)
            raise TimeoutError("HTTP server did not start")

    try:
        # Match the bounded polling window: cold optional imports can take over
        # 12 seconds on Windows while the endurance workloads are active.
        await asyncio.wait_for(ready(), 30)
        async with Client(f"http://127.0.0.1:{port}/mcp", timeout=10) as client:
            assert len(await client.list_tools()) == 23
            assert (await client.call_tool("whatsapp_status")).structured_content["state"] == "new"
    finally:
        process.terminate()
        try:
            await asyncio.to_thread(process.communicate, timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            await asyncio.to_thread(process.communicate, timeout=5)
    assert not (tmp_path / "profile").exists()
