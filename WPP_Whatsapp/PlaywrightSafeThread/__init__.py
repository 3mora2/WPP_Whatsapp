import asyncio
import typing
from PlaywrightSafeThread.browser.threadsafe_browser import ThreadsafeBrowser, BrowserName, SUPPORTED_BROWSERS
from playwright.async_api import Error


class ThreadsafeBrowser(ThreadsafeBrowser):
    def __init__(
            self,
            no_context=False,
            browser: BrowserName = "chromium",
            stealthy: bool = False,
            install: bool = False,
            check_open_dir=True,
            close_already_profile=True,
            **kwargs
    ) -> None:
        super().__init__(no_context=no_context,
                         browser=browser,
                         stealthy=stealthy,
                         install=install,
                         check_open_dir=check_open_dir,
                         close_already_profile=close_already_profile,
                         **kwargs)

    async def page_evaluate(self, expression: str, arg: typing.Optional[typing.Any] = None):
        return await self.page.evaluate(expression, arg)

    def sync_page_evaluate(self, expression: str, arg: typing.Optional[typing.Any] = None, timeout_=60):
        try:
            return self.run_threadsafe(self.page.evaluate, expression, arg, timeout_=timeout_)
        except Error as error:
            if "Execution context was destroyed, most likely because of a navigation" in error.message:
                pass
            elif "ReferenceError: WPP is not defined" in error.message:
                pass
            else:
                raise error

    async def page_wait_for_function(self, expression, arg=None, timeout: typing.Optional[float] = None,
                                     polling: typing.Optional[typing.Union[float, typing.Literal["raf"]]] = None):

        return await self.page.wait_for_function(expression, arg=arg, timeout=timeout, polling=polling)

    def sync_page_wait_for_function(self, expression, arg=None, timeout: typing.Optional[float] = None,
                                    polling: typing.Optional[typing.Union[float, typing.Literal["raf"]]] = None):

        return self.run_threadsafe(self.page.wait_for_function, expression, arg=arg, timeout=timeout, polling=polling)

    async def expose_function(self, *args, **kwargs):
        return await self.page.expose_function(*args, **kwargs)

    def sync_expose_function(self, *args, **kwargs):
        return self.run_threadsafe(self.page.expose_function, *args, **kwargs)

    async def add_script_tag(self, *args, **kwargs):
        return await self.page.add_script_tag(*args, **kwargs)

    def sync_add_script_tag(self, *args, **kwargs):
        return self.run_threadsafe(self.page.add_script_tag, *args, **kwargs)

    def sleep(self, val, *args, **kwargs):
        try:
            self.run_threadsafe(asyncio.sleep, val, *args, **kwargs, timeout_=val if val > 5 else 5)
        except:
            pass

    async def goto(self, *args, **kwargs):
        return await self.page.goto(*args, **kwargs)

    def sync_goto(self, *args, **kwargs):
        return self.run_threadsafe(self.page.goto, *args, **kwargs)

    def run_threadsafe(self, func, *args, timeout_=120, **kwargs):
        future = asyncio.run_coroutine_threadsafe(
            func(*args, **kwargs), self.loop
        )
        result = future.result(timeout=timeout_)
        return result
