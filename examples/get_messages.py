from WPP_Whatsapp import Create

# start client with your session name
your_session_name = "test"
creator = Create(session=your_session_name)
client = creator.start()
# Now scan Whatsapp Qrcode in browser

# check state of login
if creator.state != 'CONNECTED':
    raise Exception(creator.state)

phone_number = "***********"  # or "+***********"
client.waitForInChat()
# example
messages = client.getMessages(phone_number)
print(messages)
# client.joinGroup("KOtrjvEwQk8DlDw8mv9IAE")
