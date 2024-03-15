# WPP_Whatsapp
<p align="center">
  <a href="https://pypi.org/project/WPP-Whatsapp"><img alt="PyPI Version" src="https://img.shields.io/pypi/v/WPP_Whatsapp.svg?maxAge=86400" /></a>
  <a href="https://pypi.org/project/WPP-Whatsapp"><img alt="View" src="https://static.pepy.tech/personalized-badge/WPP_Whatsapp?period=total&units=international_system&left_text=Downloads"/></a>
</p>

WPP_Whatsapp aim of exporting functions from WhatsApp Web to the python, which can be used to support the creation of
any interaction, such as customer service, media sending, intelligence recognition based on phrases artificial and many
other things, use your imagination         
WPP_Whatsapp > [WPPConnect](https://github.com/wppconnect-team/wppconnect) Converted to python, so Documentation is same


## Online channels

[![Telegram Group](https://img.shields.io/badge/Telegram-Group-32AFED?logo=telegram)](https://t.me/WPP_Whatsapp)

## Functions

|                                                            |   |
|------------------------------------------------------------|---|
| Automatic QR Refresh                                       | ✔ |
| Send **text, image, video, audio and docs**                | ✔ |
| Get **contacts, chats, groups, group members, Block List** | ✔ |
| Send contacts                                              | ✔ |
| Send stickers                                              | ✔ |
| Send stickers GIF                                          | ✔ |
| Multiple Sessions                                          | ✔ |
| Forward Messages                                           | ✔ |
| Receive message                                            | ✔ |
| insert user section                                        | ✔ |
| Send _location_                                            | ✔ |
| **and much more**                                          | ✔ |

See more at <a href="https://wppconnect.io/wppconnect/classes/Whatsapp.html">WhatsApp methods</a>
## Getting Started

### Installation

installed with [pip](https://pip.pypa.io):
```commandline
pip install WPP_Whatsapp -U
```
Alternatively, you can grab the latest source code from [GitHub](https://github.com/3mora2/WPP_Whatsapp):

```
pip install git+https://github.com/3mora2/WPP_Whatsapp
```



### Send Text

```python
from WPP_Whatsapp import Create

# start client with your session name
your_session_name = "test"
creator = Create(session=your_session_name)
client = creator.start()
# Now scan Whatsapp Qrcode in browser

# check state of login
if creator.state != 'CONNECTED':
    raise Exception(creator.state)

phone_number = "201016708170"  # or "+201016708170"
message = "hello from wpp"

# Simple message
result = client.sendText(phone_number, message)
```

### Receive Messages(Auto Replay)
```python
from WPP_Whatsapp import Create

# start client with your session name
your_session_name = "test"
creator = Create(session=your_session_name)
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


# Add Listen To New Message
creator.client.onMessage(new_message)
```

### <a href="https://github.com/3mora2/WPP_Whatsapp/tree/main/examples">For More Examples</a>
