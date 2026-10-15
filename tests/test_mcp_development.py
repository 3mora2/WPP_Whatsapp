"""Account boundaries, authenticated HTTP, events and new MCP contracts."""

import asyncio
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

pytest.importorskip("fastmcp", reason="Requires optional MCP support on Python 3.10+")

import httpx2
from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport
from fastmcp.exceptions import ToolError
from fastmcp.server.auth import JWTVerifier
from fastmcp.server.auth.providers.jwt import RSAKeyPair

from tests.test_mcp import GROUP_ID, MESSAGE_ID, FakeClient
from WPP_Whatsapp.mcp import create_server
from WPP_Whatsapp.mcp.accounts import AccountConfig
from WPP_Whatsapp.mcp.event_buffer import EventBuffer
from WPP_Whatsapp.mcp.runtime import SessionRuntime


class EventClient(FakeClient):
    def __init__(self, name):
        super().__init__()
        self.session = name
        self.listeners = []
        self.events = SimpleNamespace(on_message=self.on_message)
        self.diagnostics = lambda: {"state": self.state.value, "ready": self.state.value == "ready"}

    def on_message(self, callback):
        self.listeners.append(callback)
        return lambda: self.listeners.remove(callback)

    async def receive(self, message):
        for listener in list(self.listeners):
            await listener(message)


@pytest.mark.asyncio
async def test_multi_account_delivery_ids_and_buffers_are_independent():
    first, second = EventClient("first"), EventClient("second")
    accounts = {
        "a": AccountConfig("first", client=first),
        "b": AccountConfig("second", client=second),
    }
    async with Client(create_server(accounts=accounts, default_account="a")) as client:
        assert (await client.call_tool("whatsapp_list_accounts")).data == ["a", "b"]
        for key in accounts:
            await client.call_tool("whatsapp_connect", {"account_id": key})
            await client.call_tool("whatsapp_subscribe_messages", {"account_id": key})
        await first.receive({"id": MESSAGE_ID, "body": "account a only"})
        assert (await client.call_tool("whatsapp_get_events", {"account_id": "a"})).data["events"][
            0
        ]["message"]["id"] == MESSAGE_ID
        assert (await client.call_tool("whatsapp_get_events", {"account_id": "b"})).data[
            "events"
        ] == []
        for key in accounts:
            await client.call_tool(
                "whatsapp_send_text",
                {"account_id": key, "chat_id": GROUP_ID, "text": "test", "operation_id": "same"},
            )
        first.context.sendText_.assert_awaited_once()
        second.context.sendText_.assert_awaited_once()
        await client.call_tool("whatsapp_disconnect", {"account_id": "a"})
        assert not first.listeners and second.listeners
        assert (await client.call_tool("whatsapp_status", {"account_id": "b"})).structured_content[
            "ready"
        ]
    assert not first.listeners and not second.listeners


@pytest.mark.asyncio
async def test_different_accounts_do_not_block_each_other():
    first, second = EventClient("one"), EventClient("two")
    await first.connect()
    await second.connect()
    started, gate = asyncio.Event(), asyncio.Event()

    async def read(*args):
        started.set()
        await gate.wait()
        return []

    first.context.getMessages_.side_effect = read
    server = create_server(
        accounts={"a": AccountConfig("one", client=first), "b": AccountConfig("two", client=second)}
    )
    async with Client(server) as client:
        pending = asyncio.create_task(
            client.call_tool("whatsapp_get_messages", {"account_id": "a", "chat_id": GROUP_ID})
        )
        await asyncio.wait_for(started.wait(), 1)
        try:
            result = await asyncio.wait_for(
                client.call_tool("whatsapp_get_messages", {"account_id": "b", "chat_id": GROUP_ID}),
                1,
            )
            assert result.data[0]["id"] == MESSAGE_ID
        finally:
            gate.set()
            await pending


@pytest.mark.asyncio
async def test_event_overflow_cursors_preserve_ids_without_silent_loss():
    buffer = EventBuffer(2)
    for index in range(4):
        await buffer.append({"id": MESSAGE_ID, "n": index})
    page = buffer.read(0, 1)
    assert page["lost"] == 2 and page["cursor"] == 3
    assert page["events"][0]["message"]["id"] == MESSAGE_ID
    assert buffer.read(page["cursor"])["events"][0]["sequence"] == 4
    with pytest.raises(ValueError):
        buffer.read(999)
    await buffer.append({"id": MESSAGE_ID, "body": "x" * 70000, "base64": "private-media"})
    event = buffer.read(4)["events"][0]
    assert event["truncated"] and len(event["message"]["body"]) == 65536
    assert event["message"]["id"] == MESSAGE_ID and "base64" not in event["message"]


