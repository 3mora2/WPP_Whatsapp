"""Real MCP transport contracts around the new reliability services."""

import asyncio
from unittest.mock import AsyncMock

import pytest

pytest.importorskip("fastmcp")

from fastmcp import Client
from fastmcp.exceptions import ToolError

from tests.helpers import eventually
from tests.test_mcp import GROUP_ID, MESSAGE_ID
from tests.test_mcp_development import EventClient
from WPP_Whatsapp.mcp import create_server
from WPP_Whatsapp.mcp.event_buffer import EventBuffer
from WPP_Whatsapp.mcp.runtime import SessionRuntime


@pytest.mark.asyncio
async def test_same_account_reads_and_metadata_remain_responsive():
    fake = EventClient("reliable")
    await fake.connect()
    entered, release = asyncio.Event(), asyncio.Event()

    async def slow_read(*args):
        entered.set()
        await release.wait()
        return []

    fake.context.getMessages_.side_effect = slow_read
    async with Client(create_server(fake)) as client:
        pending = asyncio.create_task(
            client.call_tool("whatsapp_get_messages", {"chat_id": GROUP_ID})
        )
        await entered.wait()
        try:
            status = await asyncio.wait_for(client.call_tool("whatsapp_status"), 1)
            assert status.structured_content["ready"]
            lookup = await asyncio.wait_for(
                client.call_tool("whatsapp_get_message", {"message_id": MESSAGE_ID}), 1
            )
            assert lookup.data["id"] == MESSAGE_ID
        finally:
            release.set()
            await pending


@pytest.mark.asyncio
async def test_lifecycle_waiter_prevents_new_reads_overtaking_disconnect():
    fake = EventClient("exclusive")
    await fake.connect()
    runtime = SessionRuntime(fake, True)
    release, started = asyncio.Event(), asyncio.Event()

    async def operation():
        started.set()
        await release.wait()

    first = asyncio.create_task(runtime.run(operation))
    await started.wait()
    disconnect = asyncio.create_task(runtime.run(fake.close, ready=False, exclusive=True))
    await eventually(lambda: runtime._exclusive_waiters == 1)
    following = asyncio.create_task(runtime.run(AsyncMock()))
    release.set()
    await first
    await disconnect
    from WPP_Whatsapp.core.errors import SessionNotReadyError

    with pytest.raises(SessionNotReadyError):
        await following
    assert runtime._active == 0


@pytest.mark.asyncio
async def test_durable_mcp_events_survive_server_lifespan_and_deduplicate(tmp_path):
    path = tmp_path / "events.db"
    for index in range(2):
        fake = EventClient("durable")
        fake.options = {"eventStore": path, "eventBufferSize": 4}
        async with Client(create_server(fake)) as client:
            await client.call_tool("whatsapp_connect")
            subscribed = (await client.call_tool("whatsapp_subscribe_messages")).data
            assert subscribed["cursor"] == index
            await fake.receive({"id": MESSAGE_ID, "body": "synthetic", "base64": "excluded"})
            events = (await client.call_tool("whatsapp_get_events")).data
            assert events["cursor"] == 1 and len(events["events"]) == 1
            assert "base64" not in events["events"][0]["message"]
        assert not fake.listeners


@pytest.mark.asyncio
async def test_new_ack_tools_are_read_only_and_do_not_dispatch():
    fake = EventClient("ack")
    await fake.connect()
    fake.messages.delivery_status = AsyncMock(
        return_value={
            "operation_id": "existing",
            "message_id": MESSAGE_ID,
            "ack": 2,
            "delivered": True,
            "read": False,
            "played": False,
        }
    )
    fake.messages.wait_for_delivery = AsyncMock(side_effect=fake.messages.delivery_status)
    async with Client(create_server(fake, read_only=True)) as client:
        tools = {tool.name: tool for tool in await client.list_tools()}
        assert len(tools) == 18 and tools["whatsapp_wait_for_delivery"].annotations.read_only_hint
        result = await client.call_tool("whatsapp_delivery_status", {"operation_id": "existing"})
        assert result.structured_content["delivered"] and not result.structured_content["read"]
        with pytest.raises(ToolError):
            await client.call_tool(
                "whatsapp_wait_for_delivery", {"operation_id": "existing", "timeout": 121}
            )
    fake.context.sendText_.assert_not_called()


@pytest.mark.asyncio
async def test_manual_reconnect_restores_subscription_without_duplicate_listener():
    fake = EventClient("rebind")
    async with Client(create_server(fake)) as client:
        await client.call_tool("whatsapp_connect")
        await client.call_tool("whatsapp_subscribe_messages")
        await client.call_tool("whatsapp_reconnect")
        assert len(fake.listeners) == 1
        await fake.receive({"id": MESSAGE_ID})
        assert len((await client.call_tool("whatsapp_get_events")).data["events"]) == 1


@pytest.mark.asyncio
async def test_event_buffer_rejects_invalid_limits_before_disk_io(tmp_path):
    path = tmp_path / "events.db"
    buffer = EventBuffer(path=path)
    with pytest.raises(ValueError):
        buffer.read(0, 0)
    assert not path.exists()
    await buffer.close()
