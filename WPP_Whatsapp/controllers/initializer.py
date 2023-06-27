import asyncio
import os
import traceback
import types
from time import sleep
from typing import Optional

import psutil as psutil

from WPP_Whatsapp.api.Whatsapp import Whatsapp
from WPP_Whatsapp.api.const import Logger
from WPP_Whatsapp.controllers.browser import Browser


class Create:
    client: Optional[Whatsapp]

    def __init__(
            self, session: str, user_data_dir='', folderNameToken="", headless=False,
            catchQR: types.FunctionType = None,
            statusFind: types.FunctionType = None, onLoadingScreen: types.FunctionType = None,
            onStateChange: types.FunctionType = None, waitForLogin: bool = True, logQR: bool = False,
            autoClose: int = 0, *args, **kwargs) -> None:
        """

        @type session: object
        """
        self.browserSessionToken = None
        self.waitLoginPromise = None
        self.Browser = None
        self.client = None
        self.state = "CLOSED"
        self.statusFind_dict = {}
        self.catchQR_dict = {}
        self.session = session
        self.user_data_dir = user_data_dir
        self.folderNameToken = (
                folderNameToken or
                # defaultOptions.get("folderNameToken") or
                os.path.join(os.getcwd(), "tokens")
        )
        if not self.user_data_dir:
            self.user_data_dir = self.create_user_dir()
            if not self.user_data_dir:
                raise Exception("- Cant create user_data_dir", user_data_dir)

        self.loop = kwargs.get("loop") or asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        self.__catchQR = catchQR if type(catchQR) == types.FunctionType else self.catchQR
        self.__statusFind = statusFind if type(statusFind) == types.FunctionType else self.statusFind
        self.__onLoadingScreen = onLoadingScreen if type(
            onLoadingScreen) == types.FunctionType else self.onLoadingScreen
        self.__onStateChange = onStateChange if type(onStateChange) == types.FunctionType else None
        self.logger = Logger
        self.waitForLogin = waitForLogin
        self.logQR = logQR
        self.autoClose = autoClose
        self.headless = headless
        self.__kwargs = kwargs

    def async_to_sync(self, future):
        result = self.loop.run_until_complete(future)
        return result

    async def close(self):
        if self.client:
            await self.client.close()
            self.state = "CLOSED"

    async def _onStateChange(self, state):
        if type(self.__onStateChange) == types.FunctionType:
            self.__onStateChange(state)
        self.state = state
        connected = await self.client.page_evaluate("() => WPP.conn.isRegistered()")
        if not connected:
            sleep(2)
            if not self.waitLoginPromise:
                try:
                    self.waitLoginPromise = self.client.waitForLogin
                finally:
                    self.waitLoginPromise = None
            await self.waitLoginPromise()

        if state == "CONNECTED":
            print("Ready ....")

        elif state in ["browserClose", 'serverClose']:
            self.state = "CLOSED"
            self.client = None
            print("client.close - session.state: " + self.state)

    def create_user_dir(self, new=False):
        user_dir = os.path.join(self.folderNameToken, self.session)
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

    async def start(self) -> Whatsapp:
        if not self.state or self.state in ["CLOSED"]:
            await self.create()

        elif self.state in ["CONFLICT", "UNPAIRED", "UNLAUNCHED"]:
            print("client.useHere()")
            await self.client.useHere()
        else:
            print(self.get_state())

        return self.client

    async def create(self) -> Whatsapp:
        self.state = "STARTING"
        # mergedOptions = defaultOptions
        # user_data_dir = r"C:\Users\ammar\Whatsapp Pro\Profile-2-2022-09-21-20-21-23"

        if self.check_profile(self.user_data_dir):
            raise Exception("- Current user_data_dir Is Opened", self.user_data_dir)

        self.Browser = Browser(self.session, self.user_data_dir, headless=self.headless, loop=self.loop)
        await self.Browser.initBrowser()
        self.Browser.browser.on("disconnected", lambda: self.statusFind('browserClose', self.session))

        self.client = Whatsapp(self.session, self.Browser, loop=self.loop, logQR=self.logQR, autoClose=self.autoClose)
        self.client.catchQR = self.__catchQR
        self.client.statusFind = self.__statusFind
        self.client.onLoadingScreen = self.__onLoadingScreen

        if not await self.client.start():
            raise Exception("cat start client")

        if self.waitForLogin:
            is_logged = await self.client.waitForLogin()
            if not is_logged:
                raise Exception('Not Logged')
            self.state = "CONNECTED"
        await self.setup()

        return self.client

    def get_state(self) -> dict:
        return {
            "session_name": self.session,
            "state": self.state,
            "status": self.statusFind_dict.get("status")
        }

    def getQrcode(self) -> dict:
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
        # print(self.state)

    def statusFind(self, status, session):
        self.statusFind_dict = {
            "status": status,
            "session": session
        }
        # print(session, status)

    def onLoadingScreen(self, percent, message):
        print("onLoadingScreen", percent, message)

    async def setup(self):
        self.client.onStateChange(self._onStateChange)
        # self.client.onAnyMessage(self.on_any_message)

    def on_any_message(self, message):
        print("int", message)
