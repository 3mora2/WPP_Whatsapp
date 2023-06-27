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
    client = await self.start()
    if self.state != 'CONNECTED':
        raise Exception(self.state)
    # Pass Number with code of country, and message
    result = await client.sendText("201016708170", "hello from wpp")
    print(result)
    """{'id': 'true_**********@c.us_*************_out', 'ack': 3, 'sendMsgResult': {}}"""

    await client.close()


asyncio.run(main())