@pytest.mark.parametrize("filename", ["../outside", "C:/secret", "https://example.com/file", ""])
def test_media_paths_reject_urls_escape_and_unconfigured_roots(tmp_path, filename):
    runtime = SessionRuntime(EventClient("one"), False, tmp_path)
    with pytest.raises((ValueError, OSError)):
        runtime.media_path(filename)
    with pytest.raises(ValueError):
        SessionRuntime(EventClient("two"), False).media_path("file")


@pytest.mark.asyncio
async def test_new_tools_forward_full_reply_id_and_bounded_media(tmp_path):
    fake = EventClient("one")
    await fake.connect()
    fake.context.getMessages_.return_value = [{"id": MESSAGE_ID, "body": "HELLO"}]
    fake.messages.send_media = AsyncMock(return_value=SimpleNamespace())
    # A dataclass receipt is returned by the real service; use one at this boundary.
    from WPP_Whatsapp.core.delivery_models import DeliveryReceipt, DeliveryState

    fake.messages.send_media.return_value = DeliveryReceipt(
        "file-once", DeliveryState.CONFIRMED, MESSAGE_ID
    )
    fake.messages.download_media_to = AsyncMock(
        return_value={"size": 5, "sha256": "hash", "mimetype": "image/png"}
    )
    (tmp_path / "photo.png").write_bytes(b"image")
    async with Client(create_server(fake, media_root=str(tmp_path))) as client:
        search = await client.call_tool(
            "whatsapp_search_messages", {"chat_id": GROUP_ID, "query": "hello", "scan_limit": 20}
        )
        assert search.data["messages"][0]["id"] == MESSAGE_ID and search.data["scanned"] == 1
        reply = await client.call_tool(
            "whatsapp_reply",
            {
                "chat_id": GROUP_ID,
                "quoted_message_id": MESSAGE_ID,
                "text": "reply",
                "operation_id": "reply-once",
            },
        )
        assert reply.structured_content["state"] == "confirmed"
        fake.context.sendText_.assert_awaited_once_with(
            GROUP_ID, "reply", {"quotedMsg": MESSAGE_ID}
        )
        media = await client.call_tool(
            "whatsapp_send_image",
            {"chat_id": GROUP_ID, "filename": "photo.png", "operation_id": "file-once"},
        )
        assert media.structured_content["state"] == "confirmed"
        assert fake.messages.send_media.call_args.kwargs["kind"] == "image"
        assert fake.messages.send_media.call_args.args[1] == str(tmp_path / "photo.png")
        downloaded = await client.call_tool("whatsapp_download_media", {"message_id": MESSAGE_ID})
        assert Path(downloaded.data["filename"]).name == downloaded.data["filename"]
        assert fake.messages.download_media_to.call_args.args[0] == MESSAGE_ID
        assert (await client.call_tool("whatsapp_diagnostics")).data["ready"]


def test_duplicate_profiles_and_missing_auth_policy_are_rejected():
    with pytest.raises(ValueError, match="profile"):
        create_server(accounts={"a": AccountConfig("same"), "b": AccountConfig("same")})
    with pytest.raises(ValueError, match="session name"):
        create_server(
            accounts={
                "a": AccountConfig("same", token_directory="a"),
                "b": AccountConfig("same", token_directory="b"),
            }
        )
    fake = EventClient("one")
    with pytest.raises(ValueError, match="share a client"):
        create_server(
            accounts={
                "a": AccountConfig("one", client=fake),
                "b": AccountConfig("two", client=fake),
            }
        )
    with pytest.raises(ValueError, match="requires a verified"):
        create_server(access_policy={"someone": {"default": {"read"}}})


@pytest.mark.parametrize("scopes", ["read", {"read": True}, [123]])
def test_malformed_scope_policy_is_rejected(scopes):
    from fastmcp.server.auth import StaticTokenVerifier

    with pytest.raises(ValueError, match="Invalid principal"):
        create_server(auth=StaticTokenVerifier({}), access_policy={"reader": {"default": scopes}})


def test_cli_requires_complete_verified_authentication_for_public_http(capsys):
    from WPP_Whatsapp.mcp.cli import main

    with pytest.raises(SystemExit) as error:
        main(["--transport", "http", "--host", "0.0.0.0"])
    assert error.value.code == 2 and "authentication" in capsys.readouterr().err
    with pytest.raises(SystemExit):
        main(["--transport", "http", "--auth-jwks-uri", "https://issuer.example/keys"])
    assert "issuer, audience and access policy" in capsys.readouterr().err


