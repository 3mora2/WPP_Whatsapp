# 💻 WPPConnect Python Examples

This folder contains essential examples demonstrating various features of the WPPConnect Python library.

---

## 📋 **Available Examples**

### **Core Examples**

#### **1. Receive Messages** ⭐ Recommended Start
- **File:** `receive_message.py`
- **Features:** Listen for incoming messages, event handlers
- **Level:** Beginner

```python
from WPP_Whatsapp import Create

client = Create(session="mybot")

def on_message(msg):
    print(f"New message: {msg}")

client.on_message(on_message)
client.start()
```

#### **2. Get QR Code**
- **File:** `get_qrcode.py`
- **Features:** Display QR code for authentication
- **Level:** Beginner

#### **3. Get Messages**
- **File:** `get_messages.py`
- **Features:** Retrieve chat history
- **Level:** Beginner

#### **4. Download Media**
- **File:** `download.py`
- **Features:** Download images, videos, documents
- **Level:** Intermediate

#### **5. Context Manager**
- **File:** `context_manager_example.py`
- **Features:** Safe session management with automatic cleanup
- **Level:** Beginner

```python
# Automatic cleanup
with Create(session="test") as client:
    client.sendText("123@c.us", "Hello!")
```

---

## 🚀 **Running Examples**

### **Prerequisites**
```bash
# Install dependencies
uv sync
uv pip install -e .
```

### **Run Any Example**
```bash
# Basic example
uv run python examples/get_qrcode.py

# Message listener
uv run python examples/receive_message.py
```

---

## 📊 **Quick Reference**

| Example | Purpose | Level |
|---------|---------|-------|
| `receive_message.py` | Listen for messages | Beginner |
| `get_qrcode.py` | Authentication | Beginner |
| `get_messages.py` | Chat history | Beginner |
| `download.py` | Media downloads | Intermediate |
| `context_manager_example.py` | Safe sessions | Beginner |

---

## 🗂️ **More Examples**

Additional examples are available in the `archive/examples/` folder:
- Bulk messaging
- Group management
- Button/list messages
- Status updates
- Community management
- And more...

---

## 💡 **Tips**

1. **Start Simple:** Begin with `receive_message.py` or `get_qrcode.py`
2. **Session Management:** Use context managers for automatic cleanup
3. **Error Handling:** Always handle exceptions gracefully
4. **Rate Limiting:** Use rate limiting for bulk operations

---

## ⚠️ **Important Notes**

### **Session Management**
- Use unique session names for different accounts
- Always close sessions properly
- Don't run multiple sessions with same phone number

### **Best Practices**
- Handle errors gracefully
- Log important events
- Test with small batches first
- Monitor WhatsApp Web for bans

---

## 🎯 **Next Steps**

After reviewing examples:
1. ✅ Try running basic examples
2. ✅ Modify examples for your use case
3. ✅ Check documentation in `/docs` folder
4. ✅ Start building your own bot!

---

## 📞 **Support**

- **Issues:** https://github.com/3mora2/WPP_Whatsapp/issues
- **Documentation:** `/docs` folder
- **PyPI:** https://pypi.org/project/wpp-whatsapp/

---

**Happy Coding! 🎉**
