import asyncio
from playwright.async_api import async_playwright
from playwright.sync_api import sync_playwright
import logging

logger = logging.getLogger(name="WPP_Whatsapp")
logger.setLevel(logging.DEBUG)

session = "test"
page = None


async def on_load(page):
    logger.debug(f'{session}: start inject')
    injected = await page.evaluate("""() => {
                        return (typeof window.WAPI !== 'undefined' &&typeof window.Store !== 'undefined');}"""
                                   )
    if injected:
        logger.info(f'{session}: already injected')
        return

    logger.info(f'{session}: injected state: {injected}')
    await page.evaluate("() => (window?.webpackChunkwhatsapp_web_client?.length || 0) > 3")
    await page.wait_for_function(
        "() => (window?.webpackChunkwhatsapp_web_client?.length || 0) > 3")

    await asyncio.sleep(1)
    await page.add_script_tag(
        url="https://github.com/wppconnect-team/wa-js/releases/download/nightly/wppconnect-wa.js")
    await page.wait_for_function("() => window.WPP?.isReady")
    await page.evaluate("""() => {
                          WPP.chat.defaultSendMessageOptions.createChat = true;
                          WPP.conn.setKeepAlive(true);
                        }""")
    logger.debug(f'{session}: End inject')


async def main():
    playwright = await async_playwright().start()
    browser_type = playwright.chromium
    browser = await browser_type.launch(
        **{
            "channel": "chrome",
            "headless": True
        })
    context = await browser.new_context(
        **{
            "no_viewport": True,
            "bypass_csp": True
        }
    )
    global page
    page = await context.new_page()
    # page.on('load', on_load)
    await page.goto('https://web.whatsapp.com', wait_until="domcontentloaded")
    await on_load(page)


# asyncio.run(main())
def test_sync():
    playwright = sync_playwright().start()
    browser_type = playwright.chromium
    browser = browser_type.launch(
        **{
            "channel": "chrome",
            "headless": True
        })
    context = browser.new_context(
        **{
            "no_viewport": True,
            "bypass_csp": True
        }
    )
    page = context.new_page()
    # page.on('load', on_load)
    page.goto('https://web.whatsapp.com', wait_until="domcontentloaded")
    print(f'{session}: start inject')
    injected = page.evaluate("""() => {
                        return (typeof window.WAPI !== 'undefined' &&typeof window.Store !== 'undefined');}"""
                             )
    if injected:
        logger.info(f'{session}: already injected')
    else:
        logger.info(f'{session}: injected state: {injected}')
        page.evaluate("() => (window?.webpackChunkwhatsapp_web_client?.length || 0) > 3")
        page.wait_for_function(
            "() => (window?.webpackChunkwhatsapp_web_client?.length || 0) > 3")

        page.add_script_tag(
            url="https://github.com/wppconnect-team/wa-js/releases/download/nightly/wppconnect-wa.js")
        page.wait_for_function("() => window.WPP?.isReady")
        page.evaluate("""() => {
                              WPP.chat.defaultSendMessageOptions.createChat = true;
                              WPP.conn.setKeepAlive(true);
                            }""")
        print(f'{session}: End inject')


test_sync()
