import asyncio
import traceback
from playwright.async_api import async_playwright

from Whatsapp.api.const import useragentOverride


class Browser:
    lastPercent = None
    lastPercentMessage = None
    session = None

    def __init__(self, session="", user_data_dir=""):
        self.session = session
        self.user_data_dir = user_data_dir
        # self.initBrowser()

    async def initBrowser(self):
        try:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch_persistent_context(
                self.user_data_dir,  channel="chrome",
                no_viewport=True,
                headless=False,
                # args=chromiumArgs,
                bypass_csp=True,
                user_agent=useragentOverride
            )

            self.page = self.browser.pages[0] if self.browser.pages else await self.browser.new_page()

            # stealth_sync(self.page)
            # self.initWhatsapp()
            # self.page.on('request', self.handel_page_request)
            return True

        except:
            traceback.print_exc()

    async def page_evaluate(self, expression, arg=None):
        try:
            return await self.page.evaluate(expression, arg)
        except:
            print(expression, arg)

    async def page_wait_for_function(self, expression, arg=None, timeout=None, polling=None):
        try:
            return await self.page.wait_for_function(expression, arg=arg, timeout=timeout, polling=polling)
        except:
            print(expression, arg)

# if __name__ == '__main__':
#     asyncio.run(Browser().initBrowser())