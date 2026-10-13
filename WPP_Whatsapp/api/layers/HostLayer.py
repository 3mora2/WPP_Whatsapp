import asyncio
import base64 as base64_model
import logging
import mimetypes
import re
from datetime import datetime
from threading import Event
import time
import math
from typing import Callable

from playwright._impl._errors import TargetClosedError
from playwright.async_api import Page

from WPP_Whatsapp.api.const import whatsappUrl, Logger
from WPP_Whatsapp.api.helpers.function import asciiQr
from WPP_Whatsapp.api.helpers.jsFunction import setInterval
from WPP_Whatsapp.api.helpers.wa_version import getPageContent, getWaJs
from WPP_Whatsapp.api.helpers.wapi import WAPI
from WPP_Whatsapp.controllers.browser import ThreadsafeBrowser
from WPP_Whatsapp.core.bridge import JavascriptBridge
from WPP_Whatsapp.core.lifecycle import Deadline, SessionLifecycle, SessionState
from WPP_Whatsapp.core.errors import SessionTimeoutError, RuntimeCompatibilityError
from playwright.async_api import Error as BrowserError


class HostLayer:
    page: Page
    session: str
    logger: logging
    ThreadsafeBrowser: "ThreadsafeBrowser"
    options: dict
    autoCloseInterval: Event
    autoCloseCalled: bool
    isInitialized: bool
    isInjected: bool
    isStarted: bool
    isClosed: bool
    isLogged: bool
    isInChat: bool
    urlCode: str
    status: str
    attempt: int
    lastPercent: str
    lastPercentMessage: str
    session: str
    autoClose: int
    checkStartInterval: Event
    logQR: bool
    remain: int
    version: str
    wa_js_version: str
    loop: object
    catchLinkCode: Callable[[str], None] = None

    def __init__(self):
        self.lifecycle = SessionLifecycle()
        self.bridge = JavascriptBridge(self.ThreadsafeBrowser, self.page)
        self.isInChat = False
        self.isLogged = False
        self.isClosed = False
        self.__initialize()

    def _get_bridge(self):
        bridge = getattr(self, 'bridge', None)
        if bridge is None:
            bridge = self.bridge = JavascriptBridge(self.ThreadsafeBrowser, self.page)
        return bridge

    async def _evaluate_js(self, command, arg=None, page=None):
        if page is not None and page is not self.page:
            raise ValueError('Bridge page does not belong to this session')
        return await self._get_bridge().call(command, arg)

    def _evaluate_js_sync(self, command, arg=None, page=None, timeout_=120):
        if page is not None and page is not self.page:
            raise ValueError('Bridge page does not belong to this session')
        return self._get_bridge().call_sync(command, arg, timeout_=timeout_)

    def catchQR(self, **kwargs):
        # self.catchQR_dict = kwargs
        pass

    def statusFind(self, status, session):
        self.status = status

    def onLoadingScreen(self, percent, message):
        pass

    def __initialize(self):
        self.page.on('close', self.on_close)
        self.page.on('load', self.on_load)
        self.isInitialized = True

    async def on_close(self, _=None):
        self.isClosed = True
        lifecycle = getattr(self, 'lifecycle', None)
        if lifecycle is not None:
            lifecycle.transition(SessionState.CLOSED)
        self.logger.info(f'{self.session}: Page Closed')
        self.cancelAutoClose()
        shutdown = getattr(self, '_shutdown_session', None)
        if shutdown:
            await shutdown()

    async def on_load(self, _=None):
        if self.isClosed or getattr(self, '_runtime_reloading', False) or getattr(self, '_initializing', False):
            return
        self._initializing = True
        try:
            self.logger.info(f'{self.session}: Page loaded')
            await self._afterPageLoad()
        except (RuntimeError, TargetClosedError):
            # mean stop app
            self.logger.info(f'{self.session}: Stop App, Auto Close')
            self.isClosed = True
            await self.tryAutoClose()
        except Exception as error:
            self._initialization_error = error
            if not self.isClosed:
                self.lifecycle.transition(SessionState.FAILED)
            self.logger.error('Session initialization failed (%s)', type(error).__name__)
        finally:
            self._initializing = False

    async def _afterPageLoad(self):
        if self.lifecycle.state == SessionState.READY:
            self.lifecycle.transition(SessionState.RECONNECTING)
            self.isInChat = False
        self.logger.info(f'{self.session}: Injecting wapi.js')
        options = self._runtime_config = {
            "deviceName": self.options.get("deviceName"),
            "disableGoogleAnalytics": self.options.get("disableGoogleAnalytics"),
            "googleAnalyticsId": self.options.get("googleAnalyticsId"),
            "linkPreviewApiServers": self.options.get("linkPreviewApiServers"),
            "poweredBy": self.options.get("poweredBy"),
        }
        self.logger.info(f'{self.session}: Start WPPConfig')
        await self._evaluate_js('HostLayer._afterPageLoad.0', options,
                                                   page=self.page)
        # await self.page.page_evaluate("""(options) => {window.WPPConfig = options;}""", options)
        self.logger.info(f'{self.session}: WPPConfig')
        self.isInjected = False
        # TODO:

        if await self.inject_api():
            self.isInjected = True
            self.logger.info(f'{self.session}: wapi.js injected')
            await self.afterPageScriptInjected()
        else:
            self.logger.info(f'{self.session}: wapi.js failed')

    async def _afterPageScriptInjectedHost(self):
        version = await self.getWAVersion()
        self.logger.info(f'{self.session}: WhatsApp WEB version: {version}')
        version = await self.getWAJSVersion()
        self.logger.info(f'{self.session}: WA-JS version: {version}')
        try:
            await self._evaluate_js('HostLayer._afterPageScriptInjectedHost.0',
                                                       page=self.page)
            await self._evaluate_js('HostLayer._afterPageScriptInjectedHost.1',
                                                       page=self.page)
        except:
            Logger.exception("window.checkQrCode")
        self.logger.info(f'{self.session}: Wait isMainReady')
        await self.ThreadsafeBrowser.page_wait_for_function("() => WPP.conn.isMainReady()", page=self.page)
        needAuthentication = not await self.isAuthenticated()
        self.logger.info(f'{self.session}: {needAuthentication=}')
        if needAuthentication:
            await self.__checkQrCode()
        else:
            await self.__checkInChat()

    async def start(self):
        if self.isStarted:
            return

        self.isStarted = True
        self.lifecycle.transition(SessionState.STARTING)
        # ToDo:
        await self.initWhatsapp()

        await self.ThreadsafeBrowser.expose_function('checkQrCode', self.__checkQrCode, page=self.page)
        await self.ThreadsafeBrowser.expose_function('checkInChat', self.__checkInChat, page=self.page)
        # ToDo:
        self.logger.info(f'{self.session}: setInterval__checkStart')
        # Clear in whatsapp
        self.checkStartInterval = setInterval(self.loop, self.__checkStart, 10)

        # return True

    ############################### initWhatsapp ####################################################
    async def initWhatsapp(self):
        # await page.setUserAgent(useragentOverride);
        self.logger.info(f'{self.session}: unregisterServiceWorker')
        await self.unregisterServiceWorker()
        if self.version:
            self.logger.info(f'{self.session}: Setting WhatsApp WEB version to {self.version}')
            await self.setWhatsappVersion(self.version)
        self.logger.info(f'{self.session}: Loading WhatsApp WEB')
        # TODO: Unkown Error
        await self.ThreadsafeBrowser.goto(
            whatsappUrl, wait_until="load", timeout=self.options.get('navigationTimeout', 60000), referer='https://whatsapp.com/', page=self.page
        )
        # self.ThreadsafeBrowser.sync_goto(whatsappUrl, wait_until="domcontentloaded")
        self.logger.info(f'{self.session}: WhatsApp WEB loaded')

    async def unregisterServiceWorker(self):
        try:
            await self._evaluate_js('HostLayer.unregisterServiceWorker.0', page=self.page)
        except:
            pass

    async def setWhatsappVersion(self, version):
        body = ""
        try:
            body = await getPageContent(version)
        except:
            Logger.exception("setWhatsappVersion")
        if not body:
            Logger.error(f"Version not available for {version}, using latest as fallback")
            return

        await self.page.route('https://web.whatsapp.com/check-update', lambda route: route.abort())
        await self.page.route('https://web.whatsapp.com/', lambda route: route.fulfill(body=body))

    async def __handel_request(self, ):
        pass

    #################################################################################################
    async def __checkStart(self):
        if self.isClosed and hasattr(self, "checkStartInterval"):
            self.clearInterval(self.checkStartInterval)
            return
        await self.__needsToScan()

    async def __checkQrCode(self):
        need_scan = await self.__needsToScan()
        Logger.info(f"{self.session}: __checkQrCode {need_scan=}")
        self.isLogged = not need_scan if need_scan is not None else need_scan
        if not need_scan:
            self.attempt = 0
            return

        result = await self.__getQrCode()
        if not result or not result.get("urlCode") or self.urlCode == result.get("urlCode"):
            return

        phoneNumber = self.options.get("phoneNumber")
        if phoneNumber:
            return await self.__loginByCode(phoneNumber)

        self.urlCode = result.get("urlCode")
        self.attempt += 1

        qr = ''

        if self.logQR:  # or self.catchQR_dict:
            qr = self.asciiQr(self.urlCode)

        if self.logQR:
            self.logger.info(f'{self.session}: Waiting for QRCode Scan (Attempt {self.attempt})...:\n{qr}')
        else:
            self.logger.info(f'{self.session}: Waiting for QRCode Scan: Attempt {self.attempt}')

        self.__qrCode = result.get("base64Image")

        self.catchQR(
            qrCode=result.get("base64Image"),
            asciiQR=qr,
            attempt=self.attempt,
            urlCode=result.get("urlCode")
        )
        self.lifecycle.transition(SessionState.WAITING_QR)

    async def __loginByCode(self, phone: str):
        code = await self._evaluate_js('HostLayer.__loginByCode.0', {"phone": phone}, page=self.page)
        if self.logQR:
            Logger.info(f'Waiting for Login By Code (Code: {code})\n')
        else:
            Logger.info("Waiting for Login By Code")
        if self.catchLinkCode:
            self.catchLinkCode(code)

    async def __checkInChat(self):
        in_chat = await self.isInsideChat()
        self.isInChat = in_chat
        if not in_chat:
            return

        self.lifecycle.transition(SessionState.READY)

        self.logger.info(f'{self.session}: http => Connected')
        self.statusFind('inChat', self.session)

    async def tryAutoClose(self):
        if self.isClosed:
            self.logger.info(f'{self.session}: Closing the page')
            self.statusFind('autocloseCalled', self.session)
            if not self.page.is_closed():
                await self.close_async()
            if hasattr(self, "autoCloseInterval") and self.autoCloseInterval:
                self.cancelAutoClose()
            return

        if not hasattr(self, "autoCloseInterval"):
            return

        if self.autoCloseInterval:
            self.cancelAutoClose()

        if (self.autoClose > 0 or self.options.get(
                "deviceSyncTimeout") > 0) and (
                not self.autoCloseInterval or self.autoCloseInterval.is_set()):

            self.logger.info(f'{self.session}: Closing the page')
            self.autoCloseCalled = True

            self.isClosed = True
            self.statusFind('autocloseCalled', self.session)
            if not self.page.is_closed():
                await self.close_async()

    def sync_tryAutoClose(self):
        if self.isClosed:
            self.logger.info(f'{self.session}: Closing the page')
            self.statusFind('autocloseCalled', self.session)
            if not self.page.is_closed():
                self.close()

        if not hasattr(self, "autoCloseInterval"):
            return

        if self.autoCloseInterval:
            self.cancelAutoClose()

        if (self.autoClose > 0 or self.options.get(
                "deviceSyncTimeout") > 0) and (
                not self.autoCloseInterval or self.autoCloseInterval.is_set()):
            self.logger.info(f'{self.session}: Closing the page')
            self.autoCloseCalled = True

            self.isClosed = True
            self.statusFind('autocloseCalled', self.session)
            if not self.page.is_closed():
                self.close()

    def startAutoClose(self, _time=None):
        if _time is None:
            _time = self.autoClose

        if _time > 0 and (not hasattr(self, "autoCloseInterval") or not self.autoCloseInterval):
            seconds = _time
            self._auto_close_deadline = Deadline(seconds)
            self.logger.info(f'{self.session}: Auto close configured to {seconds}s')
            self.remain = seconds

            self.autoCloseInterval = setInterval(self.loop, self.autoCloseIntervalHandel, 1)

    # @staticmethod
    # def __setInterval(func, interval, *args, **kwargs):
    #     stopped = threading.Event()
    #
    #     def _loop_():
    #         while not stopped.is_set():
    #             func()
    #             time.sleep(interval)
    #
    #     th = threading.Thread(target=_loop_)
    #     th.start()
    #     return stopped

    def clearInterval(self, Interval):
        self.logger.debug(f'{self.session}: clearInterval {Interval}')
        if Interval:
            Interval.set()

    async def autoCloseIntervalHandel(self):
        if self.page.is_closed():
            self.cancelAutoClose()
            return

        if not self.isStarted or self.isClosed:
            self.cancelAutoClose()
            return

        deadline = getattr(self, '_auto_close_deadline', None)
        self.remain = math.ceil(deadline.remaining) if deadline and deadline.remaining is not None else self.remain
        if self.remain % 10 == 0 or self.remain <= 5:
            self.logger.info(f'{self.session}: http => Auto close remain: {self.remain}s')

        if self.remain <= 0:
            # Cant use wait, differance loop
            await self.tryAutoClose()

    def cancelAutoClose(self):
        if hasattr(self, "autoCloseInterval"):
            self.clearInterval(self.autoCloseInterval)
        self.autoCloseInterval = None
        self._auto_close_deadline = None

    async def __getQrCode(self):
        try:
            qr_result = await self.scrapeImg()
            return qr_result
        except:
            Logger.exception("__getQrCode")
            return

    def waitForQrCodeScan(self):
        if not self.isStarted:
            raise Exception('waitForQrCodeScan error: Session not started')
        while not self.page.is_closed() and not self.isLogged and not self.isClosed:
            # sleep(200 / 1000)
            self.ThreadsafeBrowser.sleep(0.2)
            needScan = self.__sync_needsToScan()
            self.isLogged = not needScan

    async def waitForQrCodeScan_(self):
        if not self.isStarted:
            raise Exception('waitForQrCodeScan error: Session not started')
        while not self.page.is_closed() and not self.isLogged and not self.isClosed:
            # sleep(200 / 1000)
            await asyncio.sleep(200 / 1000)
            needScan = await self.__needsToScan()
            self.isLogged = not needScan

    def waitForInChat(self):
        if not self.isStarted:
            raise Exception('waitForInChat error: Session not started')

        if not self.isLogged:
            Logger.info(f"not Logged")
            return False

        deadline = Deadline.milliseconds(self.options.get('deviceSyncTimeout', 0))
        while not self.page.is_closed() and self.isLogged and not self.isInChat and not self.isClosed:
            if deadline.expired:
                Logger.info(f"deviceSyncTimeout:{self.options.get('deviceSyncTimeout')} timeout")
                return False

            # TODO::
            self.ThreadsafeBrowser.sleep(1)

            inChat = self.sync_isInsideChat()
            self.isInChat = inChat

        return self.isInChat

    async def waitForInChat_(self):
        if not self.isStarted:
            raise Exception('waitForInChat error: Session not started')

        if not self.isLogged:
            Logger.info(f"not Logged")
            return False

        deadline = Deadline.milliseconds(self.options.get('deviceSyncTimeout', 0))
        while not self.page.is_closed() and self.isLogged and not self.isInChat and not self.isClosed:
            if deadline.expired:
                Logger.info(f"deviceSyncTimeout:{self.options.get('deviceSyncTimeout')} timeout")
                return False

            # TODO::
            await asyncio.sleep(1)

            inChat = await self.isInsideChat()
            self.isInChat = inChat

        return self.isInChat

    def waitForPageLoad(self):
        deadline = Deadline(self.options.get('pageLoadTimeout', 120))
        while not self.isInjected:
            if getattr(self, '_initialization_error', None):
                raise self._initialization_error
            if deadline.expired:
                raise SessionTimeoutError('Page initialization timed out')
            if self.page.is_closed():
                return
            # Stop when close
            if self.isClosed:
                return
            # TODO::
            self.ThreadsafeBrowser.sleep(.2)

        self.ThreadsafeBrowser.page_wait_for_function_sync(
            "() => typeof window.WPP !== 'undefined' && window.WPP.isReady", timeout=120 * 1000,
            page=self.page)

    async def waitForPageLoad_(self):
        deadline = Deadline(self.options.get('pageLoadTimeout', 120))
        while not self.isInjected:
            if getattr(self, '_initialization_error', None):
                raise self._initialization_error
            if deadline.expired:
                raise SessionTimeoutError('Page initialization timed out')
            if self.page.is_closed():
                return
            # Stop when close
            if self.isClosed:
                return
            # TODO::
            await asyncio.sleep(.2)

        await self.ThreadsafeBrowser.page_wait_for_function(
            "() => typeof window.WPP !== 'undefined' && window.WPP.isReady", timeout=120 * 1000,
            page=self.page)

    async def waitForLogin_(self):
        self.logger.info(f'{self.session}: http => Waiting page load')
        await self.waitForPageLoad_()
        self.logger.info(f'{self.session}: http => Checking is logged...')
        authenticated = await self.isAuthenticated()
        self.isLogged = authenticated
        self.logger.debug(f'{self.session}: http => {authenticated=}')
        self.startAutoClose()
        if authenticated is False:
            self.logger.info(f'{self.session}: http => Waiting for QRCode Scan...')
            self.statusFind('notLogged', self.session)
            await self.waitForQrCodeScan_()
            self.logger.info(f'{self.session}: http => Checking QRCode status...')
            # // Wait for interface update
            # TODO::
            await asyncio.sleep(.2)
            authenticated = await self.isAuthenticated()
            if authenticated is None:
                self.logger.warn(f'{self.session}: Failed to authenticate')
                self.statusFind('qrReadError', self.session)
            elif authenticated:
                self.logger.info(f'{self.session}: QRCode Success')
                self.statusFind('qrReadSuccess', self.session)
            else:
                self.logger.warn(f'{self.session}: QRCode Fail')
                self.statusFind('qrReadFail', self.session)
                await self.tryAutoClose()
                raise Exception('Failed to read the QRCode')
        elif authenticated is True:
            self.logger.info(f'{self.session}: Authenticated')
            self.statusFind('isLogged', self.session)
        if authenticated is True:
            # Reset the autoClose counter
            self.cancelAutoClose()
            #  Wait for interface update
            # TODO::
            await asyncio.sleep(.2)
            self.lifecycle.transition(SessionState.SYNCING)
            self.startAutoClose(self.options.get("deviceSyncTimeout", 0) / 1000)

            self.logger.info(f'{self.session}: http => Checking phone is connected...')
            inChat = await self.waitForInChat_()
            if not inChat:
                self.logger.warn(f'{self.session}: http => Phone not connected')
                self.statusFind('phoneNotConnected', self.session)
                await self.tryAutoClose()
                raise Exception(f"Phone not connected {self.isLogged=} {inChat=}")
            self.cancelAutoClose()
            self.lifecycle.transition(SessionState.READY)
            return True
        if authenticated is False:
            await self.tryAutoClose()
            self.logger.warn(f'{self.session}: Not logged')
            raise Exception("Not logged")

        await self.tryAutoClose()
        if self.autoCloseCalled:
            self.logger.error(f'{self.session}: Auto Close Called')
            raise Exception("Auto Close Called")

        if self.page.is_closed() or self.isClosed:
            self.logger.error(f'{self.session}: Page Closed')
            raise Exception("Page Closed")

        self.logger.error(f'{self.session}: Unknow error')
        raise Exception("Unknow error")

    def waitForLogin(self):
        self.logger.info(f'{self.session}: http => Waiting page load')
        self.waitForPageLoad()
        self.logger.info(f'{self.session}: http => Checking is logged...')
        authenticated = self.sync_isAuthenticated()
        self.isLogged = authenticated
        self.logger.debug(f'{self.session}: http => {authenticated=}')
        self.startAutoClose()
        if authenticated is False:
            self.logger.info(f'{self.session}: http => Waiting for QRCode Scan...')
            self.statusFind('notLogged', self.session)
            self.waitForQrCodeScan()
            self.logger.info(f'{self.session}: http => Checking QRCode status...')
            # // Wait for interface update
            # TODO::
            self.ThreadsafeBrowser.sleep(.2)
            authenticated = self.sync_isAuthenticated()
            if authenticated is None:
                self.logger.warn(f'{self.session}: Failed to authenticate')
                self.statusFind('qrReadError', self.session)
            elif authenticated:
                self.logger.info(f'{self.session}: QRCode Success')
                self.statusFind('qrReadSuccess', self.session)
            else:
                self.logger.warn(f'{self.session}: QRCode Fail')
                self.statusFind('qrReadFail', self.session)
                self.sync_tryAutoClose()
                raise Exception('Failed to read the QRCode')
        elif authenticated is True:
            self.logger.info(f'{self.session}: Authenticated')
            self.statusFind('isLogged', self.session)
        if authenticated is True:
            # Reset the autoClose counter
            self.cancelAutoClose()
            #  Wait for interface update
            # TODO::
            self.ThreadsafeBrowser.sleep(.2)
            self.lifecycle.transition(SessionState.SYNCING)
            self.startAutoClose(self.options.get("deviceSyncTimeout", 0) / 1000)

            self.logger.info(f'{self.session}: http => Checking phone is connected...')
            inChat = self.waitForInChat()
            if not inChat:
                self.logger.warn(f'{self.session}: http => Phone not connected')
                self.statusFind('phoneNotConnected', self.session)
                self.sync_tryAutoClose()
                raise Exception(f"Phone not connected {self.isLogged=} {inChat=}")
            self.cancelAutoClose()
            self.lifecycle.transition(SessionState.READY)
            return True
        if authenticated is False:
            self.sync_tryAutoClose()
            self.logger.warn(f'{self.session}: Not logged')
            raise Exception("Not logged")

        self.sync_tryAutoClose()
        if self.autoCloseCalled:
            self.logger.error(f'{self.session}: Auto Close Called')
            raise Exception("Auto Close Called")

        if self.page.is_closed() or self.isClosed:
            self.logger.error(f'{self.session}: Page Closed')
            raise Exception("Page Closed")

        self.logger.error(f'{self.session}: Unknow error')
        raise Exception("Unknow error")

    def getHostDevice(self):
        """@returns Current host device details"""
        return self._evaluate_js_sync('HostLayer.getHostDevice.0', page=self.page)

    def getWid(self):
        """@returns Current wid connected"""
        return self._evaluate_js_sync('HostLayer.getWid.0', page=self.page)

    async def getWAVersion(self):
        """Retrieves WA version"""
        await self.ThreadsafeBrowser.page_wait_for_function("() => WAPI.getWAVersion()", page=self.page)
        return await self._evaluate_js('HostLayer.getWAVersion.0', page=self.page)

    async def getWAJSVersion(self):
        await self.ThreadsafeBrowser.page_wait_for_function("() => window.WPP.version", page=self.page)
        return await self._evaluate_js('HostLayer.getWAJSVersion.0', page=self.page)

    def getConnectionState(self):
        return self._evaluate_js_sync('HostLayer.getConnectionState.0',
                                                         page=self.page)

    def isConnected(self):
        """Retrieves if the phone is online. Please note that this may not be real time."""
        return self._evaluate_js_sync('HostLayer.isConnected.0', page=self.page)

    def isOnline(self):
        return self._evaluate_js_sync('HostLayer.isOnline.0', page=self.page)

    def isLoggedIn(self):
        return self._evaluate_js_sync('HostLayer.isLoggedIn.0', page=self.page)

    def getBatteryLevel(self):
        return self._evaluate_js_sync('HostLayer.getBatteryLevel.0', page=self.page)

    def startPhoneWatchdog(self, interval=15000):
        return self._evaluate_js_sync('HostLayer.startPhoneWatchdog.0', interval,
                                                         page=self.page)

    def stopPhoneWatchdog(self):
        return self._evaluate_js_sync('HostLayer.stopPhoneWatchdog.0', page=self.page)

    def isMultiDevice(self):
        return self._evaluate_js_sync('HostLayer.isMultiDevice.0', page=self.page)

    def isMainLoaded(self):
        return self._evaluate_js_sync('HostLayer.isMainLoaded.0', page=self.page)

    def isMainInit(self):
        return self._evaluate_js_sync('HostLayer.isMainInit.0', page=self.page)

    def joinWebBeta(self, value: bool):
        return self._evaluate_js_sync('HostLayer.joinWebBeta.0', value,
                                                         page=self.page)

    def getBuildConstants(self, ):
        return self._evaluate_js_sync('HostLayer.getBuildConstants.0', page=self.page)

    def isLidMigrated(self, ):
        return self._evaluate_js_sync('HostLayer.isLidMigrated.0', page=self.page)

    async def isAuthenticated(self):
        try:
            if self.page.is_closed() or self.isClosed:
                return None
            return await self._evaluate_js(
                'HostLayer.isAuthenticated.0', page=self.page)
        except Exception as e:
            self.logger.debug(e)
            return None

    def sync_isAuthenticated(self):
        try:
            if self.page.is_closed() or self.isClosed:
                return False
            return self._evaluate_js_sync(
                'HostLayer.sync_isAuthenticated.0', page=self.page)
        except Exception as e:
            self.logger.debug(e)
            return False

    async def __needsToScan(self):
        rs = await self.isAuthenticated()
        return not rs if rs is not None else rs

    def __sync_needsToScan(self):
        return not self.sync_isAuthenticated()

    @staticmethod
    def asciiQr(code):
        return asciiQr(code=code)

    async def scrapeImg(self):
        try:
            await self.ThreadsafeBrowser.page_wait_for_function("()=>document.querySelector('canvas')?.closest",
                                                                page=self.page)
        except:
            pass
        click = await self._evaluate_js('HostLayer.scrapeImg.0', page=self.page)
        if click:
            await self.ThreadsafeBrowser.page_wait_for_function("""() => {
              const selectorImg = document.querySelector('canvas');
              const selectorUrl = selectorImg.closest('[data-ref]');
              return selectorUrl.getAttribute('data-ref');
            }""", page=self.page)

        result = await self._evaluate_js('HostLayer.scrapeImg.1', page=self.page)
        return result

    async def isInsideChat(self):
        result = await self._evaluate_js(
            'HostLayer.isInsideChat.0', page=self.page)
        return result if result else False

    def sync_isInsideChat(self):
        result = self._evaluate_js_sync(
            'HostLayer.sync_isInsideChat.0', page=self.page)
        return result if result else False

    # /**
    #  * Returns the version of WhatsApp Web currently being run
    #  * @returns {Promise<string>}
    #  */
    async def getWWebVersion(self):
        return await self._evaluate_js('HostLayer.getWWebVersion.0', page=self.page)

    async def inject_api(self):
        self.logger.debug(f'{self.session}: start inject')
        try:
            injected = await self._evaluate_js('HostLayer.inject_api.0'
                                                                  , page=self.page)
        except:
            injected = False

        if injected:
            self.logger.info(f'{self.session}: already injected')
            return True

        self.logger.info(f'{self.session}: injected state: {injected}')

        await self.ThreadsafeBrowser.page_wait_for_function('window.Debug?.VERSION != undefined', page=self.page)
        # TODO::
        # version = await self.getWWebVersion()
        # isCometOrAbove = int(version.split('.')[1]) >= 3000
        # Logger.info(f"version {version}, {isCometOrAbove=}")
        # if isCometOrAbove:
        #     await self.ThreadsafeBrowser.page_evaluate(ExposeAuthStore, page=self.pupPage)
        # else:
        #     await self.ThreadsafeBrowser.page_evaluate(ExposeLegacyAuthStore, ModuleRaid, page=self.pupPage)

        # self.logger.info(f'{self.session}: wait for load webpackChunkwhatsapp_web_client')
        # try:
        #     # await self.ThreadsafeBrowser.page_evaluate(
        #     #     "() => (window?.webpackChunkwhatsapp_web_client?.length || 0) > 3", page=self.page)
        #     await self.ThreadsafeBrowser.page_wait_for_function(
        #         "() => (window?.webpackChunkwhatsapp_web_client?.length || 0) > 3", timeout=10000, page=self.page)
        # except:
        #     pass
        # await asyncio.sleep(0.1)
        self.logger.info(f'{self.session}: inject wppconnect-wa.js')
        # await self.ThreadsafeBrowser.add_script_tag(
        #     url="https://github.com/wppconnect-team/wa-js/releases/download/nightly/wppconnect-wa.js")
        source = await getWaJs(self.wa_js_version, cache_dir=self.options.get('runtimeCacheDir'))
        try:
            await self._inject_runtime(source)
        except (BrowserError, RuntimeCompatibilityError):
            from WPP_Whatsapp.api.helpers.wa_version import _bundled_wajs
            bundled = _bundled_wajs()
            if self.wa_js_version not in (None, 'latest') or source == bundled:
                raise
            self.logger.warning('Latest WA-JS is incompatible; restarting initialization with bundled runtime')
            self._runtime_reloading = True
            try:
                await self.ThreadsafeBrowser.create_task(self.page.reload(wait_until='load', timeout=self.options.get('navigationTimeout', 60000)))
            finally:
                self._runtime_reloading = False
            await self.ThreadsafeBrowser.page_wait_for_function('window.Debug?.VERSION != undefined', page=self.page)
            await self._evaluate_js('HostLayer._afterPageLoad.0', getattr(self, '_runtime_config', {}), page=self.page)
            await self._inject_runtime(bundled)
        # await self.ThreadsafeBrowser.page_wait_for_function("() => window.WPP?.isReady", page=self.page)
        try:
            await self._evaluate_js('HostLayer.inject_api.1', page=self.page)
        except:
            pass
        self.logger.info(f'{self.session}: inject wapi.js')
        # base_dir = Path(__file__).resolve().parent.parent.parent
        # await self.ThreadsafeBrowser.add_script_tag(path=os.path.join(base_dir, 'js_lib', 'wapi.js'), page=self.page)
        # await self.ThreadsafeBrowser.add_script_tag(
        #     url="https://raw.githubusercontent.com/3mora2/WPP_Whatsapp/main/WPP_Whatsapp/js_lib/wapi.js",
        #     page=self.page
        # )
        await self.ThreadsafeBrowser.add_script_tag(content=WAPI, page=self.page)
        await self.ThreadsafeBrowser.page_wait_for_function(
            "() => window.WAPI?._wppWhatsappReady === true", page=self.page)
        await self._onLoadingScreen()
        self.logger.info(f'{self.session}: wait window.WPP.isReady')

        # try:
        #     # Make sure WAPI is initialized
        #     await self.ThreadsafeBrowser.page_wait_for_function("""() => {
        #     return (typeof window.WAPI !== 'undefined' && typeof window.Store !== 'undefined' && window.WPP.isReady);
        #     }""", page=self.page)
        # except:
        #     pass
        return True

    async def _inject_runtime(self, source):
        await self.ThreadsafeBrowser.add_script_tag(**source, page=self.page)
        await self.ThreadsafeBrowser.page_wait_for_function(
            '() => window.WPP?.isReady', timeout=self.options.get('runtimeReadyTimeout', 30000), page=self.page)
        self.runtime_capabilities = await self._get_bridge().capabilities()

    def loadingScreen(self, percent, message):
        self.logger.info(f'{self.session}: loadingScreen: {percent}, {message}')
        if self.lastPercent != percent or self.lastPercentMessage != message:
            self.onLoadingScreen(percent, message)
            self.lastPercent = percent
            self.lastPercentMessage = message

    async def _onLoadingScreen(self):
        await self._evaluate_js('HostLayer._onLoadingScreen.0', page=self.page)
        try:
            await self.ThreadsafeBrowser.expose_function('loadingScreen', self.loadingScreen, page=self.page)
        except:
            # Function "loadingScreen" has been already registered
            pass
        await self._evaluate_js(
            'HostLayer._onLoadingScreen.1',
            {
                "PROGRESS": "//*[@id='app']/div/div/div[2]/progress",
                "PROGRESS_NEW_THEME": "//*[@id='app']/div/div/div[3]/progress",
                "PROGRESS_MESSAGE": "//*[@id='app']/div/div/div[3]",
                "PROGRESS_MESSAGE_NEW_THEME": "//*[@id='app']/div/div/div[2]",
            },
            page=self.page,
        )

    @staticmethod
    def valid_chatId(chatId):
        """
        Validate and format chatId to proper WhatsApp format

        @param chatId: Phone number, group ID, or full chat ID
        @return: Formatted chat ID with @c.us, @g.us or @lid suffix
        @raises: ValueError if chatId is invalid
        """
        if not chatId:
            raise ValueError("chatId cannot be empty")

        if not isinstance(chatId, str):
            chatId = str(chatId)

        # Remove any whitespace and plus sign
        chatId = chatId.strip().replace("+", "")

        # Check if already has proper suffix
        if '@' in chatId:
            # Validate suffix
            if not chatId.endswith(('@c.us', '@g.us', '@broadcast', '@newsletter', '@lid')):
                raise ValueError(f"Invalid chatId suffix: {chatId}. Must end with @c.us, @g.us, @lid, @broadcast, or @newsletter")
            return chatId

        # Validate phone/group number format (digits only, possibly with hyphens for groups)
        if not chatId.replace("-", "").isdigit():
            raise ValueError(f"Invalid chatId format: {chatId}. Must contain only digits (and optional hyphens for groups)")

        # Determine if group or contact based on length
        # Groups typically have format: number-number (e.g., 123456-789012)
        # Contacts are just phone numbers
        if '-' in chatId or len(chatId) > 15:
            chatId += '@g.us'
        else:
            chatId += '@c.us'
        return chatId

    async def getPnLidEntry_(self, chat_id):
        # Implemented later
        return {}
    def getPnLidEntry(self, chat_id):
        # Implemented later
        return {}

    async def get_chat_id_(self, chat_id:str):
        chatId = self.valid_chatId(chat_id)
        if chatId.endswith('@c.us'):
            chat_info = await self.getPnLidEntry_(chatId)
            chatId = self._mapped_chat_id(chatId, chat_info)
        return chatId

    def get_chat_id(self, chat_id:str):
        chatId = self.valid_chatId(chat_id)
        if chatId.endswith('@c.us'):
            chat_info = self.getPnLidEntry(chatId)
            chatId = self._mapped_chat_id(chatId, chat_info)

        return chatId

    @staticmethod
    def _mapped_chat_id(chat_id, chat_info):
        # Mapping can be absent for a valid phone number. Never replace it
        # with None, and accept both WA-JS strings and serialized Wid objects.
        for field in ('lid', 'phoneNumber'):
            value = (chat_info or {}).get(field)
            if isinstance(value, dict):
                value = value.get('_serialized')
            if isinstance(value, str) and value:
                return value
        return chat_id

    def close(self):
        self.isClosed = True
        self.ThreadsafeBrowser.sync_close()

    @staticmethod
    def convert_to_base64(path):
        mimetypes_add = {"webp": "image/webp"}
        # mime = magic.Magic(mime=True)
        # content_type = mime.from_file(path)
        content_type = mimetypes.guess_type(path)[0]
        if not content_type:
            content_type = mimetypes_add.get(path.split(".")[-1], None)
        if not content_type:
            content_type = 'application/octet-stream'
        # filename = os.path.basename(path)
        with open(path, "rb") as image_file:
            archive = base64_model.b64encode(image_file.read())
            archive = archive.decode("utf-8")

        return "data:" + content_type + ";base64," + archive

    def fileToBase64(self, path):
        return self.convert_to_base64(path)

    async def _media_to_base64(self, value, media_type=None):
        from WPP_Whatsapp.api.helpers.download_file import downloadFileToBase64

        if not isinstance(value, str) or not value:
            raise ValueError("Empty or invalid media input")
        if value.startswith('data:'):
            content = value
        elif value.lower().startswith(('http://', 'https://')):
            content = await downloadFileToBase64(value)
        else:
            content = self.fileToBase64(value)
        if not content:
            raise ValueError("Could not load media")
        mime = self.base64MimeTypeV2(content)
        if not mime or (media_type and not mime.startswith(media_type + '/')):
            raise ValueError(f"Expected {media_type or 'valid'} media")
        return content

    @staticmethod
    def base64MimeType(encoded):
        result = encoded.split(";base64")[0].split(":")[-1]
        return result

    @staticmethod
    def base64MimeTypeV2(encoded: str):
        result = None
        if not isinstance(encoded, str):
            return result

        mime = re.match(r'data:([a-zA-Z0-9]+/[a-zA-Z0-9-.+]+).*,.*', encoded)
        if mime and mime.group(1):
            result = mime.group(1)

        return result

    def refreshLinkCode(self, timeout=60):
        return self.ThreadsafeBrowser.run_threadsafe(self.refreshLinkCode_, timeout_=timeout)

    async def refreshLinkCode_(self):
        return await self._evaluate_js('HostLayer.refreshLinkCode_.0', page=self.page)

    def getQrCode(self, timeout=60):
        return self.ThreadsafeBrowser.run_threadsafe(self.getQrCode_, timeout_=timeout)

    async def getQrCode_(self):
        return await self.__getQrCode()

    def isMainReady(self):
        return self._evaluate_js_sync('HostLayer.isMainReady.0', page=self.page)

    async def isMainReady_(self):
        return await self._evaluate_js('HostLayer.isMainReady_.0', page=self.page)
