from WPP_Whatsapp import Create

import logging

logger = logging.getLogger(name="WPP_Whatsapp")
logger.setLevel(logging.DEBUG)

# start client with your session name
your_session_name = "test"
creator = Create(session=your_session_name, browser="chrome")
client = creator.start()
# Now scan Whatsapp Qrcode in browser

# check state of login
if creator.state != 'CONNECTED':
    raise Exception(creator.state)


# TODO :: Not Work

options = {
    "useTemplateButtons": True,  # False for legacy
    "buttons": [
        {
            "url": 'https://wppconnect.io/',
            "text": 'WPPConnect Site'
        },
        {
            "phoneNumber": '+55 11 22334455',
            "text": 'Call me'
        },
        {
            "id": 'your custom id 1',
            "text": 'Some text'
        },
        {
            "id": 'another id 2',
            "text": 'Another text'
        }
    ],
    "title": 'Title text',  # Optional
    "footer": 'Footer text'  # Optional
}
phone_number = "201016708170"  # or "+201016708170"
message = 'WPPConnect message with buttons'
# example
# Simple message
result = client.sendText(phone_number, message, options)
print(result)
