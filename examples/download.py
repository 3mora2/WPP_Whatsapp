import base64
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

message_id = "false_0@c.us_898814798703028-1_0@c.us"

media = client.downloadMedia(message_id)
# OR
# message = client.getMessageById(message_id)
# media = client.downloadMedia(message)

# Remove the "data:video/mp4;base64," prefix
base64_data = media.split(',')[1]

# Decode the Base64 string
video_data = base64.b64decode(base64_data)

# Specify the file path where you want to save the video
file_path = 'output_video.mp4'

# Write the binary data to the file
with open(file_path, 'wb') as file:
    file.write(video_data)
