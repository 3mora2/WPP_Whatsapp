from WPP_Whatsapp import Whatsapp
from WPP_Whatsapp.PlaywrightSafeThread import ThreadsafeBrowser

session = "test"

# Start Browser
default = {"channel": "chrome", "no_viewport": True, "bypass_csp": True, "headless": False}
ThreadsafeBrowser = ThreadsafeBrowser(browser="chromium", install=False, **default)

# Start Whatsapp
client = Whatsapp(session, ThreadsafeBrowser)
client.start()

# wait for scan qrcode and login
is_logged = client.waitForLogin()
if not is_logged:
    raise Exception('Not Logged')

# send message
message = "hello from wpp"
phone_number = "201016708170"  # or "+201016708170"
result = client.sendText(phone_number, message)
print(result)

# close Browser
ThreadsafeBrowser.sync_close()
