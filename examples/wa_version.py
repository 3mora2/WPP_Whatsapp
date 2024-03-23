from WPP_Whatsapp import Create

import logging

logger = logging.getLogger(name="WPP_Whatsapp")
logger.setLevel(logging.DEBUG)

# start client with your session name
your_session_name = "test"
creator = Create(session=your_session_name, browser="chrome", version="2.2409.2")
client = creator.start()
# Now scan Whatsapp Qrcode in browser

# check state of login
if creator.state != 'CONNECTED':
    raise Exception(creator.state)

print(client.getWAVersion())

