"""Opt-in browser injection smoke test; authenticated checks use live_whatsapp_smoke.py."""
import asyncio
import os

import pytest
from playwright.async_api import async_playwright
from playwright.sync_api import sync_playwright

from WPP_Whatsapp.api.helpers.wa_version import getWaJs
from WPP_Whatsapp.api.helpers.wapi import WAPI


pytestmark = pytest.mark.skipif(
    os.getenv('RUN_WHATSAPP_BROWSER_TESTS') != '1' or os.getenv('CI') == 'true',
    reason='Opt-in real browser/network test: set RUN_WHATSAPP_BROWSER_TESTS=1',
)


async def on_load(page):
    await page.wait_for_function('() => window.Debug?.VERSION !== undefined')
    await page.add_script_tag(**(await getWaJs()))
    await page.wait_for_function('() => window.WPP?.isReady')
    await page.add_script_tag(content=WAPI)
    await page.wait_for_function('() => window.WAPI?._wppWhatsappReady === true')


async def main():
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(channel='chrome', headless=True)
        try:
            context = await browser.new_context(no_viewport=True, bypass_csp=True)
            page = await context.new_page()
            await page.goto('https://web.whatsapp.com', wait_until='domcontentloaded')
            await on_load(page)
            assert await page.evaluate('() => WPP.isReady && WAPI._wppWhatsappReady')
        finally:
            await browser.close()


def test_sync():
    # Download before starting sync Playwright's event loop.
    script = asyncio.run(getWaJs())
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel='chrome', headless=True)
        try:
            context = browser.new_context(no_viewport=True, bypass_csp=True)
            page = context.new_page()
            page.goto('https://web.whatsapp.com', wait_until='domcontentloaded')
            page.wait_for_function('() => window.Debug?.VERSION !== undefined')
            page.add_script_tag(**script)
            page.wait_for_function('() => window.WPP?.isReady')
            page.add_script_tag(content=WAPI)
            page.wait_for_function('() => window.WAPI?._wppWhatsappReady === true')
            assert page.evaluate('() => WPP.isReady && WAPI._wppWhatsappReady')
        finally:
            browser.close()


if __name__ == '__main__':
    test_sync()
