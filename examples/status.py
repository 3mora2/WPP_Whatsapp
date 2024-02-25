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

text = "Status from wpp"

# example
# Simple message
# result = client.sendTextStatus(text)
# print(result)
#
# result = client.sendImageStatus("https://images.unsplash.com/photo-1466442929976-97f336a657be")
# print(result)
#
# result = client.sendVideoStatus("https://vod-progressive.akamaized.net/exp=1707553213~acl=%2Fvimeo-prod-skyfire-std-us%2F01%2F313%2F15%2F376569104%2F1571696626.mp4~hmac=d1f3ea53b39913411368a7c3cf761dd9f85ac6f335658693682db6a6249ad14b/vimeo-prod-skyfire-std-us/01/313/15/376569104/1571696626.mp4")
# print(result)
