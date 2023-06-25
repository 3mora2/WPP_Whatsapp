import asyncio

from Whatsapp.controllers.initializer import Create

self = Create()
asyncio.run(self.start(session="test", user_name="test"))
