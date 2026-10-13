# Performance

Measure the actual account/runtime workload; the project does not promise a
fixed throughput or browser memory footprint.

## Reads and events

Prefer `listChats({"count": ...})` and paginated `getMessages` over loading all
history. An all-history request can require many upstream fetches. Cache only
what your application needs. Keep callbacks short: one ordered queue processes
events per session, so slow handlers increase latency. Observe
`client.events.stats` (native) or `client.async_services.events.stats` (legacy),
especially rejection counts before increasing `eventQueueSize`.

## Concurrency and I/O

Use native `AsyncClient` on one event loop for async applications. Avoid sync
browser operations on that owner loop. Use `asyncio.to_thread` for your own
blocking filesystem/CPU work when appropriate. Rate-limit outbound operations
on that same loop. More concurrency is not necessarily more throughput; batch
helpers expose an explicit `concurrency` parameter and default text sends to 1.

MCP serializes WhatsApp operations with session lifecycle changes to prevent
close/read/send races. Status remains available during startup. A single MCP
server is not a distributed browser worker pool.

## Cache and shutdown

Runtime discovery still happens before a verified cached WA-JS release is used.
Use the bundled selection when avoiding runtime downloads is required; WhatsApp
network traffic remains necessary. Runtime caching is not a cache of messages.
Close contexts, listeners and owned drivers through the client instead of
deleting profiles or leaving background browser processes running.

See [architecture](ARCHITECTURE.md) for queue/cancellation behavior and
[configuration](CONFIGURATION.md) for timeout units and cache/storage options.
