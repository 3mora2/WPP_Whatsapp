from WPP_Whatsapp import Create
import logging

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

# start client with your session name
your_session_name = "test"
creator = Create(session=your_session_name,)

client = creator.start()
# Now scan Whatsapp Qrcode in browser

# check state of login
if creator.state != 'CONNECTED':
    raise Exception(creator.state)


def new_message(message):
    global client
    # Add your Code here
    if message and not message.get("isGroupMsg"):
        chat_id = message.get("from")
        message_id = message.get("id")
        if "السلام عليكم" in message.get("body"):
            client.reply(chat_id, "وعليكم السلام", message_id)
        else:
            client.reply(chat_id, "Welcome", message_id)



# creator.client.ThreadsafeBrowser.page_evaluate_sync("""
#  // Resolvenndo bug 'TypeError: i.Wid.isStatusV3 is not a function'
#     if(!WPP.whatsapp.Wid.isStatusV3) {
#       WPP.whatsapp.Wid.isStatusV3 = () => false
#     }
# """)

# Add Listen To New Message
creator.client.onMessage(new_message)
creator.loop.run_forever()
