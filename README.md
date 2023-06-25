# WPP_Whatsapp
Convert [WPPConnect](https://github.com/wppconnect-team/wppconnect) to python

Start
```
import asyncio
import traceback

from Whatsapp import Create


async def a_main():

    self = Create()
    # Pass Session Name to Save whatsapp session
    client = await self.start(session="test")
    # Pass Number with code of country, and message
    result = await client.sendText("201016708170", "hello from wpp")
    print(result)
    """
    {'id': 'true_201016708170@c.us_3EB0F8C1ED288B7C38398E_out', 'ack': 3, 'sendMsgResult': {}}
    """

    await client.close()


def main():
    self = Create()
    loop = asyncio.new_event_loop()
    loop.run_until_complete(self.start(session="test"))
    coroutine = self.client.sendText("201016708170", "hello from wpp")
    loop.run_until_complete(coroutine)
    loop.run_until_complete(self.client.close())


if __name__ == "__main__":
    asyncio.run(a_main())
    # or
    # main()
```