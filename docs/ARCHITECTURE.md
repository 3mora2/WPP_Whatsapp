# Async core, services and migration

The native `AsyncClient` owns Playwright on the caller's running event loop.
`Create` and `ThreadsafeBrowser` retain the synchronous API using one dedicated
loop per browser runtime. All browser operations, event bindings and session
construction run on that runtime's owning loop. Python 3.9+ is supported.

## Native async client

```python
import asyncio
from WPP_Whatsapp import AsyncClient

async def main():
    async with AsyncClient("mybot", autoClose=0) as client:
        async def incoming(message):
            original = await client.messages.get_message(message["id"])
            print("Message lookup succeeded:", original["id"] == message["id"])

        client.events.on_message(incoming)
        chats = await client.chats.list_chats({"count": 10})
        print("Chats loaded:", len(chats))
        await asyncio.Event().wait()

asyncio.run(main())
```

Log in in the new browser. `autoClose=0` disables the QR login auto-close timer.
The default browser is installed Chrome; set `channel=None` to use Playwright's
Chromium after installing it. Use an `AsyncClient` from one event loop only.
Concurrent `connect()` calls are serialized. `await client.reconnect()` closes
and reopens this session's profile without replaying operations.

Service objects are composed over one operation context: `messages`, `chats`,
`groups`, `catalog`, `communities`, `newsletters`, `profile`, `labels`, `lists`,
`status` and `events`. API methods use snake_case, such as `get_all_messages_in_chat`
and `create_group`. Services require a ready session before browser operations.

Definitions in `core/service_registry.py` control the service surface. Adding a
definition extends the native client and sync adapter without duplicate name
lists. Internal cleanup and injection methods are excluded from message services.
See the [development guide](DEVELOPMENT.md) for extension and quality conventions.

The legacy layer classes remain available as operation providers. `Whatsapp`
has a flat compatibility facade instead of inheriting their full chain. It
preserves existing method names, argument shapes, sync/async suffixes and raw
return values. The service API is additive; tracked send services return receipts.

## Existing sync callers

```python
from WPP_Whatsapp import Create

with Create(session="mybot", autoClose=0) as client:
    chats = client.listChats({"count": 10})          # Existing API
    chats = client.services.chats.list_chats({"count": 10})
```

Async users of the legacy factory can still use `async with Create(...)` and
`await client.getMessages_(...)`. `client.async_services` exposes the same async
services used by `AsyncClient`. Synchronous methods must not be invoked on the
browser's owner loop; synchronous callbacks run off that loop and can call them.

## Sending and uncertain results

```python
from WPP_Whatsapp import AsyncClient
from WPP_Whatsapp.core.errors import DeliveryUncertainError

client: AsyncClient  # A connected native client supplied by the application.
try:
    receipt = await client.messages.send_text(
        "123456789@c.us", "Hello", operation_id="invoice-123", timeout=30)
    print(receipt.state.value, receipt.message_id)
except DeliveryUncertainError as error:
    receipt = client.messages.deliveries.get(error.operation_id)
    # Inspect the outgoing chat / delivery state. Do not blindly resend.
```

Message-producing `messages.send_*` and `messages.reply` operations share a
delivery ledger. Presence, read receipts, reactions and forwarding retain their
ordinary return values. Existing flat `client.sendText(...)` methods retain raw
results and their historical timeout exceptions; use services for delivery tracking.

| State | Meaning |
| --- | --- |
| `pending` | The operation has been claimed and is running. |
| `confirmed` | WA-JS returned a nonempty message ID, or an outgoing message was verified by lookup. This alone does not prove recipient delivery/read. |
| `failed` | A local operation failed without a confirmed result. Its ID is still reserved. |
| `unknown` | Dispatch may have occurred, but its result cannot yet be established. |

Reusing a confirmed operation ID returns the existing receipt. Reusing any other
reserved ID raises `DeliveryUncertainError` and never dispatches a second send.
A timeout or caller cancellation leaves the underlying operation running; a
later valid result can change `unknown` to `confirmed`. An absent result ID is
never treated as success. Use `await client.messages.reconcile(operation_id,
message_id)` only for an actual outgoing message; it validates lookup and `fromMe`.

The ledger is in memory by default. Set `deliveryStore="tokens/delivery.sqlite3"`
to persist operation IDs, states, message IDs and timestamps per session. No
recipient, content, media or credentials are written to this ledger. Pending
records are treated as unknown after reopening it. SQLite claims also prevent
two ledger instances from dispatching the same session/operation ID. Keep the
store across restarts when restart-safe deduplication is needed; deleting it or
changing the operation ID removes that protection. Persistence does not provide
server-side exactly-once delivery.

