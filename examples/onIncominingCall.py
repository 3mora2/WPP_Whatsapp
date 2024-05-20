from WPP_Whatsapp import Create
import logging

logger = logging.getLogger(name="WPP_Whatsapp")
logger.setLevel(logging.DEBUG)

# start client with your session name
your_session_name = "test"
creator = Create(session=your_session_name)
client = creator.start()
# Now scan Whatsapp Qrcode in browser

# check state of login
if creator.state != 'CONNECTED':
    raise Exception(creator.state)


def callback(*args, **kwargs):
    print(args, kwargs)


# Add Listen
creator.client.onIncomingCall(callback)
creator.loop.run_forever()
