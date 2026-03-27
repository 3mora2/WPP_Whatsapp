# 🚀 Quick Start Guide

Get started with WPP_Whatsapp in minutes! This guide will help you set up and run your first WhatsApp bot.

---

## 📦 Installation

### Using uv (Recommended)
```bash
# Install uv if you don't have it
pip install uv

# Create a new project
uv init my-whatsapp-bot
cd my-whatsapp-bot

# Add WPP_Whatsapp
uv add wpp-whatsapp

# Install dependencies
uv sync
```

### Using pip
```bash
pip install wpp-whatsapp
```

---

## ⚡ Your First Bot (5 Minutes)

### Step 1: Basic Setup

Create a file called `bot.py`:

```python
from WPP_Whatsapp import Create

# Create a simple client
client = Create(session="mybot")

# Define a message handler
def on_message(message):
    print(f"New message from {message.get('from')}: {message.get('body')}")
    
    # Echo the message back
    if message.get('body'):
        client.sendText(message.get('from'), f"Echo: {message.get('body')}")

# Register the handler
client.on_message(on_message)

# Start the bot
print("Bot is running! Scan the QR code...")
client.start()
```

### Step 2: Run Your Bot

```bash
uv run python bot.py
# or
python bot.py
```

### Step 3: Scan QR Code

A QR code will appear in your terminal. Scan it with WhatsApp:
1. Open WhatsApp on your phone
2. Go to Settings → Linked Devices
3. Tap "Link a Device"
4. Scan the QR code

**That's it! Your bot is now running! 🎉**

---

## 🎯 Common Use Cases

### 1. Auto-Reply Bot

```python
from WPP_Whatsapp import Create

client = Create(session="autoreply")

def on_message(msg):
    # Ignore group messages
    if msg.get('isGroupMsg'):
        return
    
    # Auto-reply to messages
    client.sendText(
        msg.get('from'),
        "Thanks for your message! I'll get back to you soon."
    )

client.on_message(on_message)
client.start()
```

### 2. Command-Based Bot

```python
from WPP_Whatsapp import Create

client = Create(session="commandbot")

def on_message(msg):
    text = msg.get('body', '').strip()
    chat_id = msg.get('from')
    
    # Command: /hello
    if text.lower() == '/hello':
        client.sendText(chat_id, "Hello! 👋")
    
    # Command: /help
    elif text.lower() == '/help':
        help_text = """
Available Commands:
/hello - Say hello
/help - Show this help
/ping - Check if bot is alive
/time - Get current time
        """
        client.sendText(chat_id, help_text)
    
    # Command: /ping
    elif text.lower() == '/ping':
        client.sendText(chat_id, "Pong! 🏓")

client.on_message(on_message)
client.start()
```

### 3. Media Downloader

```python
from WPP_Whatsapp import Create
import os

client = Create(session="mediadownloader")

def on_message(msg):
    # Check if message has media
    if msg.get('type') in ['image', 'video', 'audio', 'document']:
        print(f"Downloading media from {msg.get('from')}...")
        
        # Download the media
        buffer = client.decryptFile(msg)
        
        # Save to file
        filename = f"downloads/{msg.get('id')}.{msg.get('mimetype').split('/')[-1]}"
        os.makedirs('downloads', exist_ok=True)
        
        with open(filename, 'wb') as f:
            f.write(buffer)
        
        client.sendText(msg.get('from'), "✅ Media downloaded successfully!")

client.on_message(on_message)
client.start()
```

### 4. Group Manager

```python
from WPP_Whatsapp import Create

client = Create(session="groupmanager")

def on_message(msg):
    if not msg.get('isGroupMsg'):
        return
    
    text = msg.get('body', '').strip()
    group_id = msg.get('from')
    
    # Command: /add (admin only)
    if text.startswith('/add '):
        number = text.replace('/add ', '')
        try:
            client.addParticipant(group_id, f"{number}@c.us")
            client.sendText(group_id, f"✅ Added {number} to the group")
        except Exception as e:
            client.sendText(group_id, f"❌ Error: {str(e)}")
    
    # Command: /remove (admin only)
    elif text.startswith('/remove '):
        number = text.replace('/remove ', '')
        try:
            client.removeParticipant(group_id, f"{number}@c.us")
            client.sendText(group_id, f"✅ Removed {number} from the group")
        except Exception as e:
            client.sendText(group_id, f"❌ Error: {str(e)}")

client.on_message(on_message)
client.start()
```

### 5. Broadcast Messages

```python
from WPP_Whatsapp import Create

client = Create(session="broadcast")

# List of contacts to send messages to
contacts = [
    "1234567890@c.us",
    "0987654321@c.us",
    "1122334455@c.us"
]

# Send broadcast message
for contact in contacts:
    try:
        client.sendText(contact, "🎉 Special offer! Check out our latest deals!")
        print(f"Sent to {contact}")
    except Exception as e:
        print(f"Failed to send to {contact}: {e}")

client.start()
```

---

## 🔧 Configuration Options

### Custom Client Setup

```python
from WPP_Whatsapp import Create

client = Create(
    session="mybot",
    headless=True,              # Run in background
    browser_args=['--no-sandbox'],  # Browser arguments
    disable_browser=False,      # Don't disable browser
    whatsapp_web_version="2.2412.54",  # Specific version
)
```

### Using Context Manager (Recommended)

```python
from WPP_Whatsapp import Create

# Automatic cleanup
with Create(session="mybot") as client:
    client.on_message(lambda msg: print(f"Message: {msg}"))
    client.start()
# Session automatically closes here
```

### Async/Await Pattern

```python
import asyncio
from WPP_Whatsapp import Create

async def main():
    client = Create(session="asyncbot")
    
    async def on_message(msg):
        await asyncio.sleep(1)  # Simulate async work
        client.sendText(msg.get('from'), "Received!")
    
    client.on_message(on_message)
    client.start()

asyncio.run(main())
```

---

## 📚 What's Next?

- Check out the [Examples](examples/) folder for more code samples
- Read the [API Reference](api_reference.md) for complete method documentation
- Join our [Community](https://github.com/3mora2/WPP_Whatsapp/discussions) for help

---

## ⚠️ Important Notes

### Best Practices
1. **Always handle errors** - Wrap your code in try-except blocks
2. **Use rate limiting** - Don't send too many messages too quickly
3. **Respect WhatsApp's terms** - Use responsibly
4. **Test thoroughly** - Test with small groups first

### Common Issues

**QR Code not appearing?**
- Make sure you have a terminal that supports ANSI colors
- Try running with `headless=False`

**Session not saving?**
- Check write permissions in the tokens directory
- Use unique session names

**Bot disconnecting frequently?**
- Implement reconnection logic
- Check your internet connection
- Update to the latest version

---

## 🆘 Need Help?

- **Documentation:** Check the `/docs` folder
- **Issues:** https://github.com/3mora2/WPP_Whatsapp/issues
- **Discussions:** https://github.com/3mora2/WPP_Whatsapp/discussions

**Happy Botting! 🤖**
