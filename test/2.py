import asyncio
import os
from pathlib import Path

from WPP_Whatsapp import Whatsapp
from WPP_Whatsapp import ThreadsafeBrowser
from WPP_Whatsapp.api.helpers.wa_version import getWaJs
# from WPP_Whatsapp.js_lib.wapi import WAPI
async def main():

    # Start Browser
    default = {"channel": "chrome", "no_viewport": True, "bypass_csp": True, "headless": False}

    ThreadsafeBrowser_ = ThreadsafeBrowser(browser="chromium", install=False, **default)
    await ThreadsafeBrowser_.goto("https://web.whatsapp.com/")
    data = await getWaJs()
    print(data)
    await ThreadsafeBrowser_.add_script_tag(**data)

    await ThreadsafeBrowser_.page_wait_for_function("() => window.WAPI.getWAVersion()")
asyncio.run(main())
