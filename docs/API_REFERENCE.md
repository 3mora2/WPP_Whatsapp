# API reference

This guide gives checked recipes. [API_METHODS.md](API_METHODS.md) is the generated
inventory of composed-service signatures and their corresponding flat operations.
It documents the Python surface; availability/results still depend on the selected
WA-JS runtime, account permissions and current WhatsApp Web behavior.

## Choose the interface

| Interface | Open and close | Operations |
| --- | --- | --- |
| Sync legacy | `with Create("mybot") as client` | `client.getMessages(...)`, `client.sendText(...)` |
| Async legacy | `async with Create("mybot") as client` | `await client.getMessages_(...)`, `await client.sendText_(...)` |
| Native asyncio | `async with AsyncClient("mybot") as client` | `await client.messages.get_messages(...)` |
| Sync composed | Same sync `Create` client | `client.services.messages.send_text(...)` |
| Async composed on legacy | Same legacy client | `await client.async_services.messages.send_text(...)` |
| MCP | [FastMCP server](FASTMCP.md) | Explicit typed protocol tools |

`Create` is a factory, not the operation client. A synchronous callback can use
sync methods; an async callback on the browser loop must await async methods.

## History and complete message IDs

The following fragments assume a ready legacy `client` and identifiers selected
by the caller. Never truncate a group participant suffix from a message ID.

```python
messages = client.getMessages(chat_id, {"count": 50})
older = client.getMessages(chat_id, {"count": 50, "id": message_id, "direction": "before"})
message = client.getMessageById(message_id)
loaded = client.getAllMessagesInChat(chat_id, includeMe=True, includeNotifications=False)
earlier = client.loadEarlierMessages(chat_id)
available = client.loadAndGetAllMessagesInChat(chat_id, includeMe=True, includeNotifications=False)
```

Opening a chat first is optional. `getAllMessagesInChat` reads already-loaded
messages; `loadAndGetAllMessagesInChat` requests history available to this linked
device. Large histories may be expensive; prefer pagination. The current native
equivalents are `messages.get_messages`, `messages.get_message`,
`messages.get_all_messages_in_chat`, `messages.load_earlier_messages` and
`messages.load_and_get_all_messages_in_chat`.

## Text and tracked sends

```python
result = client.sendText(chat_id, "Hello", options={"linkPreview": False})
reply = client.reply(chat_id, "Reply", message_id)
```

Flat methods retain raw return values. For explicit receipt tracking on a sync client:

```python
receipt = client.services.messages.send_text(chat_id, "Hello", operation_id="order-123")
print(receipt.state.value, receipt.message_id)
```

On a native async client:

```python
from WPP_Whatsapp import AsyncClient

client: AsyncClient
receipt = await client.messages.send_text(chat_id, "Hello", operation_id="order-123")
```

Use one stable operation ID per intended message. A duplicate confirmed ID returns
the previous receipt; other reserved IDs raise `DeliveryUncertainError` without
resending. A confirmed message ID is not a delivery/read receipt. Persist the
ledger with `deliveryStore` for restart-safe reservations. See
[architecture](ARCHITECTURE.md#sending-and-uncertain-results) for timeout,
cancellation, storage failure, late confirmation and reconciliation.

## Media and location

```python
image = client.sendImage(chat_id, "photo.jpg", filename="photo.jpg", caption="Caption")
document = client.sendFile(chat_id, "report.pdf", nameOrOptions="report.pdf", caption="Report")
voice = client.sendPtt(chat_id, "voice.ogg")
location = client.sendLocation(chat_id, {"lat": 40.7128, "lng": -74.0060, "title": "New York"})
card = client.sendContactVcard(chat_id, "123456789@c.us")
data_uri = client.downloadMedia(message_id)
```

The third positional argument of `sendImage` is **filename**, not caption.
`sendFile` also distinguishes filename/options from caption. Use `sendPtt` for
voice notes and `sendFile` for other file payloads; there is no generic flat
`sendVoice`/`sendAudio` recipe. `downloadMedia` returns base64 media, commonly a
data URI; see [download.py](../examples/download.py) for validated decoding.
FFmpeg is required for conversion paths that invoke it.

## Events

```python
def incoming(message):
    print(message.get("id"))

dispose = client.onMessage(incoming)
client.onAnyMessage(incoming)
client.onStateChange(lambda state: print(state))
dispose()
```

Native event services provide `events.on_message`, `events.on_any_message` and
`events.on(name, callback)` for supported event names. Payload fields vary by
event/message type; handle missing/None `body`, media fields and contact names.
Callbacks do not run once per historical message. Queues are bounded and ordered;
see [event lifecycle](ARCHITECTURE.md#events-and-lifecycle).

## Chats, groups and other services

```python
chats = client.listChats({"count": 20, "onlyGroups": True})
contact = client.getContact("123456789@c.us")
members = client.getGroupMembers(group_id)
group = client.createGroup("Example", ["123456789@c.us", "987654321@c.us"])
client.addParticipant(group_id, "123456789@c.us")
```

Group mutations require the relevant account permissions. Inspect the returned
object rather than assuming a fixed `gid`/`name` shape for every upstream build.
Catalog/business, communities, newsletters, lists, labels, status and profile
operations are listed in the [generated inventory](API_METHODS.md). Those are
library services; the MCP server intentionally exposes a smaller 12-tool surface.

## Session control

Closing a client releases its owned browser resources; `logout()` explicitly
unpairs the account and should only be called when intended. `AsyncClient.reconnect()`
reopens its saved profile and does not replay operations. Use
[configuration](CONFIGURATION.md) for paths/units and [troubleshooting](TROUBLESHOOTING.md)
for startup/ownership errors.
