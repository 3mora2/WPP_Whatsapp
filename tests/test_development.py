"""Compatibility, typed reads, bounded transfers and sanitized diagnostics."""

import asyncio
import base64
import inspect
import json
import os
from dataclasses import FrozenInstanceError
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import pytest
from playwright.async_api import Error

from tests.helpers import eventually, ready_context
from WPP_Whatsapp import AsyncClient, Chat, Group, GroupMember, Message, Whatsapp
from WPP_Whatsapp.core.delivery_models import DeliveryState
from WPP_Whatsapp.core.diagnostics import classify_failure, snapshot
from WPP_Whatsapp.core.engine import AsyncBrowser
from WPP_Whatsapp.core.errors import BridgeError, DeliveryUncertainError, ProfileInUseError
from WPP_Whatsapp.core.lifecycle import SessionState
from WPP_Whatsapp.core.media import CHUNK_BYTES, MediaTooLargeError, download_to, prepare_media
from WPP_Whatsapp.core.services import ServiceHub, SyncServices

MID = "false_123@g.us_ABC_456@lid"


def test_typed_models_preserve_ids_unknown_fields_and_missing_values():
    raw = {
        "id": {"_serialized": MID},
        "body": "hello",
        "fromMe": False,
        "t": 100,
        "future": {"field": [1]},
    }
    message = Message.from_raw(raw)
    raw["future"]["field"].append(2)
    assert message.id == MID and message.timestamp == 100 and message.from_me is False
    assert message.raw["future"] == {"field": [1]}
    exported = message.raw
    exported["future"].clear()
    assert message.raw["future"] == {"field": [1]}
    with pytest.raises(FrozenInstanceError):
        message.body = "changed"
    assert Message.from_raw({"id": MID}).from_me is None
    assert Message.from_raw({"id": MID, "t": True}).timestamp is None
    with pytest.raises(ValueError):
        Message.from_raw({"body": "no id"})
    assert Chat.from_raw({"id": "123@g.us", "name": "group"}).is_group
    assert GroupMember.from_raw({"id": {"_serialized": "456@lid"}}).is_admin is None
    group = Group.from_raw(
        {
            "id": "123@g.us",
            "groupMetadata": {
                "owner": {"_serialized": "456@lid"},
                "desc": "description",
                "participants": [{"id": "456@lid", "isAdmin": True}],
            },
        }
    )
    assert group.owner_id == "456@lid" and group.participants[0].is_admin is True
    with pytest.raises(ValueError, match="group chat"):
        Group.from_raw({"id": "123@c.us"})


@pytest.mark.asyncio
async def test_typed_services_are_additive_and_do_not_change_raw_results():
    raw = {"id": MID, "future": 1}
    context = ready_context(
        getMessageById_=AsyncMock(return_value=raw),
        getMessages_=AsyncMock(return_value=[raw]),
        listChats_=AsyncMock(return_value=[{"id": "123@g.us"}]),
        getGroupMembers_=AsyncMock(return_value=[{"id": "456@lid"}]),
    )
    hub = ServiceHub(context)
    assert await hub.messages.get_message(MID) is raw
    assert (await hub.typed.get_message(MID)).raw == raw
    assert (await hub.typed.get_messages("123@g.us"))[0].id == MID
    assert (await hub.typed.list_chats())[0].is_group
    assert (await hub.typed.get_group_members("123@g.us"))[0].id == "456@lid"
    context.getMessageById_.return_value = None
    assert await hub.typed.get_message("missing") is None
    # The sync view uses the owning browser adapter too.
    context.ThreadsafeBrowser.run_threadsafe = lambda task, **kw: task
    assert (await SyncServices(hub).typed.list_chats())[0].is_group


@pytest.mark.asyncio
async def test_bounded_search_advances_past_nonmatching_messages():
    messages = [{"id": "old", "body": "unrelated"}, {"id": MID, "body": "HELLO"}]
    getter = AsyncMock(return_value=messages)
    service = ServiceHub(ready_context(getMessages_=getter)).messages
    result = await service.search("123@g.us", "hello", count=2, before_message_id="cursor")
    assert result == {"messages": [messages[1]], "scanned": 2, "before_message_id": "old"}
    getter.assert_awaited_once_with("123@g.us", {"count": 2, "id": "cursor", "direction": "before"})
    for value in (0, 201, True):
        with pytest.raises(ValueError):
            await service.search("group", "query", count=value)
    getter.return_value = [
        {"id": "new", "timestamp": 3},
        {"id": "old", "timestamp": 1},
        {"id": "appended-anchor", "timestamp": 4},
    ]
    assert (await service.search("group", "absent"))["before_message_id"] == "old"


