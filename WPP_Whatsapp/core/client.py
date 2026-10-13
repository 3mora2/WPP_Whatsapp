from __future__ import annotations

import asyncio
from pathlib import Path

from .diagnostics import classify_failure, snapshot
from .engine import AsyncBrowser
from .errors import SessionNotReadyError
from .lifecycle import SessionState
from .models import TypedServices
from .options import validate_options
from .profiles import session_directory
from .service_registry import service_definitions


class AsyncClient:
    """Native asyncio client with composed services; no background browser thread."""

    def __init__(
        self,
        session="default",
        *,
        user_data_dir=None,
        token_directory="tokens",
        wait_for_login=True,
        wa_js_version=None,
        **options,
    ):
        self.session = session
        self.user_data_dir = user_data_dir
        self.token_directory = token_directory
        self.wait_for_login = wait_for_login
        self.wa_js_version = wa_js_version
        self.options = validate_options(options)
        self._context = None
        self.browser = None
        self._lock = None
        self._loop = None
        self._state = SessionState.NEW
        self._failure = None

    def _session_lock(self):
        loop = asyncio.get_running_loop()
        if self._loop is not None and self._loop is not loop:
            raise RuntimeError("AsyncClient must be used on its owning event loop")
        if self._lock is None:
            self._loop, self._lock = loop, asyncio.Lock()
        return self._lock

    async def connect(self):
        async with self._session_lock():
            return await self._connect()

    async def _connect(self):
        if self._context is not None:
            if self._context.isClosed:
                await self._close()
            else:
                return self
        from WPP_Whatsapp.api.Whatsapp import Whatsapp

        directory = self.user_data_dir or session_directory(self.token_directory, self.session)
        self.browser = AsyncBrowser()
        self._state = SessionState.STARTING
        self._failure = None
        phase = "browser_start"
        browser_name = self.options.get("browser", "chromium")
        options = {
            "headless": False,
            "channel": "chrome" if browser_name in ("chromium", "chrome") else None,
            "no_viewport": True,
            "bypass_csp": True,
            **self.options,
        }
        if browser_name == "chrome":
            options["browser"] = "chromium"
        try:
            await self.browser.open(user_data_dir=directory, **options)
            phase = "runtime_start"
            self._context = Whatsapp(
                self.session,
                self.browser,
                self.browser.page,
                wa_js_version=self.wa_js_version,
                **self.options,
            )
            self._context.options.setdefault(
                "runtimeCacheDir", str(Path(directory).parent / ".runtime-cache")
            )
            self._context.onStateChange(self._connection_changed)
            await self._context.start()
            if self.wait_for_login:
                phase = "login"
                if not await self._context.waitForLogin_():
                    raise SessionNotReadyError("Login or device synchronization did not complete")
                await self.browser.page_wait_for_function(
                    "() => window.onMessage?.exposed", page=self._context.page
                )
                self._context.lifecycle.transition(SessionState.READY)
            return self
        except BaseException as error:
            self._failure = classify_failure(phase, error)
            await self._close()
            self._state = SessionState.FAILED
            raise

    async def reconnect(self):
        """Reopen this session's profile. Never replays previous operations."""
        async with self._session_lock():
            await self._close()
            return await self._connect()

    async def _connection_changed(self, state):
        context = self._context
        if context is None or context.isClosed:
            return
        if state == "CONNECTED":
            if await context.isAuthenticated() and await context.isInsideChat():
                context.lifecycle.transition(SessionState.READY)
        elif state in ("UNPAIRED", "UNPAIRED_IDLE"):
            context.lifecycle.transition(SessionState.WAITING_QR)
        elif state in ("OPENING", "TIMEOUT", "CONFLICT", "DISCONNECTED"):
            context.lifecycle.transition(SessionState.RECONNECTING)

    @property
    def services(self):
        if self._context is None:
            raise SessionNotReadyError("Connect the client first")
        return self._context.async_services

    @property
    def typed(self) -> TypedServices:
        return self.services.typed

    def diagnostics(self) -> dict:
        """Return a sanitized support snapshot without opening a browser."""
        return snapshot(self.state, self._context, self._failure)

    def __getattr__(self, name):
        if not name.startswith("_") and (
            name == "events" or any(definition.name == name for definition in service_definitions())
        ):
            return getattr(self.services, name)
        raise AttributeError(name)

    def __dir__(self):
        return sorted(
            set(super().__dir__())
            | {"events"}
            | {definition.name for definition in service_definitions()}
        )

    @property
    def state(self):
        return self._context.lifecycle.state if self._context is not None else self._state

    async def close(self):
        async with self._session_lock():
            await self._close()

    async def _close(self):
        context, browser = self._context, self.browser
        try:
            if context is not None:
                context.isClosed = True
                await context._shutdown_session()
        finally:
            try:
                if browser is not None:
                    await browser.close()
            finally:
                self._context = self.browser = None
                self._state = SessionState.CLOSED

    async def __aenter__(self):
        return await self.connect()

    async def __aexit__(self, *args):
        await self.close()
