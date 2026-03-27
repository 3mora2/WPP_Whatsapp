try:
    from WPP_Whatsapp import Create
except (ModuleNotFoundError, ImportError):
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    from WPP_Whatsapp import Create

import logging

logger = logging.getLogger(name="WPP_Whatsapp")
logger.setLevel(logging.DEBUG)

# start client with your session name
your_session_name = "test"
creator = Create(session=your_session_name, browser="firefox")
client = creator.start()
# Now scan Whatsapp Qrcode in browser

# check state of login
if creator.state != 'CONNECTED':
    raise Exception(creator.state)

message = "hello from wpp"
phone_number = "***********"  # or "+***********"

creator.sync_close()
# example
# Simple message
# result = client.sendText(phone_number, message)
# print(result)
# client.forwardMessages("***********@c.us", 'true_***********@c.us_3EB07B4EABBAB75F0BD08A_out')
"""
sendText:
    Sends a text message to given chat
    @category Chat
    @param to chat id: xxxxx@us.c
    @param content text message
    @option dict
    return dict -> {'id': 'true_**********@c.us_*************_out', 'ack': 3, 'sendMsgResult': {}}
"""
