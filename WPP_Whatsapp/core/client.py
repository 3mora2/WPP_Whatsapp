from __future__ import annotations

import asyncio
from pathlib import Path
from typing import TYPE_CHECKING, Optional, cast

if TYPE_CHECKING:
    from .service_types import (
        AsyncCatalog,
        AsyncChats,
        AsyncCommunities,
        AsyncGroups,
        AsyncLabels,
        AsyncLists,
        AsyncMessages,
        AsyncNewsletters,
        AsyncProfile,
        AsyncServices,
        AsyncStatus,
    )

from .contracts import OperationContext
from .diagnostics import classify_failure, snapshot
from .engine import AsyncBrowser
from .errors import SessionNotReadyError
from .lifecycle import SessionState
from .models import TypedServices
from .options import validate_options
from .profiles import session_directory
from .recovery import RecoverySupervisor
from .service_registry import service_definitions
from .subscriptions import ClientEvents


class AsyncClient:
    """Native asyncio client with composed services; no background browser thread."""

    if TYPE_CHECKING:
        catalog: AsyncCatalog
        chats: AsyncChats
        communities: AsyncCommunities
        groups: AsyncGroups
        labels: AsyncLabels
        lists: AsyncLists
        newsletters: AsyncNewsletters
        profile: AsyncProfile
        status: AsyncStatus

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
        self._context: Optional[OperationContext] = None
        self.browser = None
        self._lock = None
        self._loop = None
        self._state = SessionState.NEW
        self._failure = None
        self._closing = False
        self.events = ClientEvents(session)
        self._recovery = RecoverySupervisor(self)

    def _session_lock(self):
        loop = asyncio.get_running_loop()
        if self._loop is not None and self._loop is not loop:
            raise RuntimeError("AsyncClient must be used on its owning event loop")
        if self._lock is None:
            self._loop, self._lock = loop, asyncio.Lock()
        return self._lock

    async def connect(self):
        self._recovery.blocked = False
        async with self._session_lock():
            return await self._connect()

    async def _connect(self, *, wait_for_login=None):
        if self._context is not None:
            if self._context.isClosed:
                await self._close()
            else:
                return self
        from WPP_Whatsapp.api.Whatsapp import Whatsapp

        directory = self.user_data_dir or session_directory(self.token_directory, self.session)
        self._closing = False
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
            self._context = cast(
                "OperationContext",
                Whatsapp(
                    self.session,
                    self.browser,
                    self.browser.page,
                    wa_js_version=self.wa_js_version,
                    **self.options,
                ),
            )
            self._context.options.setdefault(
                "runtimeCacheDir", str(Path(directory).parent / ".runtime-cache")
            )
            self._context.onStateChange(self._connection_changed)
            await self._context.start()
            self.events.bind(self._context.async_services.events)
            context = self._context

            async def handle_browser_lost():
                if self._context is context and not self._closing:
                    if context.isClosed:
                        # The legacy page-close handler can run before ours.
                        self._recovery.schedule()
                    else:
                        await self._connection_changed("DISCONNECTED")

            def browser_lost(*args):
                if self._context is context and not self._closing:
                    task = asyncio.create_task(handle_browser_lost())
                    task.add_done_callback(
                        lambda done: None if done.cancelled() else done.exception()
                    )

            assert self.browser.page is not None
            self.browser.page.on("crash", browser_lost)
            self.browser.page.on("close", browser_lost)
            should_wait = self.wait_for_login if wait_for_login is None else wait_for_login
            if should_wait:
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
        await self._recovery.stop()
        self._recovery.blocked = False
        async with self._session_lock():
            await self._close()
            return await self._connect()

    async def _recover_once(self):
        async with self._session_lock():
            if self._recovery.blocked:
                raise SessionNotReadyError("Login is required")
            await self._close()
            await self._connect(wait_for_login=False)
            while self.state != SessionState.READY:
                if self._recovery.blocked or self.state == SessionState.WAITING_QR:
                    self._recovery.blocked = True
                    raise SessionNotReadyError("Login is required")
                await asyncio.sleep(0.1)

    async def _connection_changed(self, state):
        context = self._context
        if context is None or context.isClosed:
            return
        if state == "CONNECTED":
            if await context.isAuthenticated() and await context.isInsideChat():
                self._recovery.blocked = False
                self._failure = None
                context.lifecycle.transition(SessionState.READY)
        elif state in ("UNPAIRED", "UNPAIRED_IDLE"):
            self._recovery.blocked = True
            context.lifecycle.transition(SessionState.WAITING_QR)
        elif state in ("OPENING", "TIMEOUT", "CONFLICT", "DISCONNECTED"):
            context.lifecycle.transition(SessionState.RECONNECTING)
            self._recovery.schedule()

    @property
    def services(self) -> AsyncServices:
        if self._context is None:
            raise SessionNotReadyError("Connect the client first")
        return cast("AsyncServices", self._context.async_services)

    @property
    def typed(self) -> TypedServices:
        return self.services.typed

    @property
    def messages(self) -> AsyncMessages:
        return self.services.messages

    def diagnostics(self) -> dict:
        """Return a sanitized support snapshot without opening a browser."""
        return {
            **snapshot(self.state, self._context, self._failure),
            "recovery": dict(self._recovery.stats),
        }

    async def metrics(self, *, include_processes=True) -> dict:
        """Numeric operational metrics; measures only this client's owned Chrome tree."""
        from .metrics import process_snapshot

        bridge = getattr(self._context, "bridge", None)
        result = self.diagnostics()
        result["commands"] = {
            name: dict(values) for name, values in getattr(bridge, "command_metrics", {}).items()
        }
        if include_processes:
            roots = dict(getattr(self.browser, "process_roots", {}))
            result["process"] = await asyncio.to_thread(process_snapshot, roots)
        return result

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
        self._recovery.blocked = True
        await self._recovery.stop()
        async with self._session_lock():
            await self._close()

    async def _close(self):
        self._closing = True
        self.events.detach()
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
