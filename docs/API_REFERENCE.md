# 📖 API Reference

Complete reference for all WPP_Whatsapp methods and features.

---

## 📑 Table of Contents

1. [Sender Methods](#sender-methods)
2. [Message Listening](#message-listening)
3. [Group Management](#group-management)
4. [Contact Management](#contact-management)
5. [Profile Methods](#profile-methods)
6. [Media Methods](#media-methods)
7. [Status/Stories](#statusstories)
8. [Business Features](#business-features)
9. [Utility Methods](#utility-methods)

---

## Sender Methods

### Send Text Message

```python
client.sendText(chatId, message)
```

**Parameters:**
- `chatId` (str): Contact or group ID (e.g., "1234567890@c.us")
- `message` (str): Text message to send

**Example:**
```python
# Send to individual
client.sendText("1234567890@c.us", "Hello!")

# Send to group
client.sendText("123456789@g.us", "Hello everyone!")

# Reply to a message
client.sendText("1234567890@c.us", "Replied!", reply_to="message_id")
```

---

### Send Image

```python
client.sendImage(chatId, file_path, caption=None)
```

**Parameters:**
- `chatId` (str): Contact or group ID
- `file_path` (str): Path to image file or URL
- `caption` (str, optional): Image caption

**Example:**
```python
# Send from file
client.sendImage("1234567890@c.us", "path/to/image.jpg", "Beautiful sunset!")

# Send from URL
client.sendImage("1234567890@c.us", "https://example.com/image.jpg")
```

---

### Send File/Document

```python
client.sendFile(chatId, file_path, caption=None)
```

**Parameters:**
- `chatId` (str): Contact or group ID
- `file_path` (str): Path to file or URL
- `caption` (str, optional): File caption

**Example:**
```python
client.sendFile("1234567890@c.us", "document.pdf", "Here's the document")
```

---

### Send Video

```python
client.sendVideo(chatId, file_path, caption=None)
```

**Example:**
```python
client.sendVideo("1234567890@c.us", "video.mp4", "Check this out!")
```

---

### Send Audio

```python
client.sendAudio(chatId, file_path)
```

**Example:**
```python
client.sendAudio("1234567890@c.us", "audio.mp3")
```

---

### Send Voice Note

```python
client.sendVoice(chatId, file_path)
```

**Example:**
```python
client.sendVoice("1234567890@c.us", "voice_note.ogg")
```

---

### Send Location

```python
client.sendLocation(chatId, latitude, longitude, title=None, address=None)
```

**Example:**
```python
client.sendLocation(
    "1234567890@c.us",
    40.7128,
    -74.0060,
    title="New York",
    address="Times Square"
)
```

---

### Send Contact

```python
client.sendContact(chatId, contact_id)
```

**Example:**
```python
client.sendContact("1234567890@c.us", "9876543210@c.us")
```

---

### Send Button Message

```python
client.sendButtons(chatId, title, buttons, message=None)
```

**Example:**
```python
buttons = [
    {"id": "btn1", "text": "Option 1"},
    {"id": "btn2", "text": "Option 2"},
    {"id": "btn3", "text": "Option 3"}
]

client.sendButtons(
    "1234567890@c.us",
    "Choose an option:",
    buttons,
    "Please select:"
)
```

---

### Send List Message

```python
client.sendList(chatId, title, button_text, sections, message=None)
```

**Example:**
```python
sections = [
    {
        "title": "Section 1",
        "rows": [
            {"id": "row1", "title": "Item 1", "description": "Desc 1"},
            {"id": "row2", "title": "Item 2", "description": "Desc 2"}
        ]
    }
]

client.sendList(
    "1234567890@c.us",
    "Menu",
    "View Options",
    sections,
    "Select from menu:"
)
```

---

### Send Link Preview

```python
client.sendLinkPreview(chatId, url, title=None, description=None)
```

**Example:**
```python
client.sendLinkPreview(
    "1234567890@c.us",
    "https://example.com",
    "Check this out!"
)
```

---

## Message Listening

### On Message

```python
client.on_message(callback)
```

**Example:**
```python
def handle_message(msg):
    print(f"From: {msg['from']}")
    print(f"Message: {msg['body']}")
    print(f"Type: {msg['type']}")

client.on_message(handle_message)
```

**Message Object:**
```python
{
    'id': 'message_id',
    'from': '1234567890@c.us',
    'to': 'bot@c.us',
    'body': 'Hello!',
    'type': 'chat',
    'isGroupMsg': False,
    'timestamp': 1234567890,
    'fromMe': False,
    'hasMedia': False,
    'mimetype': 'text/plain'
}
```

---

### On Any Message

```python
client.on_any_message(callback)
```

**Example:**
```python
client.on_any_message(lambda msg: print(f"Any message: {msg['id']}"))
```

---

### On State Change

```python
client.on_state_change(callback)
```

**Example:**
```python
def on_state_change(state):
    print(f"State changed: {state}")
    # States: CONNECTED, DISCONNECTED, PAIRING, etc.

client.on_state_change(on_state_change)
```

---

### On Incoming Call

```python
client.on_incoming_call(callback)
```

**Example:**
```python
def on_call(call):
    print(f"Incoming call from: {call['from']}")
    # Auto-reject call
    client.rejectCall(call['id'])

client.on_incoming_call(on_call)
```

---

## Group Management

### Create Group

```python
client.createGroup(name, participants)
```

**Example:**
```python
participants = ["1234567890@c.us", "0987654321@c.us"]
group = client.createGroup("My Group", participants)
print(f"Group created: {group['gid']}")
```

---

### Add Participant

```python
client.addParticipant(groupId, participantId)
```

**Example:**
```python
client.addParticipant("123456789@g.us", "1111111111@c.us")
```

---

### Remove Participant

```python
client.removeParticipant(groupId, participantId)
```

**Example:**
```python
client.removeParticipant("123456789@g.us", "1111111111@c.us")
```

---

### Promote to Admin

```python
client.promoteParticipant(groupId, participantId)
```

**Example:**
```python
client.promoteParticipant("123456789@g.us", "1111111111@c.us")
```

---

### Demote Admin

```python
client.demoteParticipant(groupId, participantId)
```

**Example:**
```python
client.demoteParticipant("123456789@g.us", "1111111111@c.us")
```

---

### Get Group Info

```python
client.getGroupInfo(groupId)
```

**Example:**
```python
info = client.getGroupInfo("123456789@g.us")
print(f"Group name: {info['name']}")
print(f"Participants: {info['participants']}")
```

---

### Leave Group

```python
client.leaveGroup(groupId)
```

**Example:**
```python
client.leaveGroup("123456789@g.us")
```

---

### Get All Groups

```python
client.getAllGroups()
```

**Example:**
```python
groups = client.getAllGroups()
for group in groups:
    print(f"Group: {group['name']} - {group['id']}")
```

---

## Contact Management

### Get All Contacts

```python
client.getAllContacts()
```

**Example:**
```python
contacts = client.getAllContacts()
for contact in contacts:
    print(f"{contact['name']}: {contact['id']}")
```

---

### Get Contact by ID

```python
client.getContact(contactId)
```

**Example:**
```python
contact = client.getContact("1234567890@c.us")
print(f"Name: {contact['name']}")
print(f"Number: {contact['number']}")
```

---

### Check Number Exists

```python
client.checkNumberStatus(number)
```

**Example:**
```python
status = client.checkNumberStatus("1234567890")
if status.get('exists'):
    print("Number is on WhatsApp!")
```

---

### Block Contact

```python
client.blockContact(contactId)
```

**Example:**
```python
client.blockContact("1234567890@c.us")
```

---

### Unblock Contact

```python
client.unblockContact(contactId)
```

**Example:**
```python
client.unblockContact("1234567890@c.us")
```

---

## Profile Methods

### Get Profile Picture

```python
client.getProfilePic(contactId)
```

**Example:**
```python
pic_url = client.getProfilePic("1234567890@c.us")
print(f"Profile picture: {pic_url}")
```

---

### Get My Profile

```python
client.getMyProfile()
```

**Example:**
```python
profile = client.getMyProfile()
print(f"My name: {profile['name']}")
print(f"My number: {profile['number']}")
```

---

### Set Profile Name

```python
client.setProfileName(name)
```

**Example:**
```python
client.setProfileName("John Doe")
```

---

### Set Profile Picture

```python
client.setProfilePic(file_path)
```

**Example:**
```python
client.setProfilePic("path/to/photo.jpg")
```

---

## Media Methods

### Download Media

```python
client.decryptFile(message)
```

**Example:**
```python
def on_message(msg):
    if msg.get('hasMedia'):
        buffer = client.decryptFile(msg)
        with open("downloaded_file", "wb") as f:
            f.write(buffer)

client.on_message(on_message)
```

---

### Get Media Info

```python
client.getMediaInfo(message)
```

**Example:**
```python
info = client.getMediaInfo(msg)
print(f"Mimetype: {info['mimetype']}")
print(f"Size: {info['size']}")
```

---

## Status/Stories

### Send Text Status

```python
client.sendTextStatus(text, options=None)
```

**Example:**
```python
client.sendTextStatus("Hello World!")
```

---

### Send Image Status

```python
client.sendImageStatus(file_path)
```

**Example:**
```python
client.sendImageStatus("status_image.jpg")
```

---

### Send Video Status

```python
client.sendVideoStatus(file_path)
```

**Example:**
```python
client.sendVideoStatus("status_video.mp4")
```

---

## Business Features

### Send Product

```python
client.sendProduct(chatId, product_id)
```

**Example:**
```python
client.sendProduct("1234567890@c.us", "product_123")
```

---

### Send Catalog

```python
client.sendCatalog(chatId)
```

**Example:**
```python
client.sendCatalog("1234567890@c.us")
```

---

### Get Business Profile

```python
client.getBusinessProfile(contactId)
```

**Example:**
```python
profile = client.getBusinessProfile("1234567890@c.us")
print(f"Business: {profile['name']}")
print(f"Description: {profile['description']}")
```

---

## Utility Methods

### Get QR Code

```python
client.getQrCode()
```

**Example:**
```python
qr = client.getQrCode()
print(f"Scan this QR: {qr}")
```

---

### Is Logged In

```python
client.isConnected()
```

**Example:**
```python
if client.isConnected():
    print("Bot is connected!")
```

---

### Logout

```python
client.logout()
```

**Example:**
```python
client.logout()
```

---

### Close Session

```python
client.close()
```

**Example:**
```python
client.close()
```

---

### Start Typing

```python
client.startTyping(chatId)
```

**Example:**
```python
client.startTyping("1234567890@c.us")
time.sleep(2)
client.sendText("1234567890@c.us", "Hello!")
```

---

### Stop Typing

```python
client.stopTyping(chatId)
```

**Example:**
```python
client.stopTyping("1234567890@c.us")
```

---

### Start Recording

```python
client.startRecording(chatId)
```

**Example:**
```python
client.startRecording("1234567890@c.us")
```

---

### Stop Recording

```python
client.stopRecording(chatId)
```

**Example:**
```python
client.stopRecording("1234567890@c.us")
```

---

### Get Battery Level

```python
client.getBatteryLevel()
```

**Example:**
```python
battery = client.getBatteryLevel()
print(f"Battery: {battery}%")
```

---

### Get Platform

```python
client.getPlatform()
```

**Example:**
```python
platform = client.getPlatform()
print(f"Platform: {platform}")  # android, iphone, web, etc.
```

---

## Error Handling

### Try-Except Pattern

```python
try:
    client.sendText("1234567890@c.us", "Hello!")
except Exception as e:
    print(f"Error: {e}")
```

---

### Check Number Before Sending

```python
status = client.checkNumberStatus("1234567890")
if status.get('exists'):
    client.sendText(f"{status['number']}@c.us", "Hello!")
else:
    print("Number not on WhatsApp")
```

---

## Complete Example

```python
from WPP_Whatsapp import Create
import time

# Create client
client = Create(session="complete_bot")

# Message handler
def on_message(msg):
    try:
        # Ignore group messages and own messages
        if msg.get('isGroupMsg') or msg.get('fromMe'):
            return
        
        text = msg.get('body', '').lower()
        chat_id = msg.get('from')
        
        # Show typing
        client.startTyping(chat_id)
        time.sleep(1)
        client.stopTyping(chat_id)
        
        # Commands
        if text == '/hello':
            client.sendText(chat_id, "Hello! 👋")
        
        elif text == '/help':
            help_text = """
Available Commands:
/hello - Say hello
/help - Show help
/image - Get an image
            """
            client.sendText(chat_id, help_text)
        
        elif text == '/image':
            client.sendImage(chat_id, "path/to/image.jpg", "Here's an image!")
        
        else:
            # Echo
            client.sendText(chat_id, f"You said: {text}")
    
    except Exception as e:
        print(f"Error: {e}")

# Register handler
client.on_message(on_message)

# State change handler
def on_state(state):
    print(f"State: {state}")

client.on_state_change(on_state)

# Start
print("Bot started!")
client.start()
```

---

**For more examples, check the `/examples` folder!**
