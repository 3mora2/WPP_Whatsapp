import asyncio
import os
import types
from typing import Optional
from WPP_Whatsapp.controllers.browser import SUPPORTED_BROWSERS
from WPP_Whatsapp.controllers.browser import ThreadsafeBrowser
from WPP_Whatsapp.api.Whatsapp import Whatsapp
from WPP_Whatsapp.api.const import Logger, useragentOverride


class Create:
    client: Optional[Whatsapp]
    ThreadsafeBrowser: "ThreadsafeBrowser"

    def __init__(
            self, session: str, user_data_dir='', folderNameToken="",
            catchQR=None,
            statusFind=None, onLoadingScreen=None,
            onStateChange=None, waitForLogin: bool = True, logQR: bool = False,
            autoClose: int = 0, version=None, wa_js_version=None, *args, **kwargs) -> None:
        """
        check_open_dir:bool
        close_already_profile:bool
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
        self.version = version
        self.wa_js_version = wa_js_version
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

        self.catchQR = catchQR if type(catchQR) in [types.FunctionType, types.MethodType] else self.catchQR
        self.statusFind = statusFind if type(statusFind) in [types.FunctionType, types.MethodType] else self.statusFind
        self.onLoadingScreen = onLoadingScreen if type(
            onLoadingScreen) in [types.FunctionType, types.MethodType] else self.onLoadingScreen
        self.onStateChange = onStateChange if type(onStateChange) in [types.FunctionType, types.MethodType] else None
        self.logger = Logger
        self.waitForLogin = waitForLogin
        self.logQR = logQR
        self.autoClose = autoClose
        self.__kwargs = kwargs

    def __exit__(self, *args):
        self.sync_close()

    async def close(self):
        if hasattr(self, "ThreadsafeBrowser"):
            await self.ThreadsafeBrowser.close()
        self._onStateChange("CLOSED")

    def sync_close(self):
        if hasattr(self, "ThreadsafeBrowser"):
            self.ThreadsafeBrowser.sync_close()
        self._onStateChange("CLOSED")

    def _onStateChange(self, state):
        self.state = state
        if hasattr(self, "ThreadsafeBrowser") and not self.client.page.is_closed():
            # TODO::
            connected = self.ThreadsafeBrowser.page_evaluate_sync("() => WPP.conn.isRegistered()", page=self.client.page)
            if not connected:
                self.ThreadsafeBrowser.sleep(2)
                if not self.waitLoginPromise:
                    try:
                        self.waitLoginPromise = self.client.waitForLogin
                    except:
                        Logger.exception("waitForLogin")
                    finally:
                        self.waitLoginPromise = None
                if self.waitLoginPromise:
                    self.waitLoginPromise()

        if state == "CONNECTED":
            Logger.info("Ready ....")

        elif state in ["browserClose", 'serverClose']:
            self.state = "CLOSED"
            self.client = None
            Logger.info("client.close - session.state: " + self.state)

        if self.onStateChange:
            self.onStateChange(state)

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
            self.create_sync()
        elif self.state in ["CONFLICT", "UNPAIRED", "UNLAUNCHED"]:
            Logger.info("client.useHere()")
            self.client.useHere()
        else:
            Logger.info(self.get_state())

        return self.client

    async def start_(self) -> "Whatsapp":
        if not self.state or self.state in ["CLOSED"]:
            await self.create()
        elif self.state in ["CONFLICT", "UNPAIRED", "UNLAUNCHED"]:
            Logger.info("client.useHere()")
            self.client.useHere()
        else:
            Logger.info(self.get_state())

        return self.client

    def create_sync(self) -> Whatsapp:
        self.state = "STARTING"
        default = {
            "no_viewport": True, "bypass_csp": True, "headless": False,
            "browser": "chromium", "install": True, "user_agent": useragentOverride
        }
        default.update(self.__kwargs)
        self.__kwargs = default
        # for key in default:
        #     if key not in self.__kwargs:
        #         self.__kwargs[key] = default[key]

        # Use Default channel as chrome
        if self.__kwargs.get("browser") == "chrome" or self.__kwargs.get("browser") not in SUPPORTED_BROWSERS:
            self.__kwargs["browser"] = "chromium"
            self.__kwargs["channel"] = "chrome"

        self.ThreadsafeBrowser = ThreadsafeBrowser(user_data_dir=self.user_data_dir, **self.__kwargs)

        self.ThreadsafeBrowser.page.on("close", self.close)
        self.ThreadsafeBrowser.page.on("crash", self.close)
        self.ThreadsafeBrowser.browser.on("disconnected", lambda: self.statusFind('browserClose', self.session))

        self.client = Whatsapp(self.session,
                               threadsafe_browser=self.ThreadsafeBrowser, page=self.ThreadsafeBrowser.page,
                               loop=self.loop, logQR=self.logQR,
                               autoClose=self.autoClose, version=self.version, wa_js_version=self.wa_js_version)

        self.client.catchQR = self.catchQR
        self.client.statusFind = self.statusFind
        self.client.onLoadingScreen = self.onLoadingScreen
        self.ThreadsafeBrowser.run_threadsafe(self.client.start, timeout_=120)
        self.client.onStateChange(self._onStateChange)
        if self.waitForLogin:
            is_logged = self.client.waitForLogin()
            if not is_logged:
                raise Exception('Not Logged')
            self.state = "CONNECTED"
        self.setup()

        return self.client

    async def create(self) -> Whatsapp:
        self.state = "STARTING"
        default = {
            "no_viewport": True, "bypass_csp": True, "headless": False,
            "browser": "chromium", "install": True,
        }

        for key in default:
            if key not in self.__kwargs:
                self.__kwargs[key] = default[key]

        # Use Default channel as chrome
        if self.__kwargs.get("browser") == "chrome" or self.__kwargs.get("browser") not in SUPPORTED_BROWSERS:
            self.__kwargs["browser"] = "chromium"
            self.__kwargs["channel"] = "chrome"

        self.ThreadsafeBrowser = ThreadsafeBrowser(user_data_dir=self.user_data_dir, **self.__kwargs)

        self.ThreadsafeBrowser.page.on("close", self.close)
        self.ThreadsafeBrowser.page.on("crash", self.close)
        self.ThreadsafeBrowser.browser.on("disconnected", lambda: self.statusFind('browserClose', self.session))

        self.client = Whatsapp(self.session,
                               threadsafe_browser=self.ThreadsafeBrowser, page=self.ThreadsafeBrowser.page,
                               loop=self.ThreadsafeBrowser.loop, logQR=self.logQR,
                               autoClose=self.autoClose, version=self.version, wa_js_version=self.wa_js_version)
        self.client.catchQR = self.catchQR
        self.client.statusFind = self.statusFind
        self.client.onLoadingScreen = self.onLoadingScreen
        await self.client.start()
        # self.ThreadsafeBrowser.run_threadsafe(self.client.start, timeout_=120)
        self.client.onStateChange(self._onStateChange)
        if self.waitForLogin:
            is_logged = await self.client.waitForLogin_()
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
        Logger.info("onLoadingScreen", percent, message)

    def setup(self):
        pass
