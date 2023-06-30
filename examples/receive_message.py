from WPP_Whatsapp import Create

# start client with your session name
your_session_name = "test"
creator = Create(session=your_session_name)
client = creator.async_to_sync(creator.start())
# Now scan Whatsapp Qrcode in browser

# check state of login
if creator.state != 'CONNECTED':
    raise Exception(creator.state)


async def new_message(message):
    global creator
    # Add your Code here
    if message and not message.get("isGroupMsg"):
        chat_id = message.get("from")
        message_id = message.get("id")
        if "السلام عليكم" in message.get("body"):
            await creator.client.reply(chat_id, "وعليكم السلام", message_id)
        else:
            await creator.client.reply(chat_id, "Welcome", message_id)

# Add Listen To New Message
creator.client.onMessage(new_message)
# Listen Forever
creator.loop.run_forever()

