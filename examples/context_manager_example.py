"""Read-only sync/native-async examples with owned-resource cleanup."""

import argparse
import asyncio

from WPP_Whatsapp import AsyncClient, Create


def sync_example():
    with Create("context-example", autoClose=0) as client:
        print("Chats:", len(client.listChats({"count": 5})))


async def async_example():
    async with AsyncClient("async-context-example", autoClose=0) as client:
        chats = await client.chats.list_chats({"count": 5})
        print("Chats:", len(chats))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("sync", "async"), default="sync")
    if parser.parse_args().mode == "async":
        asyncio.run(async_example())
    else:
        sync_example()


if __name__ == "__main__":
    main()
