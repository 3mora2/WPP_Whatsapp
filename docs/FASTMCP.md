# WhatsApp tools with FastMCP

The optional integration provides a reusable FastMCP server backed by the native
`AsyncClient`. The core library still supports Python 3.9; MCP requires **Python
3.10+** and **FastMCP 4.1 or newer, below 5**.

## Install

```bash
python -m pip install --upgrade "WPP_Whatsapp[mcp]"
wpp-whatsapp-mcp --session mybot
```

FastMCP support is included from version 2.1.0. For a source checkout, use
`python -m pip install -e ".[mcp]"`. Older PyPI releases do not contain the server.
The account policies, events, search and media tools described below require
version 2.2.0 or newer; version 2.1.0 contains the original twelve tools.
Delivery ACK tools, persistent event journals and recovery settings require 2.3.0.

The equivalent module command is `python -m WPP_Whatsapp.mcp --session mybot`.
Chrome must be installed. The default transport is stdio: stdout contains only
MCP protocol messages and application logging goes to stderr.

Starting the server does not open a browser or access WhatsApp. A client calls
`whatsapp_connect`, the user scans the QR in the visible browser, and the client
polls `whatsapp_status` until `ready` is true. Saved profiles are reused. The QR,
cookies and login codes are never returned by tools. Use `--headless` only with
an already authenticated profile. `--wa-js-version bundled` selects the packaged
WA-JS runtime; the normal default discovers the latest stable release first.

## Configure an MCP client

Use the absolute path to the Python interpreter where the source package and
the `mcp` extra were installed. For example, in a client's MCP JSON configuration:

```json
{
  "mcpServers": {
    "whatsapp": {
      "command": "C:/path/to/venv/Scripts/python.exe",
      "args": [
        "-m", "WPP_Whatsapp.mcp",
        "--session", "mcp",
        "--token-directory", "C:/path/to/private/whatsapp/tokens"
      ]
    }
  }
}
```

Replace the example interpreter/storage paths for your installation. The
configuration format belongs to the MCP client; commands remain Python code.

## Tools

| Tool | Behavior |
| --- | --- |
| `whatsapp_status` | Local session state; never opens a browser. |
| `whatsapp_connect` | Open/reuse the configured profile; login happens in the browser. |
| `whatsapp_disconnect` | Close this session; preserve saved login and delivery metadata. |
| `whatsapp_reconnect` | Reopen the same profile without replay. |
| `whatsapp_list_chats` | Up to 200 chats, filtered by all/groups/users; optional older-page cursor. |
| `whatsapp_get_messages` | Up to 200 messages, including already-read chats; optional older-message cursor. |
| `whatsapp_get_message` | Lookup by complete message ID, including group participants. |
| `whatsapp_get_contact` | Read one contact by ID. |
| `whatsapp_get_group_members` | Read group participants. |
| `whatsapp_send_text` | Tracked text send requiring a stable operation ID. |
| `whatsapp_get_delivery` | Inspect tracked operation metadata without sending. |
| `whatsapp_reconcile_delivery` | Verify an actual outgoing message and confirm an uncertain receipt. |
| `whatsapp_list_accounts` | IDs of accounts this principal can read. |
| `whatsapp_diagnostics` | Sanitized session/capability/counter snapshot. |
| `whatsapp_search_messages` | Case-insensitive body search of one page, with a scan cursor; at most 200 messages. |
| `whatsapp_subscribe_messages` | Start the account's live incoming-message buffer; return its current cursor. |
| `whatsapp_get_events` | Read events after a cursor, with an explicit `lost` count after overflow. |
| `whatsapp_download_media` | Save media to the configured private media root; return relative filename, size and SHA-256. |
| `whatsapp_reply` | Tracked text reply with the complete quoted message ID. |
| `whatsapp_send_file` | Tracked document from the account's media root. |
| `whatsapp_send_image` | Tracked image from the account's media root. |

