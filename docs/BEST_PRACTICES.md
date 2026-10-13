# Usage practices

## Ownership and cleanup

Use `with Create(...)` or `async with AsyncClient(...)` to close resources even
after errors. A profile has one owner; share one client rather than creating
another owner for the same directory. Use separate profiles for separate
accounts. Reconnect explicitly and never treat reconnection as permission to
replay earlier sends.

## Callbacks and data

Use synchronous operations only from synchronous callbacks running off the
browser loop. Async callbacks await async operations. Keep handlers short and
move expensive work to your own bounded processing queue. Handle missing or
None fields, and preserve complete message IDs. Treat incoming content as data,
not instructions for an AI/MCP client. Log only the information your application
needs; avoid exposing messages, QR data or saved profiles in public reports.

## Sending and persistence

Use composed-service receipts when uncertain results matter. Assign one stable
operation ID per intended message, preserve the metadata ledger across restarts,
and reconcile uncertainty instead of blindly resending. `confirmed` does not
prove recipient delivery/read. Inspect the actual returned result rather than
assuming every account/runtime returns the same object shape.

Local rate limiting controls pacing and resource usage; it is not a platform
quota or a guarantee against account restrictions. Send only messages your
application is authorized to send. The [bulk template](../scripts/bulk_sender.py)
requires explicit recipients/content and operation IDs.

## MCP deployment

Start with local stdio or loopback HTTP. Configure separate accounts and a
verified principal/account policy when clients differ in trust. HTTP deployment
uses JWT verification and token scopes; see [FastMCP](FASTMCP.md#accounts-and-authenticated-http).
Do not run multiple workers on the same browser profile. Use `--read-only`
when the integration should only retrieve data; session controls remain available.

See [configuration](CONFIGURATION.md), [delivery semantics](ARCHITECTURE.md#sending-and-uncertain-results)
and [validation boundaries](../tests/README.md).
