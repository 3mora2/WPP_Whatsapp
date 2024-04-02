import asyncio
import os
import types
from typing import Optional
from WPP_Whatsapp.controllers.browser import SUPPORTED_BROWSERS
from WPP_Whatsapp.controllers.browser import ThreadsafeBrowser
from WPP_Whatsapp.api.Whatsapp import Whatsapp
from WPP_Whatsapp.api.const import Logger, useragentOverride


class MultiCreate:
    ThreadsafeBrowser: "ThreadsafeBrowser"

    def __init__(self, **kwargs):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.logger = Logger
        self.defaultK = {
            "no_viewport": True, "bypass_csp": True, "headless": False,
            "browser": "chromium", "install": True, "user_agent": useragentOverride
        }
        self.defaultK.update(kwargs)
        if self.defaultK.get("browser") == "chrome" or self.defaultK.get("browser") not in SUPPORTED_BROWSERS:
            self.defaultK["browser"] = "chromium"
            self.defaultK["channel"] = "chrome"

        self.ThreadsafeBrowser = ThreadsafeBrowser(no_context=True, **self.defaultK)
        self.ThreadsafeBrowser.page.on("close", self.close_all)
        self.ThreadsafeBrowser.page.on("crash", self.close_all)
        self.ThreadsafeBrowser.browser.on("disconnected", lambda: print('browserClose'))
        self.Sessions: dict[str, dict] = {}

    def close_all(self):
        pass

    @staticmethod
    def create_user_dir(folderNameToken, session):
        user_dir = os.path.join(folderNameToken, session)
        if os.path.exists(user_dir):
            return user_dir

        if not os.path.exists(user_dir):
            os.makedirs(user_dir)
            return user_dir

    def create_context(self, session):
        if session not in self.Sessions:
            return
        user_data_dir = self.Sessions[session].get("user_data_dir")
        self.ThreadsafeBrowser.check_close_profile(user_data_dir)
        context = self.ThreadsafeBrowser.run_threadsafe(
            self.ThreadsafeBrowser.browser_type.launch_persistent_context(
                **self.ThreadsafeBrowser._browser_persistent_option, user_data_dir=user_data_dir))
        browser = context.browser or context
        page = context.pages[0] if context.pages else self.ThreadsafeBrowser.run_threadsafe(context.new_page())
        self.Sessions[session].update({"browser": browser, "context": context, "page": page})

    def start(self, session: str, user_data_dir='', folderNameToken="",
              catchQR=None,
              statusFind=None, onLoadingScreen=None,
              onStateChange=None, waitForLogin: bool = True, logQR: bool = False,
              autoClose: int = 0, version=None, wa_js_version=None, **kwargs):

        state = "CLOSED"
        user_data_dir = user_data_dir
        folderNameToken = (
                folderNameToken or os.path.join(os.getcwd(), "tokens")
        )
        if not user_data_dir:
            user_data_dir = self.create_user_dir(folderNameToken, session)
            if not user_data_dir:
                raise Exception("- Cant create user_data_dir", user_data_dir)

        self.Sessions[session] = dict(
            state=state, user_data_dir=user_data_dir,
            logQR=logQR, autoClose=autoClose, version=version, wa_js_version=wa_js_version
        )
        self.create_context(session)

        client = Whatsapp(
            session, threadsafe_browser=self.ThreadsafeBrowser, page=self.Sessions[session]["page"],
            loop=self.loop, logQR=logQR, autoClose=autoClose, version=version, wa_js_version=wa_js_version)

        client.catchQR = catchQR
        client.statusFind = statusFind
        client.onLoadingScreen = onLoadingScreen
        self.Sessions[session]["client"] = client
        self.ThreadsafeBrowser.run_threadsafe(client.start, timeout_=120)
        if waitForLogin:
            is_logged = client.waitForLogin()
            if not is_logged:
                raise Exception('Not Logged')
            self.Sessions[session]["state"] = "CONNECTED"
        return client
