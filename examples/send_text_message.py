from WPP_Whatsapp import Create

# start client with your session name
your_session_name = "test"
creator = Create(session=your_session_name)
client = creator.async_to_sync(creator.start())
# Now scan Whatsapp Qrcode in browser

# check state of login
if creator.state != 'CONNECTED':
    raise Exception(creator.state)

message = "hello from wpp"
phone_number = "201016708170"  # or "+201016708170"

# example
# Simple message
result = creator.send_text_message(phone_number, message)
print(result)

"""
send_text_message:
    Sends a text message to given chat
    @category Chat
    @param to chat id: xxxxx@us.c
    @param content text message
    @option dict
    return dict -> {'id': 'true_**********@c.us_*************_out', 'ack': 3, 'sendMsgResult': {}}
"""
