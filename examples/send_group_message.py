from WPP_Whatsapp import Create

# start client with your session name
your_session_name = "test"
creator = Create(session=your_session_name, browser="firefox")
client = creator.start()
# Now scan Whatsapp Qrcode in browser

# check state of login
if creator.state != 'CONNECTED':
    raise Exception(creator.state)

# Send to Group
group_name = 'Your Group Name'  # change it

all_groups = client.getAllGroups(False)
# Filter Groups By Name
current_group = next(filter(lambda x: x.get("name") == group_name, all_groups), {})
current_group_id = current_group.get("id", {}).get("_serialized")
message = "hello from wpp"

result = client.sendText(current_group_id, message)
print(result)
