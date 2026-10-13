"""Native async receiving example; no automatic outbound messages."""

import asyncio

from WPP_Whatsapp import AsyncClient


async def main():
    async with AsyncClient("native-example", autoClose=0) as client:

        async def incoming(message):
            fetched = await client.messages.get_message(message["id"])
            print("Incoming message lookup succeeded:", fetched["id"] == message["id"])

        client.events.on_message(incoming)
        print("Listening. Press Ctrl+C to close the owned browser.")
        await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