Opening another tracker does not rewrite the active owner's pending state.
Storage adapters are separate from tracking policy; blocking claims, state
updates and async cleanup run off the browser loop. Persistence failure after a
send raises `DeliveryUncertainError`. A closed tracker rejects new sends.

## Events and lifecycle

Each session has its own ordered queue (`eventQueueSize=256` by default).
Sync and async callbacks run in registration order; a callback failure is
isolated and only its exception type is logged. `onMessage` and `onAnyMessage`
deduplicate recent IDs independently (up to 4096 remembered event/ID pairs).
Overflow raises `EventQueueFullError` and increments `client.events.stats["rejected"]`;
there is no silent overwrite or automatic redelivery. Increase queue size or
reduce callback work when the counter grows. Closing cancels queued work;
already running synchronous callback threads must return cooperatively.

States include `new`, `starting`, `waiting_qr`, `syncing`, `ready`, `reconnecting`,
`closing`, `closed` and `failed`. Native connection events update these states.
Profile leases reject concurrent ownership without terminating another browser.
`MultiCreate` closes only the selected session's context when that client closes;
`close_all()` releases all contexts and stops its own worker loop.

| Option | Unit / default |
| --- | --- |
| `autoClose` | Seconds; legacy QR auto-close, `0` disables it. |
| `deviceSyncTimeout` | Milliseconds; upstream default `180000`, `0` disables it. |
| `navigationTimeout` | Milliseconds; `60000`. |
| `runtimeReadyTimeout` | Milliseconds; `30000`. |
| `pageLoadTimeout` | Seconds; `120`. |
| `operationTimeout` | Seconds; service sends default to `60`, `0` disables it. |

Deadline accounting uses a monotonic clock. Timers measure elapsed time instead
of counting polling iterations. Shutdown is idempotent and clears listeners,
intervals, delivery storage, owned contexts, profile leases and the owned driver.
`close_already_profile=True` is intentionally rejected: close the profile's owner
explicitly instead. Optional `stealthy=True` requires `pip install
"WPP_Whatsapp[stealth]"`; the default install does not include stealth patches.

## JavaScript and runtime updates

`core/commands.py` contains the typed Python dictionary used as the single command
registry for Python API evaluations. The bridge imports it directly; no JSON
registry is loaded at runtime.
`JavascriptBridge` binds commands to one session page, records aggregate timings
and reports errors without message payloads. Contract tests compile the registry,
check referenced upstream exports and verify argument/return shapes.

Startup discovers the latest stable WA-JS release before consulting its asset
cache. Cached release assets are SHA-256 checked against local metadata; corruption
causes a fresh download. This detects cache corruption, not publisher authenticity.
Nightly/custom URLs are fetched each time because their content can change.
`runtimeCacheDir` can override the default `tokens/.runtime-cache` location.
Download/discovery failure uses the packaged runtime. If the latest runtime
cannot initialize required capabilities, startup reloads once and tries the
packaged runtime before exposing operations. Explicit versions/URLs/files fail
instead of silently selecting another runtime. `wa_js_version="bundled"` skips
WA-JS discovery/download; WhatsApp Web itself still requires network access.

## Optional MCP integration

The [FastMCP server](FASTMCP.md) uses the native client and creates it lazily
per server lifespan. Its explicit tools serialize browser operations with
connect/disconnect, while local status remains available during startup. One
server owns one profile shared by its MCP clients. It defaults to persistent
session-scoped delivery metadata, exposes structured uncertain receipts and
keeps QR/login in the browser. Injected clients retain caller ownership/options.

## Releases and recovery

Publishing a GitHub release still triggers the complete test/build/PyPI workflow.
It verifies the published release, resolves its tag to an immutable commit,
checks `project.version`, tests the core on Python 3.9–3.12 and MCP on Python
3.10/3.12, checks documentation and builds that commit. Both wheel
and sdist are checked against every packaged source/runtime byte before upload.

For an interrupted publication, run **Test, Build & Upload Python Package**
manually and set `release_tag` to the already published release tag. A branch
name or draft release is rejected. Validation code comes from the workflow
commit so recovery also supports older tags. Existing PyPI files are skipped
during upload, then their metadata, SHA-256 and complete package payloads are
verified against the selected source. A mismatch fails the run. The post-upload
check retries temporary visibility/network failures for a bounded period.

Local build verification: `python tools/verify_release.py dist --dist dist`.
The `pypi` command additionally compares those artifacts with the published
version; it never uploads anything. Select the exact release source when checking
payloads. Windows checkout CRLF bytes can differ from Linux CI LF bytes; use
the tagged Git blobs and CI artifacts for exact publication comparisons.