def test_support_report_does_not_serialize_private_context_or_error():
    secret = "private-body-token-profile-number"
    context = SimpleNamespace(
        options={"secret": secret},
        session=secret,
        runtime_capabilities={"version": secret, "ready": True, "events": False},
        bridge=SimpleNamespace(metrics={"calls": 2, "failures": 1, "secret": secret}),
        _dispatcher=SimpleNamespace(stats={"delivered": 3, "message": secret}),
    )
    failure = classify_failure("browser_start", ProfileInUseError(secret))
    report = snapshot(SessionState.FAILED, context, failure)
    assert secret not in json.dumps(report)
    assert report["failure"] == {"phase": "browser_start", "category": "profile_in_use"}
    assert report["bridge"] == {"calls": 2, "failures": 1}
    assert AsyncClient().diagnostics()["state"] == "new"


def test_all_refactored_sync_wrappers_preserve_binding_and_timeout():
    client = object.__new__(Whatsapp)
    calls = []
    client.ThreadsafeBrowser = SimpleNamespace(run_threadsafe=lambda *a, **k: calls.append((a, k)))
    count = 0
    for name in dir(Whatsapp):
        wrapper = getattr(Whatsapp, name)
        if (
            not hasattr(wrapper, "__wrapped__")
            or "async_name" not in inspect.getclosurevars(wrapper).nonlocals
        ):
            continue
        count += 1
        signature = inspect.signature(wrapper)
        params = list(signature.parameters.values())[1:]
        args = [object() for parameter in params if parameter.name != "timeout"]
        getattr(client, name)(*args, 3.25)
        actual_args, actual_kwargs = calls[-1]
        assert actual_kwargs.pop("timeout_") == 3.25
        assert not actual_kwargs
        assert list(actual_args[1:]) == args
        inspect.signature(actual_args[0]).bind(*actual_args[1:])
        with pytest.raises(TypeError):
            getattr(client, name)(unexpected_argument=True)
    assert count >= 150  # Inherited overrides can hide a declaration on the flat facade.


@pytest.mark.asyncio
async def test_local_media_is_bounded_reports_progress_and_cleans_temp_files(tmp_path):
    source = tmp_path / "file.bin"
    source.write_bytes(b"x" * (CHUNK_BYTES + 3))
    progress = []
    async with prepare_media(
        source, progress=lambda done, total: progress.append((done, total))
    ) as media:
        staged = media.path
        assert media.size == source.stat().st_size and staged.read_bytes() == source.read_bytes()
    assert not staged.exists() and progress[-1] == (CHUNK_BYTES + 3, CHUNK_BYTES + 3)
    with pytest.raises(MediaTooLargeError):
        async with prepare_media(source, max_bytes=CHUNK_BYTES):
            pytest.fail("Oversized media must not reach dispatch")
    with pytest.raises(asyncio.CancelledError):
        async with prepare_media(source) as media:
            cancelled = media.path
            raise asyncio.CancelledError()
    assert not cancelled.exists()


@pytest.mark.asyncio
async def test_http_media_enforces_unknown_length_limit_and_cancellation(tmp_path, caplog):
    async def chunks(size):
        yield b"a" * 6
        yield b"b" * 6

    reply = SimpleNamespace(
        content_length=None,
        content_type="image/png",
        raise_for_status=lambda: None,
        content=SimpleNamespace(iter_chunked=chunks),
    )
    response = Mock(
        __aenter__=AsyncMock(return_value=reply), __aexit__=AsyncMock(return_value=False)
    )
    session = Mock(get=Mock(return_value=response))
    manager = Mock(
        __aenter__=AsyncMock(return_value=session), __aexit__=AsyncMock(return_value=False)
    )
    with patch("WPP_Whatsapp.core.media.aiohttp.ClientSession", return_value=manager):
        with pytest.raises(MediaTooLargeError):
            async with prepare_media("https://example.test/media", max_bytes=10):
                pytest.fail("Chunked responses must enforce the actual byte limit")
        from WPP_Whatsapp.api.helpers.download_file import downloadFileToBase64

        assert (
            await downloadFileToBase64("https://example.test/secret-token", max_bytes=10) is False
        )
        assert "secret-token" not in caplog.text


