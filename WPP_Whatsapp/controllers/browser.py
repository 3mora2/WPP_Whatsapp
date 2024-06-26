import asyncio

import playwright
from PlaywrightSafeThread.browser.threadsafe_browser import ThreadsafeBrowser as Tb, BrowserName, SUPPORTED_BROWSERS, \
    Logger
from playwright.async_api import Error


class ThreadsafeBrowser(Tb):
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

    def page_evaluate_sync(self, *args, timeout_=60, **kwargs, ):
        try:
            return super().page_evaluate_sync(*args, timeout_=60, **kwargs, )
        except Error as error:
            if "Execution context was destroyed, most likely because of a navigation" in error.message:
                pass
            # elif "ReferenceError: WPP is not defined" in error.message:
            #     pass
            else:
                raise error

    async def expose_function(self, *args, **kwargs, ):
        # TODO:
        return await super().expose_function(*args, **kwargs, )

    def sleep(self, val, timeout_=None):
        # TODO:: Change Loop
        try:
            super().sleep(val, timeout_=timeout_)
        except:
            pass

    def run_threadsafe(self, func, *args, timeout_=120, **kwargs):
        if not asyncio.iscoroutine(func):
            func = func(*args, **kwargs)
        return super().run_threadsafe(func, timeout_=timeout_)

    async def wait_for_first_selectors(self, *selectors, timeout=0):
        async def wa(selector):
            try:
                await self.page.wait_for_selector(selector, timeout=timeout)
                return selector
            except :
                return

        tasks = [self.loop.create_task(wa(selector)) for selector in selectors]
        while True:
            task_done = next(filter(lambda task: task.done(), tasks), None)
            pending = list(filter(lambda task: not task.done(), tasks))
            if not task_done:
                await asyncio.sleep(.5)
                continue

            for p in pending:
                self.loop.call_soon_threadsafe(p.cancel)

            return task_done.result()
