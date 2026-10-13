"""Additional reviewed tools; all access goes through account authorization."""

from __future__ import annotations

import uuid
from dataclasses import asdict
from typing import Annotated, Optional

from fastmcp import Context, FastMCP
from fastmcp.exceptions import ToolError
from pydantic import Field

from WPP_Whatsapp.core.delivery_models import DeliveryState
from WPP_Whatsapp.core.errors import DeliveryUncertainError

from .models import DeliveryResult
from .tool_api import READ, SESSION, Identifier, Limit, OperationId, _call, _identifier, _runtime


def register_tools(server: FastMCP, *, read_only: bool):
    @server.tool(annotations={**READ, "openWorldHint": False})
    async def whatsapp_list_accounts(ctx: Context) -> list[str]:
        """List only administrator-configured accounts this verified principal can read."""
        return ctx.lifespan_context["accounts"].visible()

    @server.tool(annotations={**READ, "openWorldHint": False})
    async def whatsapp_diagnostics(ctx: Context, account_id: Optional[Identifier] = None) -> dict:
        """Sanitized state/capability/counter report; no messages, IDs, paths, QR or credentials."""
        runtime = _runtime(ctx, account_id, "diagnostics")

        async def diagnose():
            return runtime.client.diagnostics()

        return await _call(runtime, diagnose, ready=False)

    @server.tool(annotations=READ)
    async def whatsapp_search_messages(
        ctx: Context,
        chat_id: Identifier,
        query: Annotated[str, Field(min_length=1, max_length=1024)],
        scan_limit: Limit = 100,
        before_message_id: Optional[Identifier] = None,
        account_id: Optional[Identifier] = None,
    ) -> dict:
        """Case-insensitive search of ONE history page (max 200). Continue with the scan cursor."""
        runtime = _runtime(ctx, account_id)
        return await _call(
            runtime,
            lambda: runtime.client.messages.search(
                _identifier(chat_id), query, count=scan_limit, before_message_id=before_message_id
            ),
        )

    @server.tool(annotations={**SESSION, "idempotentHint": True})
    async def whatsapp_subscribe_messages(
        ctx: Context,
        account_id: Optional[Identifier] = None,
    ) -> dict:
        """Start this account's bounded live buffer. Keep the cursor to read subsequent events."""
        runtime = _runtime(ctx, account_id, "events")

        async def subscribe():
            runtime.subscribe()
            return {"cursor": runtime.events.sequence, "capacity": runtime.events.items.maxlen}

        return await _call(runtime, subscribe)

    @server.tool(annotations=READ)
    async def whatsapp_get_events(
        ctx: Context,
        after: Annotated[int, Field(ge=0)] = 0,
        limit: Limit = 50,
        account_id: Optional[Identifier] = None,
    ) -> dict:
        """Read buffered incoming messages; lost reports overflow. Subscription starts explicitly."""
        runtime = _runtime(ctx, account_id, "events")

        async def read():
            return runtime.events.read(after, limit)

        return await _call(runtime, read, ready=False)

    @server.tool(annotations={**READ, "readOnlyHint": False})
    async def whatsapp_download_media(
        ctx: Context,
        message_id: Identifier,
        account_id: Optional[Identifier] = None,
    ) -> dict:
        """Save media under this account's configured media root; return relative name/hash/size."""
        runtime = _runtime(ctx, account_id)

        async def download():
            if runtime.media_root is None or not runtime.media_root.is_dir():
                raise ToolError("Configure an existing media root for this account first")
            name = uuid.uuid4().hex + ".bin"
            destination = runtime.media_root / name
            result = await runtime.client.messages.download_media_to(
                _identifier(message_id), str(destination), progress=progress
            )
            return {"filename": name, **result}

        async def progress(done, total):
            await ctx.report_progress(progress=done, total=total)

        return await _call(runtime, download)

    if read_only:
        return

    async def tracked(runtime, action):
        try:
            runtime.tracker = runtime.client.messages.deliveries
            return asdict(await action())
        except DeliveryUncertainError as error:
            return {
                "operation_id": error.operation_id,
                "state": DeliveryState.UNKNOWN,
                "message_id": None,
            }

    @server.tool(annotations={**SESSION, "idempotentHint": True})
    async def whatsapp_reply(
        ctx: Context,
        chat_id: Identifier,
        quoted_message_id: Identifier,
        text: Annotated[str, Field(min_length=1, max_length=65536)],
        operation_id: OperationId,
        account_id: Optional[Identifier] = None,
    ) -> DeliveryResult:
        """Send a tracked text reply. Preserve the complete quoted message ID and operation ID."""
        runtime = _runtime(ctx, account_id, "send")
        return await _call(
            runtime,
            lambda: tracked(
                runtime,
                lambda: runtime.client.messages.send_text(
                    _identifier(chat_id),
                    text,
                    {"quotedMsg": _identifier(quoted_message_id)},
                    operation_id=_identifier(operation_id),
                ),
            ),
        )

    async def send_media(ctx, chat_id, filename, operation_id, caption, account_id, kind):
        runtime = _runtime(ctx, account_id, "send")

        async def progress(done, total):
            await ctx.report_progress(progress=done, total=total)

        async def send():
            path = runtime.media_path(filename)
            return await tracked(
                runtime,
                lambda: runtime.client.messages.send_media(
                    _identifier(chat_id),
                    str(path),
                    kind=kind,
                    caption=caption,
                    operation_id=_identifier(operation_id),
                    progress=progress,
                ),
            )

        return await _call(runtime, send)

    @server.tool(annotations={**SESSION, "idempotentHint": True})
    async def whatsapp_send_file(
        ctx: Context,
        chat_id: Identifier,
        filename: Identifier,
        operation_id: OperationId,
        caption: Annotated[str, Field(max_length=4096)] = "",
        account_id: Optional[Identifier] = None,
    ) -> DeliveryResult:
        """Send a document relative to the account's media root (64 MiB max); never accept a URL."""
        return await send_media(
            ctx, chat_id, filename, operation_id, caption, account_id, "document"
        )

    @server.tool(annotations={**SESSION, "idempotentHint": True})
    async def whatsapp_send_image(
        ctx: Context,
        chat_id: Identifier,
        filename: Identifier,
        operation_id: OperationId,
        caption: Annotated[str, Field(max_length=4096)] = "",
        account_id: Optional[Identifier] = None,
    ) -> DeliveryResult:
        """Send an image relative to the account's media root (64 MiB max), with tracked delivery."""
        return await send_media(ctx, chat_id, filename, operation_id, caption, account_id, "image")
