import asyncio

from playwright.async_api import async_playwright, Playwright, BrowserContext, Page

from WPP_Whatsapp.api.const import useragentOverride


class Browser:
    session: str
    playwright: "Playwright"
    browser: "BrowserContext"
    page: "Page"

    def __init__(self, user_data_dir: str = "", headless: bool = False, *args, **kwargs):
        self.user_data_dir = user_data_dir
        self.loop = kwargs.get("loop")
        if not self.loop:
            raise Exception("Not Add Loop")
        asyncio.set_event_loop(self.loop)
        self.headless = headless

    async def initBrowser(self):
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch_persistent_context(
            self.user_data_dir, channel="chrome",
            no_viewport=True,
            headless=self.headless,
            # args=chromiumArgs,
            bypass_csp=True,
            user_agent=useragentOverride
        )

        self.page = self.browser.pages[0] if self.browser.pages else await self.browser.new_page()

    async def page_evaluate(self, expression, arg=None):
        return await self.page.evaluate(expression, arg)

    async def page_wait_for_function(self, expression, arg=None, timeout=None, polling=None):
        return await self.page.wait_for_function(expression, arg=arg, timeout=timeout, polling=polling)

# if __name__ == '__main__':
#     asyncio.run(Browser().initBrowser())
