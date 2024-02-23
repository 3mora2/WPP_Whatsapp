from WPP_Whatsapp import Create

# start client with your session name
your_session_name = "test"
creator = Create(session=your_session_name, browser="firefox")
client = creator.start()
# Now scan Whatsapp Qrcode in browser

# check state of login
if creator.state != 'CONNECTED':
    raise Exception(creator.state)

message = "hello from wpp"
filePath="path/to/file"
phone_number = "201016708170"  # or "+201016708170"

# example
# Simple message
result = client.sendImage(phone_number, filePath=filePath, caption=message)
print(result)
