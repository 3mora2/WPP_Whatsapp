import asyncio
from PlaywrightSafeThread.browser.threadsafe_browser import (ThreadsafeBrowser as Tb, BrowserName,
                                                             SUPPORTED_BROWSERS)
from playwright._impl._errors import TargetClosedError
from playwright.async_api import Error, TimeoutError

from WPP_Whatsapp.api.const import Logger


def a_check_page(method):
    async def wrapper(self, *args, **kwargs):
        if "page" not in kwargs or not kwargs["page"]:
            kwargs["page"] = self.page
        if kwargs["page"].is_closed():
            raise TargetClosedError()
        return await method(self, *args, **kwargs)
    return wrapper


def check_page(method):
    def wrapper(self, *args, **kwargs):
        if "page" not in kwargs or not kwargs["page"]:
            kwargs["page"] = self.page
        if kwargs["page"].is_closed():
            raise TargetClosedError()
        return method(self, *args, **kwargs)

    return wrapper


class ThreadsafeBrowser(Tb):
    def __init__(
            self,
            no_context=False,
            browser: BrowserName = "chromium",
            stealthy: bool = False,
            install: bool = False,
            install_callback=lambda x: print(x.strip() if x else x),
            check_open_dir=True,
            close_already_profile=True,
            **kwargs
    ) -> None:
        super().__init__(no_context=no_context,
                         browser=browser,
                         stealthy=stealthy,
                         install=install,
                         install_callback=install_callback,
                         check_open_dir=check_open_dir,
                         close_already_profile=close_already_profile,
                         **kwargs)

    def sleep(self, val, timeout_=None):
        # TODO:: Change Loop
        try:
            super().sleep(val, timeout_=timeout_)
        except:
            Logger.exception("sleep")

    # def run_threadsafe(self, func, *args, timeout_=120, **kwargs):
    #     if not asyncio.iscoroutine(func):
    #         func = func(*args, **kwargs)
    #     return super().run_threadsafe(func, timeout_=timeout_)

    # async def wait_for_first_selectors_(self, *selectors, timeout=0):
    #     async def wa(selector):
    #         try:
    #             await self.page.wait_for_selector(selector, timeout=timeout)
    #             return selector
    #         except:
    #             return
    #
    #     tasks = [self.create_task(wa(selector)) for selector in selectors]
    #
    #     while True:
    #         print("while True")
    #         task_done = next(filter(lambda task: task.done(), tasks), None)
    #         pending = list(filter(lambda task: not task.done(), tasks))
    #         if not task_done:
    #             await asyncio.sleep(.5)
    #             continue
    #         print("while True task")
    #
    #         for p in pending:
    #             self.loop.call_soon_threadsafe(p.cancel, "finish")
    #         print("return")
    #         return task_done.result()

    async def wait_for_first_selectors(self, *selectors, timeout=0):
        timeout_local = 0

        while True:
            if timeout != 0 and timeout_local >= timeout:
                break
            for selector in selectors:
                try:
                    task = await self.page_wait_for_selector(selector, timeout=1 * 1000)
                    timeout_local += 1
                    if task:
                        return selector
                except (RuntimeError, TargetClosedError):
                    return
                except TimeoutError:
                    ...
                except Exception as e:
                    Logger.exception("wait_for_first_selectors")

                await asyncio.sleep(.5)
                timeout_local += .5

    # def run_playwright(self, *args: str):
    #     env = self.get_driver_env()
    #     driver_executable, driver_cli = compute_driver_executable()
    #
    #     with subprocess.Popen([driver_executable, driver_cli, *args], env=env, stdout=subprocess.PIPE,
    #                           stderr=subprocess.STDOUT, **creation_flags_dict()) as process:
    #         for line in process.stdout:
    #             print(line.decode('utf-8'), end="\r")

    def sync_close(self, timeout_=60):
        try:
            self.run_threadsafe(self.__stop_playwright(), timeout_=timeout_)
        except Exception as e:
            print(e)
        self.stop()

    async def close(self):
        try:
            await self.create_task(self.__stop_playwright())
        except Exception as e:
            print(e)
        self.stop()

    def stop(self):
        try:
            super().stop()
        except:
            ...

    #####################
    @a_check_page
    async def goto(self, url, *args, page=None, **kwargs):
        return await super().goto(url, *args, page=page, **kwargs)

    @a_check_page
    async def add_script_tag(self, *args, page=None, **kwargs):
        return await super().add_script_tag(*args, page=page, **kwargs)

    @a_check_page
    async def expose_function(self, *args, page=None, **kwargs):
        return await super().expose_function(*args, page=page, **kwargs)

    @a_check_page
    async def page_wait_for_function(self, *args, page=None, **kwargs):
        return await super().page_wait_for_function(*args, page=page, **kwargs)

    @a_check_page
    async def page_wait_for_selector(self, *args, page=None, **kwargs):
        return await self.create_task(page.wait_for_selector(*args, **kwargs))

    @a_check_page
    async def page_evaluate(self, *args, page=None, **kwargs):
        return await super().page_evaluate(*args, page=page, **kwargs)

    ####################################################################################################################
    @check_page
    def goto_sync(self, url, *args, page=None, timeout_=60, **kwargs):
        return super().goto_sync(url, *args, page=page, timeout_=timeout_, **kwargs)

    @check_page
    def add_script_tag_sync(self, *args, page=None, timeout_=60, **kwargs):
        return super().add_script_tag_sync(*args, page=page, timeout_=timeout_, **kwargs)

    @check_page
    def expose_function_sync(self, *args, page=None, timeout_=60, **kwargs):
        return super().expose_function_sync(*args, page=page, timeout_=timeout_, **kwargs)

    @check_page
    def page_wait_for_function_sync(self, *args, page=None, timeout_=60, **kwargs):
        return super().page_wait_for_function_sync(*args, page=page, timeout_=timeout_, **kwargs)

    @check_page
    def page_evaluate_sync(self, *args, page=None, timeout_=60, **kwargs, ):
        try:
            return super().page_evaluate_sync(*args, page=page, timeout_=60, **kwargs, )
        except Error as error:
            if "Execution context was destroyed, most likely because of a navigation" in error.message:
                pass
            # elif "ReferenceError: WPP is not defined" in error.message:
            #     pass
            else:
                raise error
