from WPP_Whatsapp import Create


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


self.client.onMessage(new_message)
self.loop.run_forever()
# self.async_to_sync(self.client.close())
