# Quick start

Complete [installation](INSTALLATION.md), then open a visible browser and scan
its WhatsApp QR. Use a stable session name to reuse the saved login.

## Read a chat with the legacy client

```python
from WPP_Whatsapp import Create

with Create(session="mybot", autoClose=0) as client:
    chats = client.listChats({"count": 10})
    print("Chats:", len(chats))
```

`Create(...)` alone constructs the factory. `creator.start()` returns the client;
the context manager above also starts it and closes it at exit. Do not call
`client.start()` again after obtaining the ready client.

## Receive messages without automatically replying

```python
from threading import Event
from WPP_Whatsapp import Create

with Create("listener", autoClose=0) as client:
    def incoming(message):
        print("Received:", message.get("id"))

    client.onMessage(incoming)
    Event().wait()
```

Keep the main program alive while listening. Ctrl+C exits the context and closes
owned resources. `onMessage` is the flat API name (`on_message` is an alias on
the same client). The native equivalent is
`client.events.on_message(...)`. Sync and async callbacks are supported.

## Native asyncio

```python
import asyncio
from WPP_Whatsapp import AsyncClient

async def main():
    async with AsyncClient("asyncbot", autoClose=0) as client:
        async def incoming(message):
            fetched = await client.messages.get_message(message["id"])
            print("ID matches:", fetched["id"] == message["id"])

        client.events.on_message(incoming)
        await asyncio.Event().wait()

asyncio.run(main())
```

Async callbacks await async operations. Existing async flat operations generally
have a trailing underscore, e.g. `await client.getMessages_(chat_id, {"count": 20})`
on a legacy client; native services use snake_case without that suffix.

## FastMCP

With the `mcp` extra installed on Python 3.10+:

```bash
wpp-whatsapp-mcp --session mcp
```

Your MCP client launches this stdio command. Call `whatsapp_connect`, scan the
browser QR and poll `whatsapp_status` until ready. For local HTTP, add
`--transport http --port 8765` and use `http://127.0.0.1:8765/mcp`.
See [client configuration](FASTMCP.md#configure-an-mcp-client).

## Next steps

[API recipes](API_REFERENCE.md) cover history, sending and media. Read
[delivery semantics](ARCHITECTURE.md#sending-and-uncertain-results) before adding
automatic retries. [Configuration](CONFIGURATION.md) explains timeout units;
[examples](../examples/README.md) provide runnable programs with explicit inputs.
