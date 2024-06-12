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

message_id = "true_120363021849652757@g.us_3EB03B7A114A44955D2DBC_201016708170@c.us"

media = client.downloadMedia(message_id)
# OR
message = client.getMessageById(message_id)
media = client.downloadMedia(message)