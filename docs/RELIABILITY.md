# Reliability services

For pre-dispatch message recovery, acknowledged consumers, administration,
metrics and generated types in the 2.4.0 candidate, see [operations](OPERATIONS.md).

These additions preserve flat legacy methods and raw read results. Tracked
composed sends enforce request identity. Recovery and durable events are opt-in.

## Request identity and migration

`operation_id` identifies one intended send within a session. The tracker now
atomically binds it to a SHA-256 digest of the canonical operation arguments.
Changes to recipient, text, options, media kind, caption, quoted message, filename
or media bytes raise `OperationConflictError` before a second dispatch. Equivalent
positional/keyword calls and defaults normalize through the operation signature.

Media identity uses an immutable, bounded temporary copy of the bytes actually
sent. A duplicate media request must still prepare its source to verify identity.
Timeout does not remove the snapshot while its original dispatch is running.

The SQLite migration adds a nullable fingerprint column without deleting data.
Old receipts remain readable. A pre-2.3 record cannot prove a new request's
identity, so tracked services reject reusing it with `OperationConflictError`.
Inspect or reconcile the existing operation; an old unknown receipt never grants
permission to resend. The low-level `DeliveryTracker.send()` retains its unbound
compatibility mode when no `request_fingerprint` is supplied. Custom delivery
stores implement `claim_request()` for atomic identity-aware reservation.

Only digests and delivery metadata are stored, not send bodies. Digests are not
encryption and can reveal equality or permit guessing of low-entropy requests.
Treat the database as private. Do not prune operation IDs while clients may reuse
them: removing a reservation removes its duplicate protection.

## Durable incoming events

```bash
wpp-whatsapp-mcp --session mybot --event-store tokens/.events/mybot.sqlite3 \
  --event-buffer-size 1000 --event-retention-seconds 86400
```

Call `whatsapp_subscribe_messages` after connecting. Save the cursor returned by
each `whatsapp_get_events` page. To resume after restarting the server, pass your
previously saved cursor; the subscription's current cursor starts from now.
Sequence allocation and duplicate detection are atomic across writers and
isolated by session namespace. Recent full message IDs are deduplicated within
the retained journal. Count and age pruning retain a persistent high-water cursor;
`lost` explicitly reports the discarded prefix. Expired IDs may be admitted again.

The default is still a 256-event in-memory buffer. Durable storage opens lazily
on first use. Unlike delivery metadata, the event journal **contains incoming
message bodies and sender IDs**; protect its directory and choose an appropriate
retention period. Media/base64 and arbitrary upstream fields are excluded; bodies
are capped at 65,536 characters with `truncated=true`. No historical backfill or
exactly-once processing is promised. Consumers must commit their own work/cursors.

## Bounded recovery and subscriptions

```python
from WPP_Whatsapp import AsyncClient

native = AsyncClient(
    "mybot", reconnectAttempts=3, reconnectInitialDelay=1,
    reconnectMaxDelay=30, reconnectAttemptTimeout=30,
)
```

Recovery is disabled by default (`reconnectAttempts=0`). Transient connection
events and browser page crash/close schedule at most one recovery task. Each
attempt has a timeout; delays double up to the configured ceiling. Recovery stops
for unpairing/login, incompatible runtime or a profile already owned elsewhere.
If the existing transport becomes ready before the delay ends, no reopen occurs.
Explicit `close()` cancels recovery; explicit connect/reconnect can restart it.
Exhausting the retry budget blocks further attempts until an explicit connection
request or a verified healthy connection; repeated outage events cannot reset it.
No previous send, read, or user action is replayed.

Register through `native.events` to preserve subscriptions across replacement
contexts. Registrations made directly on the legacy context belong to that context.
MCP subscriptions also survive manual reconnect. Recovery does not fill gaps while
offline; durable journals preserve only events actually received.

## Queued, delivered and read are separate

```python
receipt = await native.messages.send_text(
    "123456789@c.us", "Requested message", operation_id="invoice-42",
)
status = await native.messages.delivery_status(receipt.operation_id)
status = await native.messages.wait_for_delivery(
    receipt.operation_id, target="delivered", timeout=30,
)
```

`confirmed` still means a queued/verified outgoing message ID. ACK observation
uses matching complete IDs and refreshes missed events from a verified outgoing
message lookup. Targets are `server`, `delivered`, `read`, and `played`.
Negative ACK codes indicate failure; missing evidence remains unknown. WA-JS's
separate `PEER=5` signal is not classified as delivery/read. Read receipts may be
unavailable. A group ACK is the upstream aggregate, not a per-participant report.
ACK codes follow the [upstream enum](https://wppconnect.io/wa-js/enums/whatsapp.enums.ACK.html).
Timeout raises `AcknowledgementTimeoutError`; closing the session ends waiting.
Neither timeout nor cancellation sends a message. ACKs are refreshed from WhatsApp
after restart; they are not a second durable local delivery ledger.

MCP exposes the read-only `whatsapp_delivery_status` and
`whatsapp_wait_for_delivery` (maximum 120 seconds). There are 29 tools, 23 with
`--read-only`. Each tool retains account authorization and verified JWT scopes.

## Admission, pacing and measurement

| Setting | Default | Meaning |
| --- | --- | --- |
| `maxConcurrentOperations` | 4 | Concurrent composed operations per session. |
| `maxPendingOperations` | 64 | Total admitted active and waiting operations. |
| `sendRateCalls` | 0 | Disabled; positive value enables the existing rate limiter. |
| `sendRatePeriod` | 60 seconds | Window for the configured number of send calls. |

Overload raises `OperationQueueFullError`. MCP rejects admission before invoking
the action. At the core tracker boundary a rejected reserved send can be recorded
as failed; inspect its receipt before deciding what to do. Cancellation releases
waiting admission. A timed-out dispatched operation keeps its own active slot
until it finishes; it is never silently replayed. Flat legacy calls keep their
existing scheduling behavior.

MCP allows bounded concurrent reads/media operations while lifecycle transitions
wait for active work and prevent new reads overtaking them. Local status/metadata
do not wait behind a media transfer. Pacing limits throughput; it does not guarantee
WhatsApp account safety. Browser media still requires a full File/Blob.

Run `python tools/soak_runtime.py --report archive/runtime-soak.json` to measure
synthetic journal throughput, restart continuity, bounded retention and Python
allocation/latency. This does not open a browser, prove production performance,
or replace multi-hour live-account testing. See [tests](../tests/README.md) and
the [HTTP](../examples/fastapi_app.py) / [MCP](../examples/reliable_mcp.py) templates.
