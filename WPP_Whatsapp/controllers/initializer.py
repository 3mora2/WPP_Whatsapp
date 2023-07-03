import asyncio
import os
import types
from time import sleep
from typing import Optional
from WPP_Whatsapp.PlaywrightSafeThread import ThreadsafeBrowser

from WPP_Whatsapp.api.Whatsapp import Whatsapp
from WPP_Whatsapp.api.const import Logger


class Create:
    client: Optional[Whatsapp]
    ThreadsafeBrowser: "ThreadsafeBrowser"

    def __init__(
            self, session: str, user_data_dir='', folderNameToken="",
            catchQR: types.FunctionType = None,
            statusFind: types.FunctionType = None, onLoadingScreen: types.FunctionType = None,
            onStateChange: types.FunctionType = None, waitForLogin: bool = True, logQR: bool = False,
            autoClose: int = 0, *args, **kwargs) -> None:
        """
        class Create:
            custom class to open browser and start whatsapp
            you can custom your class, you need only:
                ThreadsafeBrowser = ThreadsafeBrowser(browser="chromium")
                client = Whatsapp(session="test", ThreadsafeBrowser)
                client.start()
                client.waitForLogin()
        """
        self.browserSessionToken = None
        self.waitLoginPromise = None
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

        self.catchQR = catchQR if type(catchQR) == types.FunctionType else self.catchQR
        self.statusFind = statusFind if type(statusFind) == types.FunctionType else self.statusFind
        self.onLoadingScreen = onLoadingScreen if type(
            onLoadingScreen) == types.FunctionType else self.onLoadingScreen
        self.onStateChange = onStateChange if type(onStateChange) == types.FunctionType else None
        self.logger = Logger
        self.waitForLogin = waitForLogin
        self.logQR = logQR
        self.autoClose = autoClose
        self.__kwargs = kwargs

    def __exit__(self, *args):
        self.sync_close()

    async def close(self):
        await self.ThreadsafeBrowser.close()
        self.state = "CLOSED"

    def sync_close(self):
        self.ThreadsafeBrowser.sync_close()
        self.state = "CLOSED"

    def _onStateChange(self, state):
        if type(self.onStateChange) == types.FunctionType:
            self.onStateChange(state)
        self.state = state
        connected = self.ThreadsafeBrowser.page_evaluate("() => WPP.conn.isRegistered()")
        if not connected:
            sleep(2)
            if not self.waitLoginPromise:
                try:
                    self.waitLoginPromise = self.client.waitForLogin
                finally:
                    self.waitLoginPromise = None
            self.waitLoginPromise()

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

    def start(self) -> "Whatsapp":
        if not self.state or self.state in ["CLOSED"]:
            self.create()

        elif self.state in ["CONFLICT", "UNPAIRED", "UNLAUNCHED"]:
            print("client.useHere()")
            self.client.useHere()
        else:
            print(self.get_state())

        return self.client

    def create(self) -> Whatsapp:
        self.state = "STARTING"
        default = {"channel": "chrome", "no_viewport": True, "bypass_csp": True, "headless": False}
        for key in default:
            if key not in self.__kwargs:
                self.__kwargs[key] = default[key]

        self.ThreadsafeBrowser = ThreadsafeBrowser(
            browser="chromium", install=False, user_data_dir=self.user_data_dir, **self.__kwargs)

        self.ThreadsafeBrowser.page.on("close", self.close)
        self.ThreadsafeBrowser.page.on("crash", self.close)
        self.ThreadsafeBrowser.browser.on("disconnected", lambda: self.statusFind('browserClose', self.session))

        self.client = Whatsapp(self.session, self.ThreadsafeBrowser, logQR=self.logQR,
                               autoClose=self.autoClose)
        self.client.catchQR = self.catchQR
        self.client.statusFind = self.statusFind
        self.client.onLoadingScreen = self.onLoadingScreen
        self.client.start()

        if self.waitForLogin:
            is_logged = self.client.waitForLogin()
            if not is_logged:
                raise Exception('Not Logged')
            self.state = "CONNECTED"
        self.setup()

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

    def setup(self):
        self.client.onStateChange(self._onStateChange)
