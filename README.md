# WPP_Whatsapp
<p align="center">
  <a href="https://pypi.org/project/WPP-Whatsapp"><img alt="PyPI Version" src="https://img.shields.io/pypi/v/WPP_Whatsapp.svg?maxAge=86400" /></a>
  <a href="https://pypi.org/project/WPP-Whatsapp"><img alt="View" src="https://static.pepy.tech/personalized-badge/WPP_Whatsapp?period=total&units=international_system&left_text=Downloads"/></a>
  <a href="https://github.com/3mora2/WPP_Whatsapp/actions"><img alt="GitHub Actions" src="https://github.com/3mora2/WPP_Whatsapp/actions/workflows/python-publish.yml/badge.svg" /></a>
  <a href="https://python.org"><img alt="Python Version" src="https://img.shields.io/badge/python-3.9+-blue.svg" /></a>
</p>

**WPP_Whatsapp** is a powerful Python library built on top of [WPPConnect](https://github.com/wppconnect-team/wppconnect), bringing WhatsApp Web automation to Python developers.

> 💡 **Looking for something else?** Check out [neonize](https://github.com/krypton-byte/neonize) - A powerful Python library built on top of **Whatsmeow**, enabling seamless WhatsApp automation with enterprise-grade performance.

📚 **Looking for documentation?** Check out our [Complete Documentation](docs/README.md)

The native `AsyncClient`, composed services, tracked sending and release recovery
are documented in the [architecture and migration guide](docs/ARCHITECTURE.md).
Existing `Create` / `Whatsapp` methods remain available. See the
[native asyncio example](examples/native_async.py).

---

## ✨ Features

| Feature | Status |
|---------|--------|
| Automatic QR Refresh | ✅ |
| Send **text, image, video, audio, documents** | ✅ |
| Get **contacts, chats, groups, group members** | ✅ |
| Send contacts, stickers, locations | ✅ |
| Multiple Sessions Support | ✅ |
| Forward Messages | ✅ |
| Receive Messages with Callbacks | ✅ |
| Group Management | ✅ |
| Business Features | ✅ |
| Rate Limiting | ✅ |

---

## 🚀 Quick Start

### Installation

**Using pip:**
```bash
pip install wpp-whatsapp
```

**Using uv (Recommended):**
```bash
uv add wpp-whatsapp
```

### Your First Bot (2 minutes)

```python
from WPP_Whatsapp import Create

# Create and start client
creator = Create(session="mybot")

client = creator.start()
# Define message handler
def on_message(msg):
    if msg.get('body') and not msg.get('isGroupMsg'):
        # Auto-reply
        client.sendText(msg.get('from'), "Thanks for your message! 🤖")

# Register handler
client.onMessage(on_message)

print("Bot started!")
```

**That's it!** Your WhatsApp bot is now running! 🎉

### JavaScript runtime and message history

The package includes WPPConnect 2.3.4 and WA-JS 4.6.1. By default, startup first
checks GitHub for the latest stable WA-JS release and downloads its JavaScript
asset. If the check or download fails, it uses the bundled WA-JS version. This
attempt has a 30-second total timeout. To skip network access, pass
`Create(session="mybot", wa_js_version="bundled")`.
To opt into upstream nightly builds, pass
`Create(session="mybot", wa_js_version="nightly")`. Explicit version constraints,
JavaScript URLs, and local JavaScript files are also supported. Explicit
selections report errors if unavailable instead of silently changing versions.

```python
# Retrieve a page of history; opening the chat first is optional.
messages = client.getMessages("1234567890@c.us", {"count": 50})

# Retrieve all history available to this linked device.
messages = client.loadAndGetAllMessagesInChat(
    "1234567890@c.us", includeMe=True, includeNotifications=False
)

# Callbacks include the complete message ID, including group participants.
client.onMessage(lambda msg: print(msg["id"]))
```

Phone-to-LID mapping is resolved automatically. Pass explicit LIDs with `@lid`;
bare phone numbers, including 14-digit numbers, are treated as phone numbers.
`getAllMessagesInChat` returns only messages already loaded in memory.

---

## 📚 Documentation

We've created comprehensive documentation to help you:

- 📘 **[Quick Start Guide](docs/QUICKSTART.md)** - Get started in 5 minutes
- 📖 **[API Reference](docs/API_REFERENCE.md)** - Complete method documentation
- 🔧 **[Troubleshooting](docs/TROUBLESHOOTING.md)** - Common issues and solutions
- 💡 **[Examples](examples/README.md)** - Code examples for every use case
- ⚡ **[Advanced Examples](scripts/README.md)** - Advanced patterns and features

**Start here:** [Complete Documentation Index](docs/README.md)

---

## 💡 Examples

### Send Messages

```python
from WPP_Whatsapp import Create

creator = Create(session="test")
client = creator.start()
# Send text
client.sendText("1234567890@c.us", "Hello!")

# Send image
client.sendImage("1234567890@c.us", "image.jpg", "Beautiful sunset!")

# Send file
client.sendFile("1234567890@c.us", "document.pdf", "Here's the document")

# Send location
client.sendLocation("1234567890@c.us", 40.7128, -74.0060, title="New York")
```

### Receive Messages

```python
from WPP_Whatsapp import Create

creator = Create(session="test")
client = creator.start()

def on_message(message):
    # Ignore group messages
    if message.get('isGroupMsg'):
        return
    
    # Process message
    chat_id = message.get('from')
    text = message.get('body')
    
    if 'hello' in text.lower():
        client.sendText(chat_id, "Hi there! 👋")

client.on_message(on_message)
client.start()
```

### Group Management

```python
from WPP_Whatsapp import Create

creator = Create(session="test")
client = creator.start()

# Create group
group = client.createGroup("My Group", ["123@c.us", "456@c.us"])

# Add participant
client.addParticipant(group['gid'], "789@c.us")

# Send message to group
client.sendText(group['gid'], "Hello everyone!")
```

### More Examples

- 📂 **[Basic Examples](examples/README.md)** - Core functionality
- ⚡ **[Advanced Examples](scripts/README.md)** - Complex patterns
- 🗂️ **[Archive](archive/examples/README.md)** - Additional examples

---

## 🎯 Use Cases

WPP_Whatsapp can be used for:

- 🤖 **Chatbots** - Customer service automation
- 📢 **Broadcasting** - Safe bulk messaging with rate limiting
- 👥 **Group Management** - Automated group administration
- 📊 **Analytics** - Message tracking and statistics
- 🔄 **Integration** - Connect WhatsApp with other services
- 📱 **Auto-replies** - Intelligent response systems

---

## ⚠️ Important Notes

### Rate Limiting
Always use rate limiting for bulk operations to avoid bans:
```python
import time

contacts = ["123@c.us", "456@c.us"]
for contact in contacts:
    client.sendText(contact, "Hello")
    time.sleep(2)  # 2 second delay
```

### Best Practices
- ✅ Handle errors gracefully
- ✅ Use unique session names
- ✅ Implement reconnection logic
- ✅ Test with small groups first
- ✅ Respect WhatsApp's terms of service

---

## 🆘 Need Help?

### Documentation
- 📚 [Complete Documentation](docs/README.md)
- 🚀 [Quick Start Guide](docs/QUICKSTART.md)
- 🔧 [Troubleshooting](docs/TROUBLESHOOTING.md)

### Community
- 💬 [GitHub Discussions](https://github.com/3mora2/WPP_Whatsapp/discussions)
- 🐛 [Report Issues](https://github.com/3mora2/WPP_Whatsapp/issues)
- 💡 [Feature Requests](https://github.com/3mora2/WPP_Whatsapp/issues)

---

## 📦 Project Structure

```
WPP_Whatsapp/
├── WPP_Whatsapp/      # Main package
├── docs/              # Documentation
├── examples/          # Basic examples
├── scripts/           # Advanced examples
├── archive/           # Additional examples
├── tests/             # Test suite
├── README.md          # This file
├── pyproject.toml     # Project configuration
└── CHANGELOG.md       # Version history
```

---

## 🤝 Contributing

We welcome contributions! Here's how you can help:

- 📝 Improve documentation
- 🐛 Report bugs
- 💡 Suggest features
- 🔧 Submit pull requests
- 📚 Add examples

See [Contributing Guide](docs/README.md#-contributing) for details.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).

---

## 🙏 Acknowledgments

- Built on top of [WPPConnect](https://github.com/wppconnect-team/wppconnect)
- Powered by [Playwright](https://playwright.dev/)

---

**Made with ❤️ by [Ammar Alkotb](https://github.com/3mora2)**

**Happy Coding! 🎉**
