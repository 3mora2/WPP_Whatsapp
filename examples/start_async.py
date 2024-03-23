import asyncio
from WPP_Whatsapp import Create
import logging

logger = logging.getLogger(name="WPP_Whatsapp")
logger.setLevel(logging.DEBUG)


# Not Work Yet

async def main():
    # start client with your session name
    your_session_name = "test"
    creator = Create(session=your_session_name, browser="chrome",
                     loop=asyncio.get_event_loop())  # , version="2.2409.2")

    client = await creator.start_()
    # Now scan Whatsapp Qrcode in browser

    # check state of login
    if creator.state != 'CONNECTED':
        raise Exception(creator.state)

    print(client.getWAVersion())


asyncio.run(main())
