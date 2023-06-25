import asyncio
import os
import traceback
from typing import Optional

import psutil as psutil

from Whatsapp.api.Whatsapp import Whatsapp
from Whatsapp.api.const import defaultOptions
from Whatsapp.controllers.browser import Browser


class Create:
    client: Optional[Whatsapp]

    def __init__(self, *args, **kwargs):
        self.browserSessionToken = None
        self.waitLoginPromise = None
        self.browser = None
        self.client = None
        self.state = None
        self.statusFind_dict = {}
        self.catchQR_dict = {}
        # self.session = session
        # self.loop = kwargs.get("loop") or asyncio.new_event_loop()
        # asyncio.set_event_loop(self.loop)
        # g = self.loop.run_until_complete(self.create(session, "-"))
        # self.loop.run_forever()

    async def close(self):
        if self.client:
            await self.client.close()
            self.state = "CLOSED"

    async def _onStateChange(self, state):
        self.state = state
        connected = await self.client.page_evaluate("() => WPP.conn.isRegistered()")
        if not connected:
            await asyncio.sleep(2)
            if not self.waitLoginPromise:
                try:
                    self.waitLoginPromise = self.client.waitForLogin()
                finally:
                    self.waitLoginPromise = None
            await self.waitLoginPromise

        if state == "CONNECTED":
            print("Ready ....")

        elif state in ["browserClose", 'serverClose']:
            self.state = "CLOSED"
            self.client = None
            print("client.close - session.state: " + self.state)

    @staticmethod
    def create_user_dir(tokens, session, new=False):
        user_dir = os.path.join(tokens, session)
        if os.path.exists(user_dir):
            return user_dir

        if not os.path.exists(user_dir):
            os.makedirs(user_dir)
            return user_dir

        # user_dir_temp = user_dir
        # for i in itertools.count(1):
        #     if not os.path.exists(user_dir_temp):
        #         return user_dir_temp
        #     user_dir_temp = f'{user_dir}-{i}'

    @staticmethod
    def check_profile(path):
        try:
            path_old = set()
            for proc in psutil.process_iter():
                if "chrome.exe" in proc.name():
                    cmd = proc.cmdline()
                    user = list(filter(lambda x: "--user-data-dir" in x, cmd))
                    if user:
                        path_old.add(os.path.normpath(user[0].split("=")[-1]))
                elif "firefox.exe" in proc.name():
                    cmd = proc.cmdline()
                    user = list(filter(lambda x: "-profile" in x, cmd))
                    if user:
                        path_old.add(os.path.normpath(cmd[cmd.index(user[0]) + 1]))

            if os.path.normpath(path) in path_old:
                # print(f"- {path} is opened")
                return True
        except:
            traceback.print_exc()

    async def start(self, session, user_data_dir=''):
        self.session = session
        if not self.state or self.state in ["CLOSED"]:
            await self.create(session, user_data_dir)

        elif self.state in ["CONFLICT", "UNPAIRED", "UNLAUNCHED"]:
            print("client.useHere()")
            await self.client.useHere()

        else:
            print(self.get_state())

        return self.client

    async def create(self, session, user_data_dir=''):
        self.state = "STARTING"
        mergedOptions = defaultOptions
        # user_data_dir = r"C:\Users\ammar\Whatsapp Pro\Profile-2-2022-09-21-20-21-23"
        tokens = mergedOptions.get("folderNameToken")
        if not user_data_dir:
            user_data_dir = self.create_user_dir(tokens, session)
            if not user_data_dir:
                print("- Cant create user_data_dir", user_data_dir)
                return

        if self.check_profile(user_data_dir):
            print("- Current user_data_dir Is Opened", user_data_dir)
            return

        try:
            self.browser = Browser(session, user_data_dir)
            if not await self.browser.initBrowser():
                raise Exception()
            # await asyncio.sleep(1)
            self.browser.browser.on("disconnected", lambda: self.statusFind('browserClose', session))

        except:
            traceback.print_exc()
            print("cant start browser")
            return

        try:
            # loop = asyncio.get_event_loop()
            self.client = Whatsapp(session, self.browser)  # , loop=self.loop)
            self.client.catchQR = self.catchQR
            self.client.statusFind = self.statusFind
            self.client.onLoadingScreen = self.onLoadingScreen

            if not await self.client.start():
                raise Exception("cat start client")
            if mergedOptions.get("waitForLogin"):
                is_logged = await self.client.waitForLogin()
                if not is_logged:
                    Exception('Not Logged')

            self.state = "CONNECTED"
            await self.setup()
            return self.client
        except:
            traceback.print_exc()
            print("cant start client")
            return

    def get_state(self):
        return {
            "session_name": self.session,
            "state": self.state,
            "status": self.statusFind_dict.get("status")
        }

    def getQrcode(self):
        if self.state in ["UNPAIRED_IDLE"]:
            # need restart session
            return {"result": "error", **self.get_state()}
        elif self.state in ["CLOSED", None]:
            return {"result": "error", **self.get_state()}
        else:
            if self.statusFind_dict.get("status") != 'isLogged':
                return {"result": "success", **self.get_state(), "qrcode": self.catchQR_dict}
            else:
                return {"result": "success", **self.get_state()}

    def catchQR(self, *args, **kwargs):
        self.catchQR_dict = kwargs
        self.state = "QRCODE"
        print(self.state)

    def statusFind(self, status, session):
        self.statusFind_dict = {
            "status": status,
            "session": session
        }
        print(session, status)

    def onLoadingScreen(self, percent, message):
        print("onLoadingScreen", percent, message)

    async def setup(self):
        self.client.onStateChange(self._onStateChange)
        # self.client.onAnyMessage(self.on_any_message)

    def on_any_message(self, message):
        print("int", message)