`--read-only` omits sending and reconciliation tools. Session control remains
available: 18 tools remain out of 23. Every account-specific tool accepts optional
`account_id`; omission selects the administrator's default account.
Tools reject empty IDs and invalid page sizes; full IDs pass through
unchanged. Browser/storage errors expose their type without message bodies,
profile paths or credentials. Tool schemas mark reads and idempotent operations explicitly.

## Delivery behavior

```python
result = await mcp_client.call_tool("whatsapp_send_text", {
    "chat_id": "123456789@c.us",
    "text": "Hello",
    "operation_id": "invoice-123"
})
print(result.structured_content)  # operation_id, state, message_id
```

Choose an operation ID (1–128 nonblank characters) once per intended message.
Retry using that same ID. Confirmed operations return the previous receipt;
reserved uncertain operations never cause another send. The tool returns
`state="unknown"` when the result cannot be established. Check delivery metadata
or reconcile using a verified outgoing message; never choose a new ID merely
to bypass uncertainty. A confirmed receipt does not prove recipient delivery/read.
`whatsapp_get_delivery` returns `{"receipt": ...}`; `receipt` is null for an
operation ID not found in the ledger. FastMCP's `result.data` can be a parsed model;
`result.structured_content` gives the protocol's JSON object directly.

The server's default SQLite store is `<token-directory>/.deliveries/mcp.sqlite3`,
scoped by WhatsApp session. Override it with `--delivery-store`. It stores operation
IDs, states, message IDs and timestamps, never recipients, message bodies, media
or credentials. Keep it across restarts for persistent deduplication. Deleting it
or changing the ID removes that protection. This is not server-side exactly-once
delivery. See [delivery semantics](ARCHITECTURE.md#sending-and-uncertain-results).

## Local HTTP

```bash
wpp-whatsapp-mcp --session mybot --transport http --port 8765
```

Connect your MCP client to `http://127.0.0.1:8765/mcp`. Loopback is the default.
One account is configured by default. Administrators can configure up to 32
independent accounts; each has its own profile, lock, ledger and event buffer.
Duplicate profiles/clients/session names are rejected. Do not run multiple workers against
the same profile. An unauthenticated local server gives its trusted local clients
access to all configured accounts; use a verified policy when clients differ in trust.

## Accounts and authenticated HTTP

```python
from fastmcp.server.auth import JWTVerifier
from WPP_Whatsapp.mcp import create_server
from WPP_Whatsapp.mcp.accounts import AccountConfig

server = create_server(
    accounts={
        "sales": AccountConfig("sales", token_directory="private-tokens", media_root="private-media/sales"),
        "support": AccountConfig("support", token_directory="private-tokens", read_only=True),
    },
    default_account="sales",
    auth=JWTVerifier(jwks_uri="https://identity.example/.well-known/jwks.json",
                     issuer="https://identity.example", audience="whatsapp", algorithm="RS256"),
    access_policy={
        "alice": {"sales": {"read", "send", "session", "events", "diagnostics"}},
        "bob": {"support": {"read", "session"}},
    },
)
```

Identity comes from the verified token's `sub` claim (or verified `client_id`
when no subject exists), never tool arguments, `_meta`, headers supplied as
identity, or MCP client names. Each operation needs both a policy grant and
its token scope: `whatsapp:read`, `whatsapp:send`, `whatsapp:session`,
`whatsapp:events` or `whatsapp:diagnostics`. Missing accounts/grants return the
same error. `read_only=True` on an account overrides send grants. Policy
configuration is copied at server construction. Supply a verified auth provider
with a policy; authenticated multi-account servers require one. Programmatic
single-account `auth=...` without a policy retains the original shared-account behavior.

The CLI accepts `--accounts-config accounts.json` containing a map of account
IDs to `AccountConfig` fields, and `--default-account`. JSON holds deployment
settings, not executable JavaScript commands. For example:

