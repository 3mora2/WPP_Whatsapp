# Typed reads, diagnostics and bounded media

These additive features are available from version 2.2.0. Existing flat
and service raw dictionary results keep their shapes.

## Typed reads

```python
from WPP_Whatsapp import AsyncClient, Message

client: AsyncClient  # A connected native client owned by the application.
messages: list[Message] = await client.typed.get_messages("123456789@c.us", {"count": 25})
for message in messages:
    print(message.id, message.timestamp, message.from_me)
    original = message.raw  # Independent copy, including unknown upstream fields.

chats = await client.typed.list_chats({"count": 10})
members = await client.typed.get_group_members("123456789@g.us")
group = await client.typed.get_group("123456789@g.us")
```

`Message`, `Chat`, `Group` and `GroupMember` are frozen dataclasses with named fields;
missing optional upstream fields become `None`. Serialized identifiers retain
their complete group/participant suffixes. Invalid/missing identifiers raise
`ValueError`, and absent message lookup returns `None`. `raw` returns a deep copy
so application changes cannot mutate the captured response. `Chat.is_group`
identifies group chats. Python type information is included via `py.typed`.

Synchronous users call `client.services.typed.get_messages(...)`; legacy async
users call `await client.async_services.typed.get_messages(...)`. Existing
`client.getMessages(...)` and `await client.messages.get_messages(...)` return
the original raw data.

## Diagnostics

```python
from WPP_Whatsapp import AsyncClient

client: AsyncClient
report = client.diagnostics()
print(report["state"], report["failure"], report["bridge"], report["events"])
```

Native and legacy clients expose a local `diagnostics()` report with a schema
version, package version, lifecycle state, boolean runtime capabilities and
allowlisted counters. Native startup errors include a fixed phase/category;
exception text, messages, identifiers, options, QR data, tokens and profile paths
are excluded. MCP exposes this report through `whatsapp_diagnostics` under its
own permission. Reports are snapshots, not an automatic upload.

## Media

```python
from WPP_Whatsapp import AsyncClient

client: AsyncClient

async def progress(completed: int, total):
    print(completed, total)

receipt = await client.messages.send_media(
    "123456789@c.us", "report.pdf", kind="document", caption="Report",
    operation_id="report-2026-10", max_bytes=16 * 1024 * 1024,
    progress=progress,
)
download = await client.messages.download_media_to(
    "true_123456789@c.us_MESSAGE", "downloaded.pdf", progress=progress,
)
```

`send_media` supports document, image, video and audio. Core preparation accepts
local paths or HTTP(S); MCP restricts sources to account-local files. A hard byte
limit applies to content-length and actual downloaded bytes. Temporary staging
uses a private directory, chunks are at most 256 KiB, and the default limit is
64 MiB. `send_media` returns the same tracked `DeliveryReceipt` as text sends.
Timeout/cancellation after reserving an operation must be treated as uncertain;
its background execution owns the staged file until completion, then cleans it.
Retries with the same confirmed ID return the saved receipt; unknown IDs never
dispatch again. Never replay under a fresh ID merely because a call timed out.

`download_media_to` creates a destination exclusively, returns size, MIME type
and SHA-256, and removes partial files after failure/cancellation. Existing files
are preserved. WA-JS downloads a full Blob in the browser before chunk transfer;
the browser still needs memory proportional to file size. Legacy base64 media
methods remain available with their original return types and memory behavior.
Legacy HTTP-to-base64 downloads now share bounded preparation and a 64 MiB
default limit, while retaining their data-URI/`False` return contract. They still
buffer the bounded base64 result; local-file legacy converters retain their
original behavior. Network errors are logged without URLs or exception text.

Progress counts bytes transferred to/from the browser, not recipient delivery.
Media gets a preassigned WA-JS message key. Confirmation accepts an ID returned
by the send or a stored outgoing model with that exact key and expected type.
This handles upstream registration waits that lag behind an already queued
message. It never dispatches again and does not wait for a recipient ACK.
Cancellation releases staged/read buffers; it cannot recall a message already
dispatched to WhatsApp. See [delivery semantics](ARCHITECTURE.md#sending-and-uncertain-results)
and [FastMCP configuration](FASTMCP.md).
