# WPP_Whatsapp
Convert [WPPConnect](https://github.com/wppconnect-team/wppconnect) to python

Start
```
import asyncio
import traceback

from Whatsapp import Create


async def main():
    try:
        self = Create()
        client = await self.start(session="test", user_name="test")
        result = await client.sendText("201016708170", "hello from wpp")
        print(result)
        """
        {'id': 'true_201016708170@c.us_3EB0F8C1ED288B7C38398E_out', 'ack': 3, 'sendMsgResult': {}}
        """

        await client.close()

    except:
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
```