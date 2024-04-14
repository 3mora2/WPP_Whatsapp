import logging

from WPP_Whatsapp import Create

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

def new_message(message):
    global client
    if message:
        mensagem = message.get('body')
        chat_id = message.get('from')

        # Extract user ID and message content
        usuario_id = message.get('chatId')['user']

        print(usuario_id, mensagem)

        if usuario_id == 'mynumber':
            client.sendText(chat_id, "Here's what you said:" + mensagem)



your_session_name = "test"
creator = Create(session=your_session_name, browser='chrome')
client = creator.start()

# check state of login
if creator.state != 'CONNECTED':
    raise Exception(creator.state)

print('Starting!')

client.sendText('2010289465190', 'Testando docker')

creator.client.onMessage(new_message)
# creator.loop.run_forever()
# while True:
#     pass