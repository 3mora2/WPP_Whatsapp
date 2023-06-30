from WPP_Whatsapp import Create
import logging

logger = logging.getLogger(name="WPP_Whatsapp")
logger.setLevel(logging.DEBUG)

self = Create(session="test")
self.async_to_sync(self.start())

if self.state != 'CONNECTED':
    raise Exception(self.state)
# Pass Number with code of country, and message
# result = self.async_to_sync(self.client.sendText("201016708170", "hello from wpp"))
# print(result)
# """{'id': 'true_**********@c.us_*************_out', 'ack': 3, 'sendMsgResult': {}}"""


async def new_message(message):
    global self
    if message and not message.get("isGroupMsg"):
        if "السلام عليكم" in message.get("body"):
            chat_id = message.get("from")
            message_id = message.get("id")
            await self.client.reply(chat_id, "وعليكم السلام", message_id)

# self.client.onMessage(new_message)
self.loop.run_forever()
# self.async_to_sync(self.client.close())
