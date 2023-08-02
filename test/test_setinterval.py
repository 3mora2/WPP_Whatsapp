from asyncio import sleep
import asyncio


class setInterval:
    def __init__(self, action, interval):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        self.interval = interval
        self.action = action
        self.task = loop.create_task(self.__set_interval())

    async def __set_interval(self):
        while True:
            await self.action()
            await sleep(self.interval)

    def cancel(self):
        self.task.cancel()


async def pprint(f="test"):
    print(f'{f=}')


pros = setInterval(pprint, 5)