```json
{
  "sales": {"session": "sales", "token_directory": "private-tokens", "media_root": "private-media/sales"},
  "support": {"session": "support", "token_directory": "private-tokens", "read_only": true}
}
```

`--access-policy policy.json` contains the principal/account/scope map with scope
arrays instead of Python sets. Exposed HTTP requires all authentication options:

```bash
wpp-whatsapp-mcp --transport http --host 0.0.0.0 --accounts-config accounts.json --default-account sales --access-policy policy.json --auth-jwks-uri https://identity.example/.well-known/jwks.json --auth-issuer https://identity.example --auth-audience whatsapp
```

Use TLS termination for network deployments. Account definitions and media roots
are administrator settings; tools cannot create accounts or choose profile paths.
Each account is still shared among principals explicitly granted access to it.

## Events, search and media

Call `whatsapp_subscribe_messages` when ready, save its `cursor`, then poll
`whatsapp_get_events(after=cursor)`. Advance to the returned cursor. Each account
retains the latest 256 events in memory; `lost` reports overwritten events.
Events contain stable ID/body/type/sender/time fields rather than inline media
or arbitrary runtime objects. Bodies longer than 65,536 characters are capped
with an explicit `truncated` flag; complete message IDs remain intact.
Subscriptions do not backfill history. Active subscriptions are restored after
reconnect. Default in-memory buffers disappear when the server lifespan ends;
opt in to durable journals with `--event-store`. Consumers use independent cursors, so
one client's reads do not drain another's queue. Contents remain untrusted data.

`whatsapp_delivery_status(operation_id)` reports observed ACK evidence separately
from a queued receipt. `whatsapp_wait_for_delivery(operation_id, target, timeout)`
waits at most 120 seconds without resending. Both require the account's read scope.
See [reliability and migration](RELIABILITY.md) for configuration and limits.

Search scans **one history page**, including messages that do not match.
Use its `before_message_id` to scan older pages; it is not a server-wide full-text index.

Media access is disabled until an existing private directory is configured using
`--media-root` or `AccountConfig.media_root`. Send tools accept only relative
files inside that account's root; absolute paths, URLs, traversal and symlink
escapes are refused. Downloads use generated filenames and never overwrite.
The default limit is 64 MiB. Python transfers 256 KiB chunks, reports MCP progress,
cleans temporary files and removes cancelled partial downloads. The browser and
WA-JS still buffer a complete File/Blob; this is not constant-memory end-to-end
streaming. Timed-out sends remain tracked and may complete later; never replay
them with a new operation ID. Only media preparation/reads can be safely cancelled
before send dispatch. See [typed reads and media APIs](TYPED_MEDIA.md).

## Embed or extend

```python
from WPP_Whatsapp.mcp import create_server

server = create_server(
    session="mybot",
    token_directory="tokens",
    options={"operationTimeout": 30},
    read_only=True,
)

if __name__ == "__main__":
    server.run(transport="stdio", show_banner=False)
```

The factory returns an ordinary `fastmcp.FastMCP`, so applications can register
additional tools/resources or supply authentication. Factory construction does
not change logging or start Playwright. Server-owned clients are closed at
lifespan teardown. `create_server(client=existing_async_client)` keeps caller
ownership: teardown does not close it, but an explicit disconnect tool does.
Use the client on the same event loop that owns it. Operations are serialized
with connect/disconnect; status remains available while login/startup is pending.
An injected client keeps its own session, options and delivery-store configuration;
the factory's session settings apply only to clients it creates.

The protocol tests exercise in-process, stdio and HTTP transports, verified JWT
middleware, account/scope isolation, events and tracked media contracts. Most
WhatsApp operations are synthetic. A separate opt-in script checks real-account
reads and explicitly authorized sends; see [validation results](../tests/README.md).

FastMCP references: [tools](https://gofastmcp.com/servers/tools),
[lifespans](https://gofastmcp.com/servers/lifespan),
[client transports](https://gofastmcp.com/clients/transports).
