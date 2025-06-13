import asyncio
import logging
import base64 as base64_model
import mimetypes
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Callable
from playwright._impl._errors import TargetClosedError
from playwright.async_api import Page
from WPP_Whatsapp.api.const import whatsappUrl, Logger
from WPP_Whatsapp.api.helpers.function import asciiQr
from WPP_Whatsapp.api.helpers.wapi import WAPI
from WPP_Whatsapp.controllers.browser import ThreadsafeBrowser
from WPP_Whatsapp.api.helpers.jsFunction import setInterval
from WPP_Whatsapp.api.helpers.wa_version import getPageContent, getWaJs


class HostLayer:
    page: Page
    session: str
    logger: logging
    ThreadsafeBrowser: "ThreadsafeBrowser"
    options: dict
    autoCloseInterval: asyncio.Event
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
    checkStartInterval: asyncio.Event
    logQR: bool
    remain: int
    version: str
    wa_js_version: str
    loop: object
    catchLinkCode: Callable[[str], None] = None

    def __init__(self):
        self.isInChat = False
        self.isLogged = False
        self.isClosed = False
        self.__initialize()

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

    async def on_close(self, _):
        self.isClosed = True
        self.logger.info(f'{self.session}: Page Closed')
        self.cancelAutoClose()

    async def on_load(self, _):
        if self.isClosed:
            return
        try:
            self.logger.info(f'{self.session}: Page loaded')
            await self._afterPageLoad()
        except (RuntimeError, TargetClosedError):
            # mean stop app
            self.logger.info(f'{self.session}: Stop App, Auto Close')
            self.isClosed = True
            await self.tryAutoClose()

    async def _afterPageLoad(self):
        self.logger.info(f'{self.session}: Injecting wapi.js')
        options = {
            "deviceName": self.options.get("deviceName"),
            "disableGoogleAnalytics": self.options.get("disableGoogleAnalytics"),
            "googleAnalyticsId": self.options.get("googleAnalyticsId"),
            "linkPreviewApiServers": self.options.get("linkPreviewApiServers"),
            "poweredBy": self.options.get("poweredBy"),
        }
        self.logger.info(f'{self.session}: Start WPPConfig')
        await self.ThreadsafeBrowser.page_evaluate("""(options) => {window.WPPConfig = options;}""", options,
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
            await self.ThreadsafeBrowser.page_evaluate("() => {WPP.on('conn.auth_code_change', window.checkQrCode);}",
                                                       page=self.page)
            await self.ThreadsafeBrowser.page_evaluate("() => {WPP.on('conn.main_ready', window.checkInChat);}",
                                                       page=self.page)
        except:
            Logger.exception("window.checkQrCode")

        self.logger.info(f'{self.session}: Wait First selector (INTRO_IMG, INTRO_QRCODE)')
        INTRO_IMG_SELECTOR = '[data-icon*=\'search\']'
        INTRO_QRCODE_SELECTOR = 'div[data-ref] canvas'
        result = await self.ThreadsafeBrowser.wait_for_first_selectors(INTRO_IMG_SELECTOR, INTRO_QRCODE_SELECTOR)
        needAuthentication = True if result == INTRO_QRCODE_SELECTOR else False

        self.logger.info(f'{self.session}: {needAuthentication=}')
        if needAuthentication:
            await self.__checkQrCode()
        else:
            await self.__checkInChat()

    async def start(self):
        if self.isStarted:
            return

        self.isStarted = True
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
            whatsappUrl, wait_until="load", timeout=0, referer='https://whatsapp.com/', page=self.page
        )
        # self.ThreadsafeBrowser.sync_goto(whatsappUrl, wait_until="domcontentloaded")
        self.logger.info(f'{self.session}: WhatsApp WEB loaded')

    async def unregisterServiceWorker(self):
        try:
            await self.ThreadsafeBrowser.page_evaluate("""() => {
                    setInterval(() => {
                      window.onerror = console.error;
                      window.onunhandledrejection = console.error;
                    }, 500);
                    
                    // Remove existent service worker
                    navigator.serviceWorker
                      .getRegistrations()
                      .then((registrations) => {
                        for (let registration of registrations) {
                          registration.unregister();
                        }
                      })
                      .catch((err) => null);
                
                    // Disable service worker registration
                    // @ts-ignore
                    navigator.serviceWorker.register = new Promise(() => {});
                  }""", page=self.page)
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

    async def __loginByCode(self, phone: str):
        code = await self.ThreadsafeBrowser.page_evaluate("""async ({ phone }) => {
        return JSON.parse(
          JSON.stringify(await WPP.conn.genLinkDeviceCodeForPhoneNumber(phone))
        );
          }""", {"phone": phone})
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

        self.logger.info(f'{self.session}: http => Connected')
        self.statusFind('inChat', self.session)

    async def tryAutoClose(self):
        if self.isClosed:
            self.logger.info(f'{self.session}: Closing the page')
            self.statusFind('autocloseCalled', self.session)
            if not self.page.is_closed():
                await self.ThreadsafeBrowser.close()        
            if  hasattr(self, "autoCloseInterval") and self.autoCloseInterval:
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
                await self.ThreadsafeBrowser.close()

    def sync_tryAutoClose(self):
        if self.isClosed:
            self.logger.info(f'{self.session}: Closing the page')
            self.statusFind('autocloseCalled', self.session)
            if not self.page.is_closed():
                self.ThreadsafeBrowser.sync_close()

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
                self.ThreadsafeBrowser.sync_close()

    def startAutoClose(self, _time=None):
        if not _time:
            _time = self.autoClose

        if _time > 0 and (not hasattr(self, "autoCloseInterval") or not self.autoCloseInterval):
            # seconds = round(time / 1000)
            seconds = round(_time)
            self.logger.info(f'{self.session}: Auto close configured to {seconds}s')
            self.remain = seconds

            self.autoCloseInterval = setInterval(self.loop, self.autoCloseIntervalHandel, 5)

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

        self.remain -= 1
        if self.remain % 10 == 0 or self.remain <= 5:
            self.logger.info(f'{self.session}: http => Auto close remain: {self.remain}s')

        if self.remain <= 0:
            # Cant use wait, differance loop
            await self.tryAutoClose()

    def cancelAutoClose(self):
        if hasattr(self, "autoCloseInterval"):
            self.clearInterval(self.autoCloseInterval)
        # self.autoCloseInterval = None

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

        start = datetime.now()
        while not self.page.is_closed() and self.isLogged and not self.isInChat and not self.isClosed:
            if 0 < self.options.get("deviceSyncTimeout") <= (datetime.now() - start).seconds:
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

        start = datetime.now()
        while not self.page.is_closed() and self.isLogged and not self.isInChat and not self.isClosed:
            if 0 < self.options.get("deviceSyncTimeout") <= (datetime.now() - start).seconds:
                Logger.info(f"deviceSyncTimeout:{self.options.get('deviceSyncTimeout')} timeout")
                return False

            # TODO::
            await asyncio.sleep(1)

            inChat = await self.isInsideChat()
            self.isInChat = inChat

        return self.isInChat

    def waitForPageLoad(self):
        while not self.isInjected:
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
        while not self.isInjected:
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
            self.startAutoClose(self.options.get("deviceSyncTimeout"))

            self.logger.info(f'{self.session}: http => Checking phone is connected...')
            inChat = await self.waitForInChat_()
            if not inChat:
                self.logger.warn(f'{self.session}: http => Phone not connected')
                self.statusFind('phoneNotConnected', self.session)
                await self.tryAutoClose()
                raise Exception(f"Phone not connected {self.isLogged=} {inChat=}")
            self.cancelAutoClose()
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
            self.startAutoClose(self.options.get("deviceSyncTimeout"))

            self.logger.info(f'{self.session}: http => Checking phone is connected...')
            inChat = self.waitForInChat()
            if not inChat:
                self.logger.warn(f'{self.session}: http => Phone not connected')
                self.statusFind('phoneNotConnected', self.session)
                self.sync_tryAutoClose()
                raise Exception(f"Phone not connected {self.isLogged=} {inChat=}")
            self.cancelAutoClose()
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
        return self.ThreadsafeBrowser.page_evaluate_sync("() => WAPI.getHost()", page=self.page)

    def getWid(self):
        """@returns Current wid connected"""
        return self.ThreadsafeBrowser.page_evaluate_sync("() => WAPI.getWid()", page=self.page)

    async def getWAVersion(self):
        """Retrieves WA version"""
        await self.ThreadsafeBrowser.page_wait_for_function("() => WAPI.getWAVersion()", page=self.page)
        return await self.ThreadsafeBrowser.page_evaluate("() => WAPI.getWAVersion()", page=self.page)

    async def getWAJSVersion(self):
        await self.ThreadsafeBrowser.page_wait_for_function("() => window.WPP.version", page=self.page)
        return await self.ThreadsafeBrowser.page_evaluate("() => window.WPP.version", page=self.page)

    def getConnectionState(self):
        return self.ThreadsafeBrowser.page_evaluate_sync("() => {return window.WPP.whatsapp.Socket.state;}",
                                                         page=self.page)

    def isConnected(self):
        """Retrieves if the phone is online. Please note that this may not be real time."""
        return self.ThreadsafeBrowser.page_evaluate_sync("() => WAPI.isConnected()", page=self.page)

    def isLoggedIn(self):
        return self.ThreadsafeBrowser.page_evaluate_sync("() => WAPI.isLoggedIn()", page=self.page)

    def getBatteryLevel(self):
        return self.ThreadsafeBrowser.page_evaluate_sync("() => WAPI.getBatteryLevel()", page=self.page)

    def startPhoneWatchdog(self, interval=15000):
        return self.ThreadsafeBrowser.page_evaluate_sync("(interval) => WAPI.startPhoneWatchdog(interval)", interval,
                                                         page=self.page)

    def stopPhoneWatchdog(self):
        return self.ThreadsafeBrowser.page_evaluate_sync("() => WAPI.stopPhoneWatchdog()", page=self.page)

    def isMultiDevice(self):
        return self.ThreadsafeBrowser.page_evaluate_sync("() => window.WPP.conn.isMultiDevice()", page=self.page)

    async def isAuthenticated(self):
        try:
            if self.page.is_closed() or self.isClosed:
                return None
            return await self.ThreadsafeBrowser.page_evaluate(
                "() => typeof window.WPP !== 'undefined' && window.WPP.conn.isRegistered()", page=self.page)
        except Exception as e:
            self.logger.debug(e)
            return None

    def sync_isAuthenticated(self):
        try:
            if self.page.is_closed() or self.isClosed:
                return False
            return self.ThreadsafeBrowser.page_evaluate_sync(
                "() => typeof window.WPP !== 'undefined' && window.WPP.conn.isRegistered()", page=self.page)
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
        click = await self.ThreadsafeBrowser.page_evaluate("""() => {
              const selectorImg = document.querySelector('canvas');
              const selectorUrl = selectorImg.closest('[data-ref]');
              //const buttonReload = selectorUrl.querySelector('[role="button"]') as HTMLButtonElement;
              const buttonReload = selectorUrl.querySelector('button');
              if (buttonReload != null) {
                buttonReload.click();
                return true;
              }
              return false;
            }""", page=self.page)
        if click:
            await self.ThreadsafeBrowser.page_wait_for_function("""() => {
              const selectorImg = document.querySelector('canvas');
              const selectorUrl = selectorImg.closest('[data-ref]');
              return selectorUrl.getAttribute('data-ref');
            }""", page=self.page)

        result = await self.ThreadsafeBrowser.page_evaluate("""() => {
              const selectorImg = document.querySelector('canvas');
              const selectorUrl = selectorImg.closest('[data-ref]');
        
              if (selectorImg != null && selectorUrl != null) {
                let data = {
                  base64Image: selectorImg.toDataURL(),
                  urlCode: selectorUrl.getAttribute('data-ref'),
                };
                return data;
              } else {
                return undefined;
              }
            }""", page=self.page)
        return result

    async def isInsideChat(self):
        result = await self.ThreadsafeBrowser.page_evaluate(
            "() => typeof window.WPP !== 'undefined' && window.WPP.conn.isMainReady()", page=self.page)
        return result if result else False

    def sync_isInsideChat(self):
        result = self.ThreadsafeBrowser.page_evaluate_sync(
            "() => typeof window.WPP !== 'undefined' && window.WPP.conn.isMainReady()", page=self.page)
        return result if result else False

    # /**
    #  * Returns the version of WhatsApp Web currently being run
    #  * @returns {Promise<string>}
    #  */
    async def getWWebVersion(self):
        return await self.ThreadsafeBrowser.page_evaluate("""() => {
            return window.Debug.VERSION;
        }""")

    async def inject_api(self):
        self.logger.debug(f'{self.session}: start inject')
        try:
            injected = await self.ThreadsafeBrowser.page_evaluate("""() => {
                        return (typeof window.WAPI !== 'undefined' &&typeof window.Store !== 'undefined');}"""
                                                                  , page=self.page)
        except:
            injected = False

        if injected:
            self.logger.info(f'{self.session}: already injected')
            return

        self.logger.info(f'{self.session}: injected state: {injected}')

        await self.ThreadsafeBrowser.page_wait_for_function('window.Debug?.VERSION != undefined')
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
        await self.ThreadsafeBrowser.add_script_tag(**(await getWaJs(self.wa_js_version)), page=self.page)
        # await self.ThreadsafeBrowser.page_wait_for_function("() => window.WPP?.isReady", page=self.page)
        try:
            await self.ThreadsafeBrowser.page_evaluate("""() => {
                                  window.WPP.chat.defaultSendMessageOptions.createChat = true;
                                  window.WPP.conn.setKeepAlive(true);
                                }""", page=self.page)
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

    def loadingScreen(self, percent, message):
        self.logger.info(f'{self.session}: loadingScreen: {percent}, {message}')
        if self.lastPercent != percent or self.lastPercentMessage != message:
            self.onLoadingScreen(percent, message)
            self.lastPercent = percent
            self.lastPercentMessage = message

    async def _onLoadingScreen(self):
        await self.ThreadsafeBrowser.page_evaluate("""function getElementByXpath(path) {
        return document.evaluate(path, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
            }""", page=self.page)
        try:
            await self.ThreadsafeBrowser.expose_function('loadingScreen', self.loadingScreen, page=self.page)
        except:
            # Function "loadingScreen" has been already registered
            pass
        await self.ThreadsafeBrowser.page_evaluate(
            """
     function load_ (selectors) {
      let observer = new MutationObserver(function () {
        let window2 = window;

        let progressBar = window2.getElementByXpath(selectors.PROGRESS);
        let progressBarNewTheme = window2.getElementByXpath(
          selectors.PROGRESS_NEW_THEME
        );
        let progressMessage = window2.getElementByXpath(
          selectors.PROGRESS_MESSAGE
        );
        let progressMessageNewTheme = window2.getElementByXpath(
          selectors.PROGRESS_MESSAGE_NEW_THEME
        );

        if (progressBar) {
          if (
            this.lastPercent !== progressBar.value ||
            this.lastPercentMessage !== progressMessage.innerText
          ) {
            window2.loadingScreen(progressBar.value, progressMessage.innerText);
            this.lastPercent = progressBar.value;
            this.lastPercentMessage = progressMessage.innerText;
          }
        } else if (progressBarNewTheme) {
          if (
            this.lastPercent !== progressBarNewTheme.value ||
            this.lastPercentMessage !== progressMessageNewTheme.innerText
          ) {
            const progressMsg =
              progressMessageNewTheme.innerText != 'WhatsApp'
                ? progressMessageNewTheme.innerText
                : '';
            window2.loadingScreen(progressBarNewTheme.value, progressMsg);
            this.lastPercent = progressBarNewTheme.value;
            this.lastPercentMessage = progressMsg;
          }
        }
      });

      observer.observe(document, {
        attributes: true,
        childList: true,
        characterData: true,
        subtree: true,
      });
    }""",
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
        chatId = chatId.replace("+", "")
        if chatId and (
                not chatId.endswith('@c.us') and not chatId.endswith('@g.us') and not chatId.endswith('@newsletter')):
            chatId += '@g.us' if len(chatId) > 15 else '@c.us'
        return chatId

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
