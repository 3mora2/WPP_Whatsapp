import asyncio
import inspect
import os
from typing import Optional

from WPP_Whatsapp.api.const import Logger
from WPP_Whatsapp.api.Whatsapp import Whatsapp
from WPP_Whatsapp.controllers.browser import SUPPORTED_BROWSERS, ThreadsafeBrowser
from WPP_Whatsapp.core.lifecycle import SessionState
from WPP_Whatsapp.core.options import validate_options
from WPP_Whatsapp.core.profiles import session_directory


class Create:
    client: Optional[Whatsapp]
    ThreadsafeBrowser: "ThreadsafeBrowser"

    def __init__(
        self,
        session: str,
        user_data_dir="",
        folderNameToken="",
        catchQR=None,
        statusFind=None,
        onLoadingScreen=None,
        catchLinkCode=None,
        onStateChange=None,
        waitForLogin: bool = True,
        logQR: bool = False,
        autoClose: int = 0,
        version=None,
        wa_js_version=None,
        **kwargs,
    ) -> None:
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
        kwargs = validate_options(kwargs, autoClose=autoClose)
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
        self.folderNameToken = folderNameToken or os.path.join(os.getcwd(), "tokens")
        if not self.user_data_dir:
            self.user_data_dir = self.create_user_dir()
            if not self.user_data_dir:
                raise Exception("- Cant create user_data_dir", user_data_dir)

        self.loop = kwargs.get("loop")

        self.catchQR = catchQR if callable(catchQR) else self.catchQR
        self.statusFind = statusFind if callable(statusFind) else self.statusFind
        self.onLoadingScreen = (
            onLoadingScreen if callable(onLoadingScreen) else self.onLoadingScreen
        )

        self.catchLinkCode = catchLinkCode

        self.onStateChange = onStateChange if callable(onStateChange) else None
        self.logger = Logger
        self.waitForLogin = waitForLogin
        self.logQR = logQR
        self.autoClose = autoClose
        self.__kwargs = kwargs

    def __enter__(self):
        return self.start()

    def __exit__(self, *args):
        self.sync_close()

    async def __aenter__(self):
        return await self.start_()

    async def __aexit__(self, *args):
        await self.close()

    async def close(self):
        if self.waitLoginPromise:
            self.waitLoginPromise.cancel()
        if self.client:
            await self.client.close_async()
        elif hasattr(self, "ThreadsafeBrowser"):
            await self.ThreadsafeBrowser.close()
        callback = self._onStateChange("CLOSED")
        if inspect.isawaitable(callback):
            await callback

    def sync_close(self):
        if self.waitLoginPromise:
            self.waitLoginPromise.cancel()
        if self.client:
            self.client.close()
        elif hasattr(self, "ThreadsafeBrowser"):
            self.ThreadsafeBrowser.sync_close()

        callback = self._onStateChange("CLOSED")
        if inspect.isawaitable(callback):
            try:
                current = asyncio.get_running_loop()
            except RuntimeError:
                asyncio.run(callback)
            else:
                current.create_task(callback)

    def _onStateChange(self, state):
        self.state = state
        client = self.client
        browser = getattr(self, "ThreadsafeBrowser", None)
        if (
            state not in ("CLOSED", "browserClose", "serverClose")
            and client is not None
            and not client.page.is_closed()
            and browser is not None
            and browser.loop.is_running()
            and not self.waitLoginPromise
        ):

            async def check_connection():
                if not await browser.page_evaluate(
                    "() => WPP.conn.isRegistered()", page=client.page
                ):
                    client.lifecycle.transition(SessionState.RECONNECTING)
                    await client.waitForLogin_()

            self.waitLoginPromise = asyncio.run_coroutine_threadsafe(
                check_connection(), browser.loop
            )

            def finished(future):
                self.waitLoginPromise = None
                if not future.cancelled() and future.exception():
                    Logger.error(
                        "Session reconnection failed (%s)", type(future.exception()).__name__
                    )

            self.waitLoginPromise.add_done_callback(finished)

        if state == "CONNECTED":
            Logger.info("Ready ....")

        elif state in ["browserClose", "serverClose"]:
            self.state = "CLOSED"
            self.client = None
            Logger.info("client.close - session.state: " + self.state)

        if self.onStateChange:
            return self.onStateChange(state)

    def create_user_dir(self, new=False):
        return session_directory(self.folderNameToken, self.session)

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
            await self.client.useHere_()
        else:
            Logger.info(self.get_state())

        return self.client

    def create_sync(self) -> Whatsapp:
        try:
            self.__create()
            self.ThreadsafeBrowser.run_threadsafe(self.client.start, timeout_=120)
            if self.waitForLogin:
                if not self.client.waitForLogin():
                    raise RuntimeError("Not Logged")
                self.state = "CONNECTED"
            self.setup()
            return self.client
        except BaseException:
            self.sync_close()
            raise

    async def create(self) -> Whatsapp:
        creation = asyncio.create_task(asyncio.to_thread(self.__create))
        try:
            await asyncio.shield(creation)
            await self.ThreadsafeBrowser.create_task(self.client.start())
            if self.waitForLogin:
                if not await self.ThreadsafeBrowser.create_task(self.client.waitForLogin_()):
                    raise RuntimeError("Not Logged")
                self.state = "CONNECTED"
            self.setup()
            return self.client
        except BaseException:
            # A Python worker cannot be cancelled while it is launching a
            # browser. Wait for ownership to be recorded before cleaning it up.
            try:
                await asyncio.shield(creation)
            except Exception:
                pass
            await self.close()
            raise

    def __create(self):
        options = self.__kwargs.copy()
        options.setdefault("runtimeCacheDir", os.path.join(self.folderNameToken, ".runtime-cache"))
        self.state = "STARTING"
        default = {
            "no_viewport": True,
            "bypass_csp": True,
            "headless": False,
            "browser": "chrome",
            "channel": "chrome",
            "install": False,
        }

        default.update(self.__kwargs)

        # Use Default channel as chrome
        if default.get("browser") == "chrome" or default.get("browser") not in SUPPORTED_BROWSERS:
            default["browser"] = "chromium"
            default["channel"] = "chrome"

        self.ThreadsafeBrowser = ThreadsafeBrowser(user_data_dir=self.user_data_dir, **default)
        self.loop = self.ThreadsafeBrowser.loop

        async def build_client():
            self.ThreadsafeBrowser.page.on("close", self.close)
            self.ThreadsafeBrowser.page.on("crash", self.close)
            self.ThreadsafeBrowser.browser.on(
                "disconnected", lambda: self.statusFind("browserClose", self.session)
            )
            client = Whatsapp(
                self.session,
                threadsafe_browser=self.ThreadsafeBrowser,
                page=self.ThreadsafeBrowser.page,
                loop=self.ThreadsafeBrowser.loop,
                logQR=self.logQR,
                autoClose=self.autoClose,
                version=self.version,
                wa_js_version=self.wa_js_version,
                **options,
            )
            client.catchQR = self.catchQR
            client.statusFind = self.statusFind
            client.onLoadingScreen = self.onLoadingScreen
            client.catchLinkCode = self.catchLinkCode
            client.onStateChange(self._onStateChange)
            return client

        self.client = self.ThreadsafeBrowser.run_threadsafe(build_client())

    def get_state(self) -> dict:
        return {
            "session_name": self.session,
            "state": self.state,
            "status": self.statusFind_dict.get("status"),
        }

    def getQrcode(self) -> dict:
        if self.state in ["UNPAIRED_IDLE"]:
            # need restart session
            return {"result": "error", **self.get_state()}
        elif self.state in ["CLOSED", None]:
            return {"result": "error", **self.get_state()}
        else:
            if self.statusFind_dict.get("status") != "isLogged":
                return {"result": "success", **self.get_state(), "qrcode": self.catchQR_dict}
            else:
                return {"result": "success", **self.get_state()}

    def catchQR(self, *args, **kwargs):
        self.catchQR_dict = kwargs
        self.state = "QRCODE"
        # print(self.state)

    def statusFind(self, status, session):
        self.statusFind_dict = {"status": status, "session": session}
        # print(session, status)

    def onLoadingScreen(self, percent, message):
        Logger.info("Loading screen: %s (%s%%)", message, percent)

    def setup(self):
        pass
