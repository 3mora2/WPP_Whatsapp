# WPP_Whatsapp

**Automate WhatsApp Web from Python.**

Build message listeners, read conversations, work with media, and connect WhatsApp
to MCP clients. WPP_Whatsapp brings together
[WPPConnect](https://github.com/wppconnect-team/wppconnect),
[WA-JS](https://github.com/wppconnect-team/wa-js), and Playwright, with both
synchronous and native `asyncio` interfaces.

**English** · [العربية](https://github.com/3mora2/WPP_Whatsapp/blob/main/README.ar.md) · [Español](https://github.com/3mora2/WPP_Whatsapp/blob/main/README.es-ES.md)

[Documentation](https://github.com/3mora2/WPP_Whatsapp/blob/main/docs/README.md) ·
[PyPI](https://pypi.org/project/WPP-Whatsapp/) ·
[Releases](https://github.com/3mora2/WPP_Whatsapp/releases) ·
[Report an issue](https://github.com/3mora2/WPP_Whatsapp/issues)

**On this page**

- [What you can build](#what-you-can-build)
- [Installation](#installation)
- [Quick start](#quick-start-receive-messages)
- [Native asyncio](#use-native-asyncio)
- [MCP integration](#connect-an-mcp-client)
- [Sessions and delivery](#working-with-sessions-and-delivery)
- [Documentation](#explore-the-documentation)
- [Contributing and support](#contributing-and-support)
- [License](#license)

## What you can build

- **Message workflows:** receive incoming messages, read chat history, send text,
  and reply to conversations.
- **Media integrations:** send images and documents, and download message media.
- **Contact and group tools:** look up contacts, list chats, and read group members.
- **Async applications:** use native `asyncio` services for messages, chats, events,
  and more, with optional typed read results.
- **MCP integrations:** expose WhatsApp tools over stdio or local HTTP, with
  account isolation, access policies, diagnostics, and tracked sends.

## Installation

You need **Python 3.9+**, **Chrome or Playwright Chromium**, and an internet connection.
The optional MCP integration requires **Python 3.10+**.

Install the Python library:

```bash
python -m pip install --upgrade WPP_Whatsapp
```

For MCP support, install the optional extra instead:

```bash
python -m pip install --upgrade "WPP_Whatsapp[mcp]"
```

Chrome is the default browser. You can also use Playwright Chromium; see the
[installation guide](https://github.com/3mora2/WPP_Whatsapp/blob/main/docs/INSTALLATION.md)
for browser setup, optional FFmpeg support, and the `stealth` extra.

## Quick start: receive messages

Save this as `listener.py`, then run `python listener.py`:

```python
from threading import Event

from WPP_Whatsapp import Create


def incoming(message):
    print("Received message ID:", message.get("id"))


with Create(session="mybot", autoClose=0) as client:
    client.onMessage(incoming)
    print("Listening; press Ctrl+C to close.")
    Event().wait()
```

On the first run, scan the QR code in the browser with WhatsApp on your phone.
Use the same session name on later runs to reuse the saved login.
The example prints incoming message IDs and keeps listening until you press Ctrl+C.
Leaving the `with` block closes the client's resources while preserving the login.

`Create` manages startup and returns the ready client when you enter the `with`
block. If you manage startup yourself, use `creator.start()` to get that client
before registering callbacks or calling methods.

## Use native asyncio

Choose `AsyncClient` for an application that already uses `asyncio`.
This example loads up to ten chats:

```python
import asyncio

from WPP_Whatsapp import AsyncClient


async def main():
    async with AsyncClient("mybot", autoClose=0) as client:
        chats = await client.chats.list_chats({"count": 10})
        print("Chats loaded:", len(chats))


asyncio.run(main())
```

Keep each async client on the event loop that created it. Native services use
`snake_case` method names; existing flat methods keep their names and raw results.
See the [API reference](https://github.com/3mora2/WPP_Whatsapp/blob/main/docs/API_REFERENCE.md)
for sending, history, and media examples, or the
[migration guide](https://github.com/3mora2/WPP_Whatsapp/blob/main/docs/ARCHITECTURE.md)
for moving existing code to native services.

## Connect an MCP client

With the `mcp` extra installed, configure your MCP client to launch:

```bash
wpp-whatsapp-mcp --session mybot
```

This uses stdio. To run a local HTTP server instead:

```bash
wpp-whatsapp-mcp --session mybot --transport http --port 8765
```

The HTTP endpoint is `http://127.0.0.1:8765/mcp`.
Once the server is running:

1. Call `whatsapp_connect` from your MCP client.
2. Complete WhatsApp login in the browser.
3. Poll `whatsapp_status` until `ready` is true.

Starting the MCP server alone does not open WhatsApp. Version **2.3.0** provides
**23 tools** for sessions, chats, messages, search, events, media, diagnostics and ACK evidence.
Use `--read-only` to omit sending and reconciliation tools, leaving **18 tools**.

The [FastMCP guide](https://github.com/3mora2/WPP_Whatsapp/blob/main/docs/FASTMCP.md)
covers client configuration, multiple accounts, verified JWT access policies,
and delivery tracking. MCP was introduced in 2.1.0 with 12 tools; the expanded
toolset requires 2.2.0 or newer.

Version 2.3.0 adds request-bound operation IDs, optional durable event journals,
bounded connection recovery, delivery/read ACK waits, and admission/rate controls.
See the [reliability and migration guide](https://github.com/3mora2/WPP_Whatsapp/blob/main/docs/RELIABILITY.md),
[release status](https://github.com/3mora2/WPP_Whatsapp/blob/main/CHANGELOG.md), and runnable HTTP/MCP examples.

## Working with sessions and delivery

- **Reuse sessions consistently.** Each browser profile has one owner at a time.
  Close the current owner before reusing it; `close_already_profile=True` is rejected.
- **Keep complete IDs.** Preserve message IDs exactly, including group participant
  suffixes. Bare phone numbers are treated as phone numbers; explicit LIDs use `@lid`.
- **Check send receipts before retrying.** Tracked service sends return receipts.
  A confirmed message ID does not prove recipient delivery or reading. See
  [delivery semantics](https://github.com/3mora2/WPP_Whatsapp/blob/main/docs/ARCHITECTURE.md#sending-and-uncertain-results)
  before adding automatic retries.
- **Choose the runtime when needed.** Startup normally discovers the latest stable
  WA-JS, checks its verified cache, and falls back to bundled assets. Set
  `wa_js_version="bundled"` to skip discovery and download. WhatsApp Web still
  needs an internet connection. Explicit versions, URLs, and files are strict selections.
- **Check optional settings.** `stealthy=True` requires `WPP_Whatsapp[stealth]`.
  Timeout units vary by setting; see
  [configuration](https://github.com/3mora2/WPP_Whatsapp/blob/main/docs/CONFIGURATION.md).

Bundled assets: WPPConnect **2.3.4** and WA-JS **4.6.1**.

## Explore the documentation

| I want to… | Start here |
| --- | --- |
| Set up the library and browser | [Installation](https://github.com/3mora2/WPP_Whatsapp/blob/main/docs/INSTALLATION.md) |
| Open a session and read messages | [Quick start](https://github.com/3mora2/WPP_Whatsapp/blob/main/docs/QUICKSTART.md) |
| Find methods and arguments | [API reference](https://github.com/3mora2/WPP_Whatsapp/blob/main/docs/API_REFERENCE.md) · [Service signatures](https://github.com/3mora2/WPP_Whatsapp/blob/main/docs/API_METHODS.md) |
| Configure profiles and timeouts | [Configuration](https://github.com/3mora2/WPP_Whatsapp/blob/main/docs/CONFIGURATION.md) |
| Recover operations, consume durable events and inspect metrics | [Operations (2.4)](https://github.com/3mora2/WPP_Whatsapp/blob/main/docs/OPERATIONS.md) |
| Use typed reads and bounded media operations | [Typed reads and media](https://github.com/3mora2/WPP_Whatsapp/blob/main/docs/TYPED_MEDIA.md) |
| Run a complete example | [Examples](https://github.com/3mora2/WPP_Whatsapp/blob/main/examples/README.md) · [Application templates](https://github.com/3mora2/WPP_Whatsapp/blob/main/scripts/README.md) |
| Resolve a problem | [Troubleshooting](https://github.com/3mora2/WPP_Whatsapp/blob/main/docs/TROUBLESHOOTING.md) · [FAQ](https://github.com/3mora2/WPP_Whatsapp/blob/main/docs/FAQ.md) |
| Plan reliable application behavior | [Usage practices](https://github.com/3mora2/WPP_Whatsapp/blob/main/docs/BEST_PRACTICES.md) · [Performance](https://github.com/3mora2/WPP_Whatsapp/blob/main/docs/PERFORMANCE.md) |

## Contributing and support

For bugs, open a [GitHub issue](https://github.com/3mora2/WPP_Whatsapp/issues) with
a minimal example and sanitized version and error details.
For code contributions, start with the
[development guide](https://github.com/3mora2/WPP_Whatsapp/blob/main/docs/DEVELOPMENT.md)
and [test guide](https://github.com/3mora2/WPP_Whatsapp/blob/main/tests/README.md).
Release changes are recorded in the
[changelog](https://github.com/3mora2/WPP_Whatsapp/blob/main/CHANGELOG.md).

Automated MCP tests use synthetic WhatsApp operations with real MCP transports;
they do not certify live sending or every upstream API. Local rate limiting
controls pacing and does not guarantee platform acceptance or account safety.

## License

The Python project is licensed under [MIT](https://github.com/3mora2/WPP_Whatsapp/blob/main/LICENSE).
Bundled JavaScript dependencies retain their
[upstream licenses](https://github.com/3mora2/WPP_Whatsapp/blob/main/WPP_Whatsapp/js_lib/UPSTREAM.md).
