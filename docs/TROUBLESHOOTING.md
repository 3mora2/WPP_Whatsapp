# 🔧 Troubleshooting Guide

Common issues and their solutions for WPP_Whatsapp.

---

## 📋 Table of Contents

1. [Installation Issues](#installation-issues)
2. [Connection Issues](#connection-issues)
3. [QR Code Issues](#qr-code-issues)
4. [Message Sending Issues](#message-sending-issues)
5. [Media Issues](#media-issues)
6. [Session Issues](#session-issues)
7. [Performance Issues](#performance-issues)
8. [Error Messages](#error-messages)

---

## Installation Issues

### Issue: `ModuleNotFoundError: No module named 'WPP_Whatsapp'`

**Solution:**
```bash
# Make sure the package is installed
uv pip install wpp-whatsapp

# Or if developing locally
uv pip install -e .

# Verify installation
uv pip show wpp-whatsapp
```

---

### Issue: `uv: command not found`

**Solution:**
```bash
# Install uv
pip install uv

# Or on macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Verify installation
uv --version
```

---

### Issue: Dependency Conflicts

**Solution:**
```bash
# Create a fresh virtual environment
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
uv sync

# Or with pip
pip install --upgrade pip
pip install wpp-whatsapp
```

---

## Connection Issues

### Issue: QR Code Not Appearing

**Possible Causes:**
1. Terminal doesn't support ANSI colors
2. Browser not launching properly
3. Network issues

**Solutions:**

```python
# Try with headless=False
client = Create(session="mybot", headless=False)

# Or specify browser path
client = Create(
    session="mybot",
    browser_args=['--no-sandbox', '--disable-setuid-sandbox']
)
```

**Check your internet connection:**
```bash
ping google.com
```

---

### Issue: "Session Unpaired" / Disconnected Frequently

**Solutions:**

1. **Implement reconnection logic:**
```python
from WPP_Whatsapp import Create
import time

client = Create(session="mybot")

def on_state_change(state):
    print(f"State: {state}")
    if state in ['DISCONNECTED', 'UNPAIRED']:
        print("Reconnecting...")
        time.sleep(5)
        # Client will auto-reconnect

client.on_state_change(on_state_change)
client.start()
```

2. **Use a stable session name:**
```python
# Don't change session name between runs
client = Create(session="my_persistent_bot")  # Good
client = Create(session="random_session")     # Bad
```

3. **Clear corrupted session:**
```bash
# Delete token file
rm tokens/mybot.token  # On Windows: del tokens\mybot.token

# Restart
```

---

### Issue: Browser Crashes

**Solutions:**

```python
# Add browser arguments
client = Create(
    session="mybot",
    browser_args=[
        '--no-sandbox',
        '--disable-setuid-sandbox',
        '--disable-dev-shm-usage',
        '--disable-accelerated-2d-canvas',
        '--no-first-run',
        '--no-zygote'
    ]
)
```

---

## QR Code Issues

### Issue: Can't Scan QR Code

**Possible Causes:**
1. QR code expired (they refresh every 30 seconds)
2. Screen brightness too low
3. Camera focus issues

**Solutions:**
1. Wait for QR code to refresh
2. Increase screen brightness
3. Clean camera lens
4. Try WhatsApp Web → Link a Device

---

### Issue: QR Code Shows as Squares/Characters

**This is normal!** The QR code is displayed in ASCII format in the terminal.

**To make it clearer:**
```python
# Use a terminal that supports ANSI colors
# Windows: Use Windows Terminal or PowerShell
# macOS/Linux: Use iTerm2 or modern terminal
```

---

## Message Sending Issues

### Issue: "Number not on WhatsApp"

**Solution:**
```python
# Check number before sending
status = client.checkNumberStatus("1234567890")
if status.get('exists'):
    client.sendText(f"{status['number']}@c.us", "Hello!")
else:
    print("Number not registered on WhatsApp")
```

**Number Format:**
- ✅ Correct: `1234567890@c.us`
- ❌ Wrong: `+1234567890@c.us`
- ❌ Wrong: `001234567890@c.us`

---

### Issue: Messages Not Being Delivered

**Possible Causes:**
1. Rate limiting by WhatsApp
2. Invalid chat ID
3. Contact blocked you
4. Account flagged

**Solutions:**

1. **Add delays between messages:**
```python
import time

contacts = ["123@c.us", "456@c.us", "789@c.us"]
for contact in contacts:
    client.sendText(contact, "Hello")
    time.sleep(2)  # Wait 2 seconds
```

2. **Use rate limiter:**
```python
from WPP_Whatsapp.utils.rate_limiter import WhatsAppRateLimiters

limiter = WhatsAppRateLimiters.conservative()  # 1 msg per 2 seconds
```

3. **Check if blocked:**
```python
contact = client.getContact("1234567890@c.us")
if contact.get('isBusiness'):
    print("Business account")
```

---

### Issue: Can't Send to Groups

**Solution:**
```python
# Make sure you're still a member of the group
# Check group ID format: should end with @g.us

group_id = "123456789@g.us"  # Correct
group_id = "123456789@c.us"  # Wrong (this is for individuals)

# Verify you're in the group
groups = client.getAllGroups()
for group in groups:
    print(f"Group: {group['name']} - {group['id']}")
```

---

## Media Issues

### Issue: Can't Download Media

**Possible Causes:**
1. Media expired (media URLs expire after some time)
2. File type not supported
3. Permission issues

**Solutions:**

```python
def on_message(msg):
    if msg.get('hasMedia'):
        try:
            # Download immediately
            buffer = client.decryptFile(msg)
            
            # Save with correct extension
            ext = msg.get('mimetype', '').split('/')[-1]
            filename = f"downloads/{msg['id']}.{ext}"
            
            with open(filename, 'wb') as f:
                f.write(buffer)
                
        except Exception as e:
            print(f"Download failed: {e}")
```

---

### Issue: Can't Send Images/Files

**Solutions:**

1. **Check file path:**
```python
import os

file_path = "path/to/file.jpg"
if os.path.exists(file_path):
    client.sendImage("123@c.us", file_path)
else:
    print(f"File not found: {file_path}")
```

2. **Check file size:**
- Images: Max 20 MB
- Videos: Max 64 MB
- Documents: Max 100 MB
- Audio: Max 16 MB

3. **Use absolute paths:**
```python
import os

abs_path = os.path.abspath("file.jpg")
client.sendImage("123@c.us", abs_path)
```

---

## Session Issues

### Issue: Session Not Saving

**Solutions:**

1. **Check permissions:**
```bash
# On Linux/Mac
chmod 755 tokens/

# On Windows - run as administrator
```

2. **Specify token location:**
```python
client = Create(
    session="mybot",
    tokens_folder="path/to/tokens"
)
```

---

### Issue: Multiple Sessions Conflict

**Solution:**
```python
# Use unique session names
client1 = Create(session="bot1")  # For phone number 1
client2 = Create(session="bot2")  # For phone number 2

# Don't use same session for different numbers!
```

---

## Performance Issues

### Issue: Bot Running Slow

**Solutions:**

1. **Use async operations:**
```python
import asyncio

async def send_messages():
    tasks = []
    for contact in contacts:
        task = asyncio.create_task(send_message(contact))
        tasks.append(task)
    await asyncio.gather(*tasks)
```

2. **Reduce browser memory:**
```python
client = Create(
    session="mybot",
    browser_args=['--disable-extensions', '--disable-gpu']
)
```

3. **Clear old sessions:**
```bash
# Remove old token files
rm tokens/*.token
```

---

### Issue: High Memory Usage

**Solutions:**

1. **Use context manager:**
```python
with Create(session="mybot") as client:
    # Your code here
    pass
# Automatically cleans up
```

2. **Close properly:**
```python
try:
    client.start()
finally:
    client.close()
```

---

## Error Messages

### Error: `AttributeError: module 'aiohttp' has no attribute 'ClientSession'`

**Solution:**
```bash
# Upgrade aiohttp
uv pip install --upgrade aiohttp

# Or reinstall
uv pip uninstall aiohttp
uv pip install aiohttp
```

---

### Error: `TypeError: 'type' object is not subscriptable`

**Cause:** Using Python 3.8 with new type hints

**Solution:**
```bash
# Upgrade to Python 3.9+
# Or add this import at the top of your files
from __future__ import annotations
```

---

### Error: `PlaywrightTimeoutError`

**Solution:**
```python
# Increase timeout
client = Create(
    session="mybot",
    timeout=60000  # 60 seconds
)

# Or add browser launch timeout
client = Create(
    session="mybot",
    browser_args=['--timeout=60000']
)
```

---

### Error: `NetworkError: net::ERR_CONNECTION_CLOSED`

**Solutions:**

1. **Check internet connection**
2. **Restart browser:**
```python
client.close()
client = Create(session="mybot")
```

3. **Use proxy if needed:**
```python
client = Create(
    session="mybot",
    proxy="http://proxy:port"
)
```

---

## Debug Mode

### Enable Debug Logging

```python
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

client = Create(session="mybot")
```

---

### Get Detailed Error Info

```python
import traceback

try:
    client.sendText("123@c.us", "Hello")
except Exception as e:
    print(f"Error: {e}")
    print(f"Traceback: {traceback.format_exc()}")
```

---

## Getting Help

### Information to Include When Reporting Issues

```python
# 1. Version info
import WPP_Whatsapp
print(f"Version: {WPP_Whatsapp.__version__}")

# 2. Python version
import sys
print(f"Python: {sys.version}")

# 3. Platform
import platform
print(f"Platform: {platform.platform()}")

# 4. Error traceback
import traceback
traceback.print_exc()
```

---

### Resources

- **GitHub Issues:** https://github.com/3mora2/WPP_Whatsapp/issues
- **Discussions:** https://github.com/3mora2/WPP_Whatsapp/discussions
- **Documentation:** `/docs` folder

---

**Still having issues? Open a GitHub issue with detailed information!**
