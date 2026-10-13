"""Backward-compatible sync facade over the native async browser runtime."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from typing import Literal

from WPP_Whatsapp.core.engine import AsyncBrowser, LoopRunner

SUPPORTED_BROWSERS = ("chromium", "firefox", "webkit")
BrowserName = Literal["chromium", "firefox", "webkit"]


class ThreadsafeBrowser(AsyncBrowser):
    def __init__(
        self,
        no_context=False,
        browser="chromium",
        stealthy=False,
        install=False,
        install_callback=None,
        check_open_dir=True,
        close_already_profile=False,
        **kwargs,
    ):
        if close_already_profile:
            raise ValueError("Profile takeover is unsupported; close its owner explicitly")
        self._runner = LoopRunner()
        self.loop = self._runner.loop

        async def initialize():
            AsyncBrowser.__init__(self)
            if install and not kwargs.get("channel") and not kwargs.get("executable_path"):
                from playwright.async_api import async_playwright

                async with async_playwright() as probe:
                    missing = not Path(getattr(probe, browser).executable_path).exists()
                if missing:
                    process = await asyncio.create_subprocess_exec(
                        sys.executable,
                        "-m",
                        "playwright",
                        "install",
                        browser,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.STDOUT,
                    )
                    output, _ = await process.communicate()
                    if install_callback:
                        install_callback(output.decode(errors="replace"))
                    if process.returncode:
                        raise RuntimeError("Playwright browser installation failed")
            await self.open(browser=browser, no_context=no_context, stealthy=stealthy, **kwargs)

        try:
            asyncio.run_coroutine_threadsafe(initialize(), self.loop).result(120)
        except BaseException:
            self._runner.stop()
            raise

    @property
    def is_same_loop(self):
        try:
            return asyncio.get_running_loop() is self.loop
        except RuntimeError:
            return False

    async def close(self):
        if self.loop.is_closed() or not self.loop.is_running():
            return
        await super().close()
        if self.is_same_loop:
            asyncio.current_task().add_done_callback(lambda _: self.loop.call_soon(self.loop.stop))
        else:
            self.stop()

    def sync_close(self, timeout_=60):
        if self.loop.is_closed() or not self.loop.is_running():
            return
        self.run_threadsafe(super().close(), timeout_=timeout_)
        self.stop()

    def stop(self):
        runner = getattr(self, "_runner", None)
        if runner is not None:
            runner.stop()

    def goto_sync(self, *args, **kwargs):
        return self.sync_goto(*args, **kwargs)

    def add_script_tag_sync(self, *args, timeout_=120, **kwargs):
        return self.run_threadsafe(self.add_script_tag(*args, **kwargs), timeout_=timeout_)

    def expose_function_sync(self, *args, timeout_=120, **kwargs):
        return self.run_threadsafe(self.expose_function(*args, **kwargs), timeout_=timeout_)

    def check_close_profile(self, directory):
        """Compatibility hook: profile ownership is checked when opening it."""
        return None
