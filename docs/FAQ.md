# FAQ

## Which Python version do I need?

Python 3.9+ for the core, Python 3.10+ for the optional FastMCP integration.
Install `WPP_Whatsapp[mcp]` for MCP or `WPP_Whatsapp[stealth]` for optional stealth.

## Is Create the client?

It is the factory. `creator.start()` and `with Create(...) as client` return
the legacy `Whatsapp` client. Native asyncio applications can use `AsyncClient`.
Flat callbacks use `onMessage`; native events use `events.on_message`.

## Where does login happen?

In the visible browser's QR flow. Terminal QR logging is optional on `Create`.
MCP does not return QR data or cookies; call its connect tool and poll status.
Saved profiles are reused until the account unpairs or you explicitly log out.

## Does bundled mode work offline?

It avoids WA-JS release discovery/download. WhatsApp Web itself still needs
network access. Explicit versions/URLs/files fail instead of silently falling
back. Default latest discovery can fall back to the packaged compatible runtime.

## Can I run two workers with the same profile?

No: profiles have exclusive ownership. Close the owner or use a different
profile for another account. One MCP server shares one account among its clients;
it is not per-user account isolation.

## Why is history empty or a message lookup missing?

Loaded history and linked-device-available history differ. Use paginated reads,
and preserve full message IDs including group participants. See
[history examples](API_REFERENCE.md#history-and-complete-message-ids).

## Is a confirmed receipt a read receipt?

No. It means WA-JS returned a nonempty message ID or an outgoing message was
verified by lookup. Unknown operations must be inspected/reconciled, not
automatically resent under a new ID. Durable reservations require a preserved
SQLite ledger; persistence is not server-side exactly-once delivery.

## Does the MCP server expose every library method?

No. It exposes 12 explicit tools. The library has a broader generated
[service inventory](API_METHODS.md). An embedding application can register
additional FastMCP tools with its own access policy.

## Are examples and tests live-account verification?

Most tests use synthetic WhatsApp operations, even when the MCP transport is
real. Native Chrome checks verify browser behavior. Separate opt-in account
scripts verify specific read/callback flows; none of those checks certify every
method or live outbound sends. See the [test guide](../tests/README.md).