@pytest.mark.asyncio
async def test_media_timeout_keeps_temp_until_late_confirmation_and_never_resends(tmp_path):
    source = tmp_path / "file.bin"
    source.write_bytes(b"media")
    context = ready_context()
    service = ServiceHub(context).messages
    gate, started = asyncio.Event(), asyncio.Event()
    staged = []

    async def send(context, to, media, **kwargs):
        staged.append(media.path)
        started.set()
        await gate.wait()
        assert media.path.exists()
        return {"id": MID}

    with patch("WPP_Whatsapp.core.services.send_prepared", side_effect=send) as dispatch:
        with pytest.raises(DeliveryUncertainError):
            await service.send_media("123@g.us", str(source), operation_id="once", timeout=0.01)
        assert started.is_set() and staged[0].exists()
        with pytest.raises(DeliveryUncertainError):
            await service.send_media("123@g.us", str(source), operation_id="once")
        gate.set()
        await eventually(lambda: service.deliveries.get("once").state == DeliveryState.CONFIRMED)
        assert not staged[0].exists() and dispatch.call_count == 1


@pytest.mark.asyncio
async def test_download_refuses_overwrite_and_removes_partial_files(tmp_path):
    target = tmp_path / "file"
    evaluate = AsyncMock(
        side_effect=[{"size": 4, "mimetype": "image/png"}, base64.b64encode(b"part").decode(), None]
    )
    context = SimpleNamespace(
        ThreadsafeBrowser=SimpleNamespace(page_evaluate=evaluate), page=object()
    )
    result = await download_to(context, MID, target)
    assert result["size"] == 4 and target.read_bytes() == b"part"
    evaluate.side_effect = [{"size": 4, "mimetype": "image/png"}, None]
    with pytest.raises(FileExistsError):
        await download_to(context, MID, target)
    assert target.read_bytes() == b"part"
    target.unlink()
    evaluate.side_effect = [{"size": 4, "mimetype": "image/png"}, Error("private token"), None]
    with pytest.raises(BridgeError):
        await download_to(context, MID, target)
    assert not target.exists()


@pytest.mark.skipif(
    os.getenv("RUN_WHATSAPP_BROWSER_TESTS") != "1" or os.getenv("CI") == "true",
    reason="Opt-in native Chrome file/Blob transfer test",
)
@pytest.mark.asyncio
async def test_real_browser_file_upload_and_blob_download_are_byte_exact(tmp_path):
    from WPP_Whatsapp.core.media import send_prepared

    browser = AsyncBrowser()
    await browser.open(user_data_dir=tmp_path / "profile", channel="chrome", headless=True)
    context = SimpleNamespace(ThreadsafeBrowser=browser, page=browser.page)
    payload = bytes(range(256)) * 2049
    source = tmp_path / "source.bin"
    source.write_bytes(payload)
    try:
        await browser.page_evaluate(
            """() => { window.WPP = {chat: {
            find: async id => ({id}),
            generateMessageID: async () => ({_serialized: 'uploaded'}),
            sendFileMessage: async (to, file) => {
                if (!(file instanceof File)) throw new Error('Expected File');
                window.testMedia = file;
                const id = Object.create({get _serialized() {return 'uploaded';}});
                return {id, ack: 1, sendMsgResult: Promise.resolve('OK')};
            }, downloadMedia: async () => window.testMedia
        }}; }""",
            page=browser.page,
        )
        async with prepare_media(source) as media:
            assert (await send_prepared(context, "123@c.us", media, kind="document"))[
                "id"
            ] == "uploaded"
        target = tmp_path / "download.bin"
        result = await download_to(context, "uploaded", target)
        assert result["size"] == len(payload) and target.read_bytes() == payload
        assert await browser.page_evaluate("() => window.__wppMedia.size", page=browser.page) == 0
    finally:
        await browser.close()
