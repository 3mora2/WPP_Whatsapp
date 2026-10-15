# Operating persistent clients (2.4.0)

These APIs are additive. Flat legacy methods retain raw results. No recovery or
administration command automatically resends a message.

## Recover an interrupted send

Configure `deliveryStore` for persistence. Native/composed `send_text` and
`send_media` allocate a complete outgoing key and commit its key, canonical chat
ID and message type **before dispatch**. The request digest still identifies the
original arguments and bytes. Bodies and media are absent from the delivery
ledger, but the new recipient metadata requires private storage.

```python
from WPP_Whatsapp import AsyncClient

async def recover_existing(operation_id):
    native = AsyncClient("mybot", deliveryStore="tokens/.deliveries/mybot.sqlite3")
    async with native:
        return await native.messages.recover(operation_id)
```

Recovery verifies the exact persisted key, outgoing direction, canonical chat and
message type. Missing/mismatched evidence never confirms or resends. A confirmed
receipt does not prove delivery/read; use `delivery_status`. Other legacy helpers
and older entries may lack pre-dispatch evidence and keep their no-replay contract.
Custom delivery stores need `set_expected` and `expected` for prepared sends.

An ordinary exception after the reserved send callable starts now yields an
unknown receipt and `DeliveryUncertainError`: it could occur while converting a
result after dispatch. Only a preparation failure or explicitly undispatched
`BridgeError` proves failure before sending. Flat legacy calls keep their errors.

This uses the upstream [key allocator](https://wppconnect.io/wa-js/functions/chat.generateMessageID.html)
and [messageId option](https://wppconnect.io/wa-js/interfaces/chat.FileMessageOptions.html).
If WhatsApp removes the message from its history/store, evidence recovery may be
impossible. Reconnection never replays an uncertain operation.

## Consume durable incoming events

```python
import asyncio
from WPP_Whatsapp import AsyncClient

async def consume():
    native = AsyncClient("mybot", reconnectAttempts=3)
    async with native.events.journal("tokens/.events/mybot.sqlite3") as journal:
        async with native:
            worker = journal.consumer("orders", max_attempts=5, lease_seconds=60)
            while True:
                result = await worker.claim()
                if result["lost"]:
                    print("Discarded events:", result["lost"])
                lease = result["lease"]
                if lease is None:
                    await asyncio.sleep(0.5)
                    continue
                try:
                    # Replace with idempotent application work before acknowledging.
                    print("Processing sequence:", lease.sequence)
                except Exception:
                    await worker.fail(lease)
                else:
                    await worker.ack(lease)
```

Namespaces default to the client's session. Register before connecting so
subscriptions survive replacement contexts. Events missed offline are not
backfilled. The journal contains private incoming bodies and sender IDs; bodies
are bounded and inline media is excluded.

Each consumer has one outstanding event. Processes sharing its ID atomically
share its lease; different IDs have independent cursors. Ack commits the cursor.
Failure retries with exponential backoff (default 1 second, capped at 1 hour).
Lease expiry also retries. Exhaustion records a dead letter and advances. Use
`await worker.renew(lease)` before a long-running valid lease expires. Expired or
replaced tokens cannot acknowledge another worker's event.

Crashes can repeat application side effects. Deduplicate your own work by journal
namespace, consumer ID and sequence, or by complete message ID where appropriate.
Handling is at least once **within retention**, with no exactly-once guarantee.
An outstanding lease retains its payload even if the original event is pruned.

The Python helper defaults to 10,000 events/24 hours; MCP keeps its configurable
256 events/24 hours. Retention gaps return `lost`; cumulative `lost_total` survives
restart. Maximum attempts are persisted and cannot silently change on restart.
Each namespace supports at most 128 consumers. Dead letters use journal count/age
bounds per consumer. Inspect with `await worker.dead_letters(after=0, limit=50)`.
Pruning removes logical records, not securely erased bytes.

## Inspect and compact delivery metadata

```bash
wpp-whatsapp-admin --store tokens/.deliveries/mybot.sqlite3 --namespace mybot list --limit 50
wpp-whatsapp-admin --store tokens/.deliveries/mybot.sqlite3 --namespace mybot inspect invoice-42
wpp-whatsapp-admin --store tokens/.deliveries/mybot.sqlite3 --namespace mybot compact --older-than-days 30
wpp-whatsapp-admin --store tokens/.deliveries/mybot.sqlite3 --namespace mybot compact --older-than-days 30 --apply
wpp-whatsapp-admin --store tokens/.deliveries/mybot.sqlite3 --namespace mybot recover invoice-42 --token-directory tokens
```

Listing, inspection and compaction do not open a browser. Recovery opens the
specified session for lookup. The store must exist. Listing accepts `--state`,
lexicographic operation-ID cursor `--after`, and at most 200 rows. Its state is the
persisted state: `pending` can represent a crashed process, whereas the tracker
presents another owner's inactive claim as unknown.

Compaction previews the count by default. `--apply` removes old terminal message
evidence, retaining operation IDs and digests as tombstones. Pending/unknown
operations are excluded. Reusing a compacted ID raises `OperationConflictError`.
Tombstones stay indefinitely; the ledger is not constant-size. Compaction does not
promise immediate physical file shrinkage or secure deletion.

## Metrics and service types

SQLite-backed tracker inspection remains available after session shutdown, even
for receipts evicted from the bounded memory cache. Reads open a short-lived
read-only connection; a closed tracker cannot reserve or dispatch new sends.

```python
from WPP_Whatsapp.core.metrics import prometheus

async def operational_metrics(native):
    return prometheus(await native.metrics())
```

Metrics include aggregate/per-command calls, failures, duration totals/maxima,
admission counts and queue/operation time, reconnect attempts, Python RSS/handles,
and RSS/process counts for this client's owned Chrome tree. PID creation time
guards against process-ID reuse. Python measurements cover the hosting process;
browser measurements exclude other sessions and unrelated browsers. Labels omit
account/message IDs. Totals/maxima are not latency percentiles.
Bridge and admission counters reset when a replacement context opens; recovery
counters last for the native client object's lifetime.

Applications may serve the numeric Prometheus text from their own authenticated
endpoint; the library opens no metrics port. `include_processes=False` skips
process inspection. `diagnostics()` remains a lightweight support snapshot.

Generated `.pyi` declarations cover all composed service signatures, tracked
receipts, typed reads and sync/async parity. Unspecified legacy raw returns remain
`Any`. In the development environment, run `python tools/generate_stubs.py` or
`python tools/generate_stubs.py --check`. CI checks all core modules and rejects
stale declarations.

## FastMCP additions

| Tool | Permission | Behavior |
| --- | --- | --- |
| `whatsapp_list_operations` | `read` | Bounded ledger inspection. |
| `whatsapp_recover_delivery` | `send` | Verify reserved evidence; never sends. Omitted in read-only mode. |
| `whatsapp_metrics` | `diagnostics` | Numeric Prometheus text. |
| `whatsapp_claim_event` | `events` | Lease one event from configured `eventStore`. |
| `whatsapp_complete_event` | `events` | `ack`, `fail` or `renew` with sequence/token. |
| `whatsapp_dead_letters` | `events` | Read bounded exhausted events. |

There are 29 tools, 23 with `--read-only`. Read-only mode prevents outgoing sends
and delivery reconciliation; session control, downloads and local consumer state
changes remain available. Every tool retains account/principal/scope checks.
Durable tools require `eventStore`; subscribe explicitly to receive new events.
