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

`--read-only` omits sending and reconciliation tools. Session control remains
available. Tools reject empty IDs and invalid page sizes; full IDs pass through
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

Connect your MCP client to `http://127.0.0.1:8765/mcp`. The command binds only to
loopback. Each server owns **one WhatsApp account/profile shared by its connected
MCP clients**; it does not provide per-user account isolation. For an authenticated
deployment, pass a FastMCP authentication provider to `create_server(auth=...)`
and configure the transport in your application. Do not run multiple workers
against the same browser profile.

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

The protocol tests exercise real FastMCP clients over in-process, stdio and HTTP
transports with synthetic WhatsApp operations, including unknown delivery,
reconciliation and duplicate suppression. They do not certify live message sends.

FastMCP references: [tools](https://gofastmcp.com/servers/tools),
[lifespans](https://gofastmcp.com/servers/lifespan),
[client transports](https://gofastmcp.com/clients/transports).
