from __future__ import annotations

import asyncio
import inspect
import threading
from concurrent.futures import TimeoutError as FutureTimeout

from playwright.async_api import Error as PlaywrightError
from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from playwright.async_api import async_playwright

from .errors import SessionClosedError, SessionTimeoutError
from .lifecycle import Deadline
from .profiles import ProfileLease


class AsyncBrowser:
    """Native Playwright runtime. Every operation executes on its owning loop."""

    def __init__(self):
        self.loop = asyncio.get_running_loop()
        self.page = self.context = self.browser = self.playwright = self.browser_type = None
        self.contexts = []
        self.leases = {}
        self._close_task = None

    async def open(self, browser="chromium", no_context=False, **options):
        if browser not in ("chromium", "firefox", "webkit"):
            raise ValueError("Unsupported browser")
        self._stealth = None
        if options.get("stealthy"):
            try:
                from playwright_stealth import Stealth
            except ImportError:
                raise ImportError("stealthy=True requires WPP_Whatsapp[stealth]") from None
            self._stealth = Stealth()
        self.playwright = await async_playwright().start()
        self.browser_type = getattr(self.playwright, browser)
        allowed = inspect.signature(self.browser_type.launch_persistent_context).parameters
        self._browser_persistent_option = {k: v for k, v in options.items() if k in allowed}
        try:
            if not no_context:
                if options.get("user_data_dir"):
                    self.context = await self.open_context(**self._browser_persistent_option)
                    self.browser = self.context.browser
                else:
                    launch_keys = inspect.signature(self.browser_type.launch).parameters
                    self.browser = await self.browser_type.launch(
                        **{k: v for k, v in options.items() if k in launch_keys}
                    )
                    context_keys = inspect.signature(self.browser.new_context).parameters
                    self.context = await self.browser.new_context(
                        **{k: v for k, v in options.items() if k in context_keys}
                    )
                    self.contexts.append(self.context)
                    if self._stealth:
                        await self._stealth.apply_stealth_async(self.context)
                self.page = (
                    self.context.pages[0] if self.context.pages else await self.context.new_page()
                )
            return self
        except BaseException:
            await self.close()
            raise

    async def open_context(self, user_data_dir, **options):
        lease = ProfileLease(user_data_dir).acquire()
        context = None
        try:
            context = await self.browser_type.launch_persistent_context(user_data_dir, **options)
            if self._stealth:
                await self._stealth.apply_stealth_async(context)
        except BaseException:
            try:
                if context is not None:
                    await context.close()
            finally:
                lease.release()
            raise
        self.contexts.append(context)
        self.leases[context] = lease

        def released(*_):
            self.leases.pop(context, lease).release()
            if context in self.contexts:
                self.contexts.remove(context)

        context.on("close", released)
        return context

    async def create_task(self, task, *args, **kwargs):
        if not inspect.isawaitable(task):
            task = task(*args, **kwargs)
        if asyncio.get_running_loop() is self.loop:
            return await task
        if not self.loop.is_running():
            if inspect.iscoroutine(task):
                task.close()
            raise SessionClosedError("Browser loop is closed")
        return await asyncio.shield(
            asyncio.wrap_future(asyncio.run_coroutine_threadsafe(task, self.loop))
        )

    def run_threadsafe(self, task, *args, timeout_=120, **kwargs):
        if not inspect.isawaitable(task):
            task = task(*args, **kwargs)
        try:
            running = asyncio.get_running_loop()
        except RuntimeError:
            running = None
        if running is self.loop:
            if inspect.iscoroutine(task):
                task.close()
            raise RuntimeError("Use the async API on the browser event loop")
        if not self.loop.is_running():
            if inspect.iscoroutine(task):
                task.close()
            raise SessionClosedError("Browser loop is closed")
        future = asyncio.run_coroutine_threadsafe(task, self.loop)
        try:
            return future.result(timeout=timeout_ or None)
        except FutureTimeout:
            # A Playwright call may already have executed. Do not cancel/replay it.
            raise SessionTimeoutError("Browser operation exceeded its deadline") from None

    async def _page_call(self, method, *args, page=None, **kwargs):
        target = page if page is not None else self.page
        if target is None or target.is_closed():
            raise SessionClosedError("Session page is closed")
        return await self.create_task(getattr(target, method)(*args, **kwargs))

    async def page_evaluate(self, *args, page=None, **kwargs):
        return await self._page_call("evaluate", *args, page=page, **kwargs)

    async def goto(self, *args, page=None, **kwargs):
        return await self._page_call("goto", *args, page=page, **kwargs)

    async def add_script_tag(self, *args, page=None, **kwargs):
        return await self._page_call("add_script_tag", *args, page=page, **kwargs)

    async def expose_function(self, *args, page=None, **kwargs):
        return await self._page_call("expose_function", *args, page=page, **kwargs)

    async def page_wait_for_function(self, *args, page=None, **kwargs):
        return await self._page_call("wait_for_function", *args, page=page, **kwargs)

    async def page_wait_for_selector(self, *args, page=None, **kwargs):
        return await self._page_call("wait_for_selector", *args, page=page, **kwargs)

    async def wait_for_first_selectors(self, *selectors, timeout=0, page=None):
        """Wait for any visible selector; legacy timeout is in seconds (0 disables it)."""
        Deadline(timeout)  # Validate the legacy timeout before scheduling browser work.
        if not selectors:
            raise ValueError("At least one selector is required")
        target = page if page is not None else self.page

        async def wait_any():
            tasks = {
                asyncio.create_task(
                    self.page_wait_for_selector(selector, timeout=timeout * 1000, page=target)
                ): selector
                for selector in selectors
            }
            pending = set(tasks)
            try:
                while pending:
                    done, pending = await asyncio.wait(pending, return_when=asyncio.FIRST_COMPLETED)
                    for task in done:
                        try:
                            if task.result() is not None:
                                return tasks[task]
                        except PlaywrightTimeoutError:
                            continue
                        except (SessionClosedError, PlaywrightError):
                            if target is None or target.is_closed():
                                return None
                            raise
                return None
            finally:
                for task in pending:
                    task.cancel()
                await asyncio.gather(*tasks, return_exceptions=True)

        return await self.create_task(wait_any())

    async def _close(self):
        try:
            outcomes = await asyncio.gather(
                *(context.close() for context in list(self.contexts)), return_exceptions=True
            )
            if self.browser is not None and self.context is None:
                await self.browser.close()
            for outcome in outcomes:
                if isinstance(outcome, Exception):
                    raise outcome
        finally:
            try:
                if self.playwright:
                    await self.playwright.stop()
            finally:
                for lease in self.leases.values():
                    lease.release()
                self.leases.clear()
                self.contexts.clear()

    async def _close_owned(self):
        if self._close_task is None:
            self._close_task = self.loop.create_task(self._close())
        return await asyncio.shield(self._close_task)

    async def close(self):
        return await self.create_task(self._close_owned())

    def sync_close(self, timeout_=60):
        return self.run_threadsafe(self.close(), timeout_=timeout_)

    def page_evaluate_sync(self, *args, page=None, timeout_=120, **kwargs):
        return self.run_threadsafe(
            self.page_evaluate(*args, page=page, **kwargs), timeout_=timeout_
        )

    def page_wait_for_function_sync(self, *args, page=None, timeout_=120, **kwargs):
        return self.run_threadsafe(
            self.page_wait_for_function(*args, page=page, **kwargs), timeout_=timeout_
        )

    def sync_goto(self, *args, page=None, timeout_=120, **kwargs):
        return self.run_threadsafe(self.goto(*args, page=page, **kwargs), timeout_=timeout_)

    def sleep(self, seconds, timeout_=None):
        return self.run_threadsafe(asyncio.sleep(seconds), timeout_=timeout_)


class LoopRunner:
    """The sync facade's single dedicated loop, with deterministic teardown."""

    def __init__(self):
        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self._run, name="WPP-browser", daemon=True)
        self.thread.start()

    def _run(self):
        asyncio.set_event_loop(self.loop)
        try:
            self.loop.run_forever()
        finally:
            tasks = asyncio.all_tasks(self.loop)
            for task in tasks:
                task.cancel()
            self.loop.run_until_complete(asyncio.gather(*tasks, return_exceptions=True))
            self.loop.run_until_complete(self.loop.shutdown_asyncgens())
            self.loop.run_until_complete(self.loop.shutdown_default_executor())
            self.loop.close()

    def stop(self):
        from .events import CALLBACK_THREAD

        if not self.loop.is_closed():
            self.loop.call_soon_threadsafe(self.loop.stop)
        # The loop shuts down its executor after callbacks return. Joining it
        # from one of those callbacks would make each wait for the other.
        if (
            threading.current_thread() is not self.thread
            and getattr(CALLBACK_THREAD, "owner", None) is not self.loop
        ):
            self.thread.join(10)
