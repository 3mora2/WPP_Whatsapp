# WPP_Whatsapp
<p align="center">
  <a href="https://pypi.org/project/WPP-Whatsapp"><img alt="PyPI Version" src="https://img.shields.io/pypi/v/WPP-Whatsapp.svg?maxAge=86400" /></a>
  <a href="https://pypi.org/project/WPP-Whatsapp"><img alt="Python Versions" src="https://img.shields.io/pypi/pyversions/WPP-Whatsapp.svg?maxAge=86400" /></a>
</p>

WPP_Whatsapp aim of exporting functions from WhatsApp Web to the python, which can be used to support the creation of
any interaction, such as customer service, media sending, intelligence recognition based on phrases artificial and many
other things, use your imagination         
WPP_Whatsapp > [WPPConnect](https://github.com/wppconnect-team/wppconnect) Converted to python, so Documentation is same

<p align="center">
  <a href="https://wppconnect.io/wppconnect/pages/getting-started/basic-functions.html">Basic Function</a> •
  <a href="https://wppconnect.io/wppconnect/">Documentation</a>
</p>

## Functions

|                                                            |   |
|------------------------------------------------------------|---|
| Automatic QR Refresh                                       | ✔ |
| Send **text, image, video, audio and docs**                | ✔ |
| Get **contacts, chats, groups, group members, Block List** | ✔ |
| Send contacts                                              | ✔ |
| Send stickers                                              | ✔ |
| Send stickers GIF                                          | ✔ |
| Multiple Sessions                                          | ✔ |
| Forward Messages                                           | ✔ |
| Receive message                                            | ✔ |
| insert user section                                        | ✔ |
| Send _location_                                            | ✔ |
| **and much more**                                          | ✔ |

See more at <a href="https://wppconnect.io/wppconnect/classes/Whatsapp.html">WhatsApp methods</a>

## Installation

installed with [pip](https://pip.pypa.io):
```commandline
pip install WPP_Whatsapp
```
Alternatively, you can grab the latest source code from [GitHub](https://github.com/3mora2/WPP_Whatsapp):

```commandline
git clone https://github.com/3mora2/WPP_Whatsapp.git
cd WPP_Whatsapp
pip install .
```

## Getting Started

### Sync

```
from WPP_Whatsapp import Create


self = Create(session="test")
self.async_to_sync(self.start())
```

### Async

```
import asyncio
from WPP_Whatsapp import Create


async def main():
    self = Create(session="test")
    client = await self.start()

asyncio.run(main())
```

## Send Text

### Sync

```
from WPP_Whatsapp import Create


self = Create(session="test")
self.async_to_sync(self.start())

if self.state != 'CONNECTED':
    raise Exception(self.state)
# Pass Number with code of country, and message
result = self.async_to_sync(self.client.sendText("201016708170", "hello from wpp"))
print(result)
"""{'id': 'true_**********@c.us_*************_out', 'ack': 3, 'sendMsgResult': {}}"""
self.async_to_sync(self.client.close())
```

### Async

```
import asyncio
from WPP_Whatsapp import Create


async def main():
    self = Create(session="test")
    # Pass Session Name to Save whatsapp session
    client = await self.start()
    if self.state != 'CONNECTED':
        raise Exception(self.state)
    # Pass Number with code of country, and message
    result = await client.sendText("201016708170", "hello from wpp")
    print(result)
    """{'id': 'true_**********@c.us_*************_out', 'ack': 3, 'sendMsgResult': {}}"""
    await client.close()


asyncio.run(main())
```

## Receive New Message

```
def new_message(message):
    print(message)

self.client.onMessage(new_message)
# wait new message
self.client.loop.run_forever()
```