"""New MCP operations use real FastMCP dispatch with isolated durable journals."""

from unittest.mock import AsyncMock

import pytest

pytest.importorskip("fastmcp")

from fastmcp import Client
from fastmcp.exceptions import ToolError

from tests.test_mcp_development import EventClient
from WPP_Whatsapp.core.delivery_models import DeliveryReceipt, DeliveryState
from WPP_Whatsapp.mcp import create_server
from WPP_Whatsapp.mcp.accounts import AccountConfig


@pytest.mark.asyncio
async def test_durable_mcp_claim_complete_restart_and_account_boundary(tmp_path):
    first, other = EventClient("first"), EventClient("other")
    for fake in (first, other):
        fake.options = {"eventStore": str(tmp_path / "events")}
    accounts = {
        "a": AccountConfig("first", client=first),
        "b": AccountConfig("other", client=other),
    }
    async with Client(create_server(accounts=accounts, read_only=True)) as client:
        for account in ("a", "b"):
            await client.call_tool("whatsapp_connect", {"account_id": account})
            await client.call_tool("whatsapp_subscribe_messages", {"account_id": account})
        await first.receive({"id": "full_group_id", "body": "private"})
        result = (
            await client.call_tool(
                "whatsapp_claim_event", {"account_id": "a", "consumer_id": "worker"}
            )
        ).data
        lease = result["lease"]
        assert lease["event"]["message"]["id"] == "full_group_id" and lease["attempt"] == 1
        completion = {
            "consumer_id": "worker",
            "sequence": lease["sequence"],
            "token": lease["token"],
            "outcome": "ack",
        }
        with pytest.raises(ToolError):
            await client.call_tool("whatsapp_complete_event", {**completion, "account_id": "b"})
        await client.call_tool(
            "whatsapp_complete_event", {**completion, "account_id": "a", "outcome": "renew"}
        )
        await client.call_tool("whatsapp_complete_event", {**completion, "account_id": "a"})
        with pytest.raises(ToolError):
            await client.call_tool("whatsapp_complete_event", {**completion, "account_id": "a"})
    async with Client(create_server(first, read_only=True)) as client:
        result = (await client.call_tool("whatsapp_claim_event", {"consumer_id": "worker"})).data
        assert result["lease"] is None and result["lost_total"] == 0
    first.context.sendText_.assert_not_called()
    other.context.sendText_.assert_not_called()


@pytest.mark.asyncio
async def test_durable_tools_refuse_memory_buffer_and_metrics_are_sanitized():
    fake = EventClient("account")
    fake.metrics = AsyncMock(return_value={"bridge": {"calls": 3}, "private": "omit"})
    async with Client(create_server(fake, read_only=True)) as client:
        with pytest.raises(ToolError, match="eventStore"):
            await client.call_tool("whatsapp_claim_event", {"consumer_id": "worker"})
        result = await client.call_tool("whatsapp_metrics")
        assert "wpp_bridge_calls 3" in str(result.content)
        assert "omit" not in str(result.content)
        tools = {tool.name: tool for tool in await client.list_tools()}
        assert "whatsapp_recover_delivery" not in tools
        assert not tools["whatsapp_complete_event"].annotations.read_only_hint


@pytest.mark.asyncio
async def test_recovery_and_operation_listing_use_read_and_send_scopes(tmp_path):
    fake = EventClient("account")
    fake.context.options["deliveryStore"] = str(tmp_path / "ledger")
    await fake.connect()
    async with Client(create_server(fake)) as client:
        # Listing metadata is bounded and does not initiate a send.
        assert (await client.call_tool("whatsapp_list_operations")).data == []
        with pytest.raises(ToolError):
            await client.call_tool("whatsapp_recover_delivery", {"operation_id": "unknown"})
        fake.messages.deliveries._store.save(
            DeliveryReceipt("existing", DeliveryState.CONFIRMED, "full-key")
        )
        await client.call_tool("whatsapp_disconnect")
        receipt = (
            await client.call_tool("whatsapp_get_delivery", {"operation_id": "existing"})
        ).structured_content
        assert receipt["receipt"]["message_id"] == "full-key"
        assert len((await client.call_tool("whatsapp_list_operations")).data) == 1
    fake.context.sendText_.assert_not_called()