@pytest.mark.asyncio
async def test_http_jwt_auth_denies_cross_account_and_scope_escalation():
    keys = RSAKeyPair.generate()
    auth = JWTVerifier(
        public_key=keys.public_key, issuer="https://issuer.example", audience="whatsapp"
    )
    first, second = EventClient("one"), EventClient("two")
    await first.connect()
    await second.connect()
    policy = {
        "reader": {"a": {"read"}},
        "operator": {"b": {"read", "send", "events", "diagnostics"}},
    }
    server = create_server(
        accounts={
            "a": AccountConfig("one", client=first),
            "b": AccountConfig("two", client=second),
        },
        auth=auth,
        access_policy=policy,
    )
    # Caller mutations after construction cannot change the server's grant snapshot.
    policy["reader"]["b"] = {"read", "send"}
    app = server.http_app(path="/mcp", stateless_http=True, json_response=True)

    def factory(**kwargs):
        return httpx2.AsyncClient(transport=httpx2.ASGITransport(app=app), **kwargs)

    def transport(token):
        return StreamableHttpTransport(
            "http://localhost/mcp", auth=token, httpx_client_factory=factory
        )

    token = keys.create_token(
        subject="reader",
        issuer="https://issuer.example",
        audience="whatsapp",
        scopes=["whatsapp:read", "whatsapp:send", "whatsapp:events", "whatsapp:diagnostics"],
    )
    async with app.router.lifespan_context(app):
        async with Client(transport(token)) as client:
            assert (await client.call_tool("whatsapp_list_accounts")).data == ["a"]
            assert (
                await client.call_tool("whatsapp_status", {"account_id": "a"})
            ).structured_content["ready"]
            for tool, args in (
                ("whatsapp_get_messages", {"account_id": "b", "chat_id": GROUP_ID}),
                ("whatsapp_list_operations", {"account_id": "b"}),
                ("whatsapp_metrics", {"account_id": "a"}),
                ("whatsapp_claim_event", {"account_id": "a", "consumer_id": "worker"}),
                ("whatsapp_dead_letters", {"account_id": "a", "consumer_id": "worker"}),
                (
                    "whatsapp_complete_event",
                    {
                        "account_id": "a",
                        "consumer_id": "worker",
                        "sequence": 1,
                        "token": "0" * 32,
                        "outcome": "ack",
                    },
                ),
                ("whatsapp_recover_delivery", {"account_id": "a", "operation_id": "blocked"}),
                (
                    "whatsapp_send_text",
                    {
                        "account_id": "a",
                        "chat_id": GROUP_ID,
                        "text": "blocked",
                        "operation_id": "blocked",
                    },
                ),
            ):
                with pytest.raises(ToolError, match="permission unavailable"):
                    await client.call_tool(tool, args)
        # Even policy-granted sends require the scope on the verified token.
        limited = keys.create_token(
            subject="operator",
            issuer="https://issuer.example",
            audience="whatsapp",
            scopes=["whatsapp:read"],
        )
        async with Client(transport(limited)) as client:
            with pytest.raises(ToolError, match="permission unavailable"):
                await client.call_tool(
                    "whatsapp_send_text",
                    {
                        "account_id": "b",
                        "chat_id": GROUP_ID,
                        "text": "blocked",
                        "operation_id": "blocked",
                    },
                )
            for tool, args in (
                ("whatsapp_metrics", {"account_id": "b"}),
                ("whatsapp_claim_event", {"account_id": "b", "consumer_id": "worker"}),
                ("whatsapp_dead_letters", {"account_id": "b", "consumer_id": "worker"}),
                (
                    "whatsapp_complete_event",
                    {
                        "account_id": "b",
                        "consumer_id": "worker",
                        "sequence": 1,
                        "token": "0" * 32,
                        "outcome": "ack",
                    },
                ),
                ("whatsapp_recover_delivery", {"account_id": "b", "operation_id": "blocked"}),
            ):
                with pytest.raises(ToolError, match="permission unavailable"):
                    await client.call_tool(tool, args)
        # Invalid signatures are rejected by the HTTP auth layer before tool execution.
        invalid = RSAKeyPair.generate().create_token(
            issuer="https://issuer.example", audience="whatsapp"
        )
        async with httpx2.AsyncClient(
            transport=httpx2.ASGITransport(app=app), base_url="http://localhost"
        ) as probe:
            response = await probe.post(
                "/mcp", headers={"Authorization": "Bearer " + invalid}, json={}
            )
            assert response.status_code == 401
    first.context.sendText_.assert_not_awaited()
    second.context.sendText_.assert_not_awaited()


@pytest.mark.asyncio
async def test_read_only_account_cannot_send_even_on_writable_server():
    fake = EventClient("one")
    await fake.connect()
    async with Client(
        create_server(accounts={"a": AccountConfig("one", client=fake, read_only=True)})
    ) as client:
        with pytest.raises(ToolError, match="read-only"):
            await client.call_tool(
                "whatsapp_send_text",
                {"chat_id": GROUP_ID, "text": "blocked", "operation_id": "blocked"},
            )
        with pytest.raises(ToolError, match="read-only"):
            await client.call_tool("whatsapp_recover_delivery", {"operation_id": "blocked"})
    fake.context.sendText_.assert_not_awaited()
