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

message = {
                "buttonText": 'Click here',
                "description": 'Choose one option',
                "sections": [
                  {
                    "title": 'Section 1',
                    'rows': [
                      {
                        'rowId': 'my_custom_id',
                        'title': 'Test 1',
                        'description': 'Description 1',
                      },
                      {
                        'rowId': '2',
                        "title": 'Test 2',
                        'description': 'Description 2',
                      },
                    ],
                  },
                ],
              }
phone_number = "201016708170"  # or "+201016708170"

# example
# Simple message
result = client.sendListMessage(phone_number, message)
print(result)

