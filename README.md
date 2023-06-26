# WPP_Whatsapp
WPP_Whatsapp aim of exporting functions from WhatsApp Web to the python, which can be used to support the creation of any interaction, such as customer service, media sending, intelligence recognition based on phrases artificial and many other things, use your imagination         
WPP_Whatsapp: Convert [WPPConnect](https://github.com/wppconnect-team/wppconnect) to python

Start Sync
```
from Whatsapp import Create


def catchQR(*args, **kwargs):
    """
    kwargs:{
        "qrCode":"data:image/png;base64,",
        "asciiQR":"",
        "attempt":1,
        "urlCode":"2@242",
     }
     """


self = Create(session="test", catchQR=catchQR)
# Pass Session Name to Save whatsapp session
self.async_to_sync(self.start())

if self.state != 'CONNECTED':
    raise Exception(self.state)
# Pass Number with code of country, and message
result = self.async_to_sync(self.client.sendText("201016708170", "hello from wpp"))
print(result)
"""{'id': 'true_**********@c.us_*************_out', 'ack': 3, 'sendMsgResult': {}}"""
self.async_to_sync(self.client.close())
```

Start Async
```
import asyncio
from Whatsapp import Create


def catchQR(*args, **kwargs):
    """
    kwargs:{
        "qrCode":"data:image/png;base64,",
        "asciiQR":"",
        "attempt":1,
        "urlCode":"2@242",
     }
     """


async def main():
    self = Create(session="test", catchQR=catchQR)
    # Pass Session Name to Save whatsapp session
    client = await self.start()
    if self.state != 'CONNECTED':
        raise Exception(self.state)
    # Pass Number with code of country, and message
    result = await client.sendText("201016708170", "hello from wpp")
    print(result)
    """
    {'id': 'true_201016708170@c.us_3EB0F8C1ED288B7C38398E_out', 'ack': 3, 'sendMsgResult': {}}
    """

    await client.close()


asyncio.run(main())

```