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
filePath="https://images.unsplash.com/photo-1466442929976-97f336a657be"
# filePath=r"C:\Users\ammar\Downloads\12.jpg"
phone_number = "***********"  # or "+***********"

# example
# Simple message
result = client.sendImage(phone_number, filePath=filePath, caption=message)
print(result)
