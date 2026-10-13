"""Guide contracts and runnable example boundaries without browser/account access."""

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import pytest

from tools.verify_docs import link_errors, recipe_errors, verify
from WPP_Whatsapp.core.errors import DeliveryUncertainError


def test_guides_examples_links_and_generated_signatures_are_current():
    documents, errors = verify()
    assert len(documents) >= 24
    assert not errors, "\n".join(errors)


def test_link_validation_rejects_missing_files_and_headings(tmp_path):
    path = tmp_path / "guide.md"
    path.write_text("# Existing heading\n", encoding="utf-8")
    assert not link_errors(path, "[valid](#existing-heading)")
    assert len(link_errors(path, "[missing](absent.md) [bad anchor](#absent)")) == 2
    assert link_errors(
        path, "[missing](https://github.com/3mora2/WPP_Whatsapp/blob/main/docs/ABSENT.md)"
    )


@pytest.mark.parametrize(
    "recipe",
    [
        "client.decryptFile(message)",
        "client.sendLocation(chat_id, latitude=1, longitude=2)",
        'client = Create("example")\nclient.sendText(chat_id, "bad factory use")',
        "return 1",
    ],
)
def test_recipe_validation_rejects_removed_names_wrong_arguments_and_invalid_python(recipe):
    assert recipe_errors(recipe, "invalid-recipe")


@pytest.mark.asyncio
async def test_router_awaits_async_client_operations_and_handles_empty_body():
    from scripts.advanced_message_handler import router

    client = SimpleNamespace(sendText_=AsyncMock())
    await router.handle(client, {"from": "synthetic@c.us", "body": None})
    client.sendText_.assert_not_awaited()
    await router.handle(client, {"from": "synthetic@c.us", "body": "/ping"})
    client.sendText_.assert_awaited_once()


def test_download_example_preserves_existing_output_before_starting_browser(tmp_path):
    from examples import download

    output = tmp_path / "existing.bin"
    output.write_bytes(b"keep")
    with (
        patch("sys.argv", ["download.py", "synthetic-id", str(output)]),
        patch.object(download, "Create") as creator,
    ):
        with pytest.raises(SystemExit):
            download.main()
    creator.assert_not_called()
    assert output.read_bytes() == b"keep"


def test_download_example_decodes_selected_media(tmp_path):
    from examples import download

    output = tmp_path / "new.bin"
    client = SimpleNamespace(
        downloadMedia=Mock(return_value="data:application/octet-stream;base64,aGVsbG8=")
    )
    creator = Mock()
    creator.return_value.__enter__ = Mock(return_value=client)
    creator.return_value.__exit__ = Mock(return_value=False)
    with (
        patch("sys.argv", ["download.py", "complete-message-id", str(output)]),
        patch.object(download, "Create", creator),
    ):
        download.main()
    client.downloadMedia.assert_called_once_with("complete-message-id")
    assert output.read_bytes() == b"hello"


@pytest.mark.asyncio
async def test_bulk_template_stops_on_uncertainty_and_closes_owned_client():
    from scripts import bulk_sender

    client = SimpleNamespace(
        messages=SimpleNamespace(send_text=AsyncMock(side_effect=DeliveryUncertainError("batch:0")))
    )
    owner = AsyncMock()
    owner.__aenter__.return_value = client
    args = SimpleNamespace(
        session="synthetic",
        delivery_store="unused.sqlite3",
        recipients=["one@c.us", "two@c.us"],
        text="synthetic",
        operation_prefix="batch",
    )
    with patch.object(bulk_sender, "AsyncClient", return_value=owner):
        with pytest.raises(DeliveryUncertainError):
            await asyncio.wait_for(bulk_sender.send_batch(args), 1)
    client.messages.send_text.assert_awaited_once_with(
        "one@c.us", "synthetic", operation_id="batch:0"
    )
    owner.__aexit__.assert_awaited_once()
