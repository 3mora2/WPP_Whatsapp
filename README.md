# WPP_Whatsapp

WhatsApp Web automation for Python, built on [WPPConnect](https://github.com/wppconnect-team/wppconnect)
and [WA-JS](https://github.com/wppconnect-team/wa-js), using Playwright.

[Documentation](https://github.com/3mora2/WPP_Whatsapp/blob/main/docs/README.md) · [Español](https://github.com/3mora2/WPP_Whatsapp/blob/main/README.es-ES.md) ·
[PyPI](https://pypi.org/project/WPP-Whatsapp/) ·
[Releases](https://github.com/3mora2/WPP_Whatsapp/releases)

## Install

The core supports Python **3.9+**. FastMCP support requires **Python 3.10+**.

```bash
python -m pip install --upgrade WPP_Whatsapp
python -m pip install --upgrade "WPP_Whatsapp[mcp]"
```

The second command adds the optional MCP server. For a source checkout, use
`python -m pip install -e ".[mcp,dev]"`. Chrome is used by default; see
[installation](https://github.com/3mora2/WPP_Whatsapp/blob/main/docs/INSTALLATION.md) for Playwright Chromium and optional FFmpeg/stealth.

## Synchronous client

`Create` is a factory. `start()` or entering its context returns the `Whatsapp`
client; register callbacks on that client.

```python
from threading import Event
from WPP_Whatsapp import Create

with Create(session="mybot", autoClose=0) as client:
    def incoming(message):
        print("Received message ID:", message.get("id"))

    client.onMessage(incoming)
    print("Listening; press Ctrl+C to close.")
    Event().wait()
```

Scan the QR in the browser. The saved profile is reused on the next run.
Context exit closes owned resources; it does not log the account out.

## Native asyncio

```python
import asyncio
from WPP_Whatsapp import AsyncClient

async def main():
    async with AsyncClient("mybot", autoClose=0) as client:
        chats = await client.chats.list_chats({"count": 10})
        print("Chats loaded:", len(chats))

asyncio.run(main())
```

Use one client from its owning event loop. Native services use snake_case;
legacy flat methods retain their names and raw return values. Tracked service
sends return delivery receipts; a confirmed ID does not prove delivery/read.
See [API examples](https://github.com/3mora2/WPP_Whatsapp/blob/main/docs/API_REFERENCE.md) and the [migration guide](https://github.com/3mora2/WPP_Whatsapp/blob/main/docs/ARCHITECTURE.md).

## FastMCP server

```bash
wpp-whatsapp-mcp --session mybot
wpp-whatsapp-mcp --session mybot --transport http --port 8765
```

Choose one command: the first uses stdio, the second exposes
`http://127.0.0.1:8765/mcp`. Starting the server does not start WhatsApp. Call
`whatsapp_connect`, log in in the browser, then poll `whatsapp_status` until ready.

The 12 tools cover session control, paginated chat/history reads, complete
message-ID lookup, contacts, group members, tracked text sending and receipt
inspection/reconciliation. `--read-only` omits send/reconciliation tools.
One server owns one account shared by its MCP clients. See
[FastMCP configuration and delivery semantics](https://github.com/3mora2/WPP_Whatsapp/blob/main/docs/FASTMCP.md).

## Runtime, sessions and compatibility

- Bundled assets: WPPConnect **2.3.4**, WA-JS **4.6.1**. Startup discovers the
  latest stable WA-JS before checking its verified cache, with bundled fallback.
- `wa_js_version="bundled"` skips WA-JS discovery/download; WhatsApp Web still
  requires a network connection. Explicit versions/URLs/files stay strict.
- Preserve full message IDs, including group participant suffixes. Bare phone
  numbers are treated as phone numbers; explicit LIDs use `@lid`.
- A browser profile has one owner. Close that owner before reusing it;
  `close_already_profile=True` is rejected.
- Install `WPP_Whatsapp[stealth]` before enabling `stealthy=True`.
- Timeouts have different units; consult [configuration](https://github.com/3mora2/WPP_Whatsapp/blob/main/docs/CONFIGURATION.md).

## Guides and validation

- [Quick start](https://github.com/3mora2/WPP_Whatsapp/blob/main/docs/QUICKSTART.md), [API reference](https://github.com/3mora2/WPP_Whatsapp/blob/main/docs/API_REFERENCE.md),
  [generated service signatures](https://github.com/3mora2/WPP_Whatsapp/blob/main/docs/API_METHODS.md)
- [Troubleshooting](https://github.com/3mora2/WPP_Whatsapp/blob/main/docs/TROUBLESHOOTING.md), [FAQ](https://github.com/3mora2/WPP_Whatsapp/blob/main/docs/FAQ.md),
  [usage practices](https://github.com/3mora2/WPP_Whatsapp/blob/main/docs/BEST_PRACTICES.md), [performance](https://github.com/3mora2/WPP_Whatsapp/blob/main/docs/PERFORMANCE.md)
- [Runnable examples](https://github.com/3mora2/WPP_Whatsapp/blob/main/examples/README.md), [application templates](https://github.com/3mora2/WPP_Whatsapp/blob/main/scripts/README.md)
- [Development](https://github.com/3mora2/WPP_Whatsapp/blob/main/docs/DEVELOPMENT.md), [tests and validation boundaries](https://github.com/3mora2/WPP_Whatsapp/blob/main/tests/README.md),
  [changelog](https://github.com/3mora2/WPP_Whatsapp/blob/main/CHANGELOG.md)

Automated MCP tests use synthetic WhatsApp operations with real MCP transports.
They do not certify live sending or every upstream API. Rate limiting controls
local pacing; it does not guarantee account safety or platform acceptance.

Report reproducible bugs through [GitHub issues](https://github.com/3mora2/WPP_Whatsapp/issues).
The Python project uses [MIT](https://github.com/3mora2/WPP_Whatsapp/blob/main/LICENSE); bundled upstream code retains its
[own licenses](https://github.com/3mora2/WPP_Whatsapp/blob/main/WPP_Whatsapp/js_lib/UPSTREAM.md).
