from __future__ import annotations

import asyncio
import os
import threading
from functools import wraps

from WPP_Whatsapp.api.const import Logger
from WPP_Whatsapp.api.Whatsapp import Whatsapp
from WPP_Whatsapp.controllers.browser import SUPPORTED_BROWSERS, ThreadsafeBrowser
from WPP_Whatsapp.core.errors import SessionClosedError
from WPP_Whatsapp.core.options import validate_options
from WPP_Whatsapp.core.profiles import session_directory


def _serialize_session_start(method):
    """Share one startup per session while allowing different sessions to start."""

    @wraps(method)
    def start(self, session, *args, **kwargs):
        with self._sessions_lock:
            if self._closing or not self.loop.is_running():
                raise SessionClosedError("Multi-session browser is closed")
            lock = self._start_locks.setdefault(session, threading.Lock())
        with lock:
            return method(self, session, *args, **kwargs)

    return start


class MultiCreate:
    ThreadsafeBrowser: "ThreadsafeBrowser"

    def __init__(self, **kwargs):
        kwargs = validate_options(kwargs)
        self.logger = Logger
        self.defaultK = {
            "no_viewport": True,
            "bypass_csp": True,
            "headless": False,
            "browser": "chromium",
            "install": True,
        }
        self.defaultK.update(kwargs)
        if (
            self.defaultK.get("browser") == "chrome"
            or self.defaultK.get("browser") not in SUPPORTED_BROWSERS
        ):
            self.defaultK["browser"] = "chromium"
            self.defaultK["channel"] = "chrome"

        self.ThreadsafeBrowser = ThreadsafeBrowser(no_context=True, **self.defaultK)
        self.loop = self.ThreadsafeBrowser.loop
        self.Sessions: dict[str, dict] = {}
        self._sessions_lock = threading.RLock()
        self._start_locks = {}
        self._closing = False

    def close_all(self):
        if not self.loop.is_running():
            self.ThreadsafeBrowser.stop()
            return
        try:
            return self.ThreadsafeBrowser.run_threadsafe(self.close_all_)
        finally:
            self.ThreadsafeBrowser.stop()

    async def close_all_(self):
        if self._closing or not self.loop.is_running():
            return
        self._closing = True
        try:

            async def shutdown(session):
                try:
                    client = session.get("client")
                    if client:
                        client.isClosed = True
                        await self.ThreadsafeBrowser.create_task(client._shutdown_session())
                finally:
                    try:
                        context = session.get("context")
                        if context:
                            await self.ThreadsafeBrowser.create_task(context.close())
                    finally:
                        session["state"] = "CLOSED"

            outcomes = await asyncio.gather(
                *(shutdown(session) for session in list(self.Sessions.values())),
                return_exceptions=True,
            )
            for outcome in outcomes:
                if isinstance(outcome, BaseException):
                    raise outcome
        finally:
            try:
                await self.ThreadsafeBrowser.close()
            finally:
                self._closing = False

    @staticmethod
    def create_user_dir(folderNameToken, session):
        return session_directory(folderNameToken, session)

    def create_context(self, session):
        if session not in self.Sessions:
            return
        user_data_dir = self.Sessions[session].get("user_data_dir")
        self.ThreadsafeBrowser.check_close_profile(user_data_dir)
        options = dict(self.ThreadsafeBrowser._browser_persistent_option)
        options["user_data_dir"] = user_data_dir

        async def create():
            context = await self.ThreadsafeBrowser.open_context(**options)
            page = context.pages[0] if context.pages else await context.new_page()
            self.Sessions[session].update(
                browser=context.browser or context, context=context, page=page
            )
            context.on("close", lambda *_: self.Sessions[session].update(state="CLOSED"))

        self.ThreadsafeBrowser.run_threadsafe(create())

    @_serialize_session_start
    def start(
        self,
        session: str,
        user_data_dir="",
        folderNameToken="",
        catchQR=None,
        statusFind=None,
        onLoadingScreen=None,
        onStateChange=None,
        waitForLogin: bool = True,
        logQR: bool = False,
        autoClose: int = 0,
        version=None,
        wa_js_version=None,
        **kwargs,
    ):
        kwargs = validate_options(kwargs, autoClose=autoClose)
        if session in self.Sessions and self.Sessions[session].get("state") != "CLOSED":
            return self.Sessions[session]["client"]
        state = "STARTING"
        folderNameToken = folderNameToken or os.path.join(os.getcwd(), "tokens")
        if not user_data_dir:
            user_data_dir = self.create_user_dir(folderNameToken, session)
            if not user_data_dir:
                raise Exception("- Cant create user_data_dir", user_data_dir)

        self.Sessions[session] = dict(
            state=state,
            user_data_dir=user_data_dir,
            logQR=logQR,
            autoClose=autoClose,
            version=version,
            wa_js_version=wa_js_version,
        )

        async def build_client():
            client = Whatsapp(
                session,
                threadsafe_browser=self.ThreadsafeBrowser,
                page=self.Sessions[session]["page"],
                loop=self.ThreadsafeBrowser.loop,
                logQR=logQR,
                autoClose=autoClose,
                version=version,
                wa_js_version=wa_js_version,
                **kwargs,
            )
            client._owns_transport = False
            client.options.setdefault(
                "runtimeCacheDir", os.path.join(folderNameToken, ".runtime-cache")
            )
            for name, callback in [
                ("catchQR", catchQR),
                ("statusFind", statusFind),
                ("onLoadingScreen", onLoadingScreen),
            ]:
                if callable(callback):
                    setattr(client, name, callback)
            if callable(onStateChange):
                client.onStateChange(onStateChange)
            return client

        try:
            self.create_context(session)
            client = self.ThreadsafeBrowser.run_threadsafe(build_client())
            self.Sessions[session]["client"] = client
            self.ThreadsafeBrowser.run_threadsafe(client.start, timeout_=120)
            if waitForLogin:
                if not client.waitForLogin():
                    raise RuntimeError("Not Logged")
                self.Sessions[session]["state"] = "CONNECTED"
            return client
        except BaseException:
            context = self.Sessions[session].get("context")
            client = self.Sessions[session].get("client")
            if client:
                client.close()
            elif context:
                self.ThreadsafeBrowser.run_threadsafe(context.close())
            self.Sessions[session]["state"] = "CLOSED"
            raise
