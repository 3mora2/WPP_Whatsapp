import asyncio
import logging
import os
import traceback
from asyncio import sleep
from datetime import datetime
from pathlib import Path

import pyqrcode
from playwright._impl import _api_types
from playwright.async_api import Page, BrowserContext

from WPP_Whatsapp.api.const import whatsappUrl


class HostLayer:
    page: Page
    browser: BrowserContext
    session: str
    options = {}
    logger: logging
    autoCloseInterval = None
    autoCloseCalled = False
    isInitialized = False
    isInjected = False
    isStarted = False
    isLogged = False
    isInChat = False
    logQR = False
    checkStartInterval = None
    urlCode = ''
    status = ''
    attempt = 0
    autoClose = 0
    # catchQR_dict = {}
    # statusFind_dict = {}
    # onLoadingScreen = LoadingScreen()
    lastPercent = None
    lastPercentMessage = None
    Browser: "Browser"

    def __init__(self):
        # self.session = session
        # asyncio.set_event_loop(self.loop)

        super().__init__()
        self.__initialize()
        # self.start()

    async def page_evaluate(self, expression, arg=None):
        try:
            return await self.Browser.page_evaluate(expression, arg)
        except _api_types.Error as error:
            if "WPP is not defined" in error.message:
                pass

            elif "Cannot read properties of null" in error.message:
                pass

            else:
                raise error

    async def page_wait_for_function(self, expression, arg=None, timeout=None, polling=None):
        try:
            return await self.Browser.page_wait_for_function(expression, arg, timeout, polling)
        except _api_types.Error as error:
            if "WPP is not defined" in error.message:
                pass

            elif "Cannot read properties of null" in error.message:
                pass

            else:
                raise error

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

    def on_close(self):
        self.logger.info(f'{self.session}: Page Closed')
        self.cancelAutoClose()

    async def on_load(self):
        self.logger.info(f'{self.session}: Page loaded')
        await self._afterPageLoad()

    async def _afterPageLoad(self):
        self.logger.info(f'{self.session}: Injecting wapi.js')
        options = {
            "deviceName": self.options.get("deviceName"),
            "disableGoogleAnalytics": self.options.get("disableGoogleAnalytics"),
            "googleAnalyticsId": self.options.get("googleAnalyticsId"),
            "linkPreviewApiServers": self.options.get("linkPreviewApiServers"),
            "poweredBy": self.options.get("poweredBy"),
        }
        await self.page_evaluate("""(options) => {window.WPPConfig = options;}""", options)

        self.isInjected = False
        try:
            # TODO:____
            if await self.inject_api():
                self.isInjected = True
                self.logger.info(f'{self.session}: wapi.js injected')
                await self.afterPageScriptInjected()
        except:
            traceback.print_exc()
            self.logger.info(f'{self.session}: wapi.js failed')

    async def _afterPageScriptInjectedHost(self):
        version = await self.getWAVersion()
        self.logger.info(f'{self.session}: WhatsApp WEB version: {version}')
        version = await self.getWAJSVersion()
        self.logger.info(f'{self.session}: WA-JS version: {version}')
        await self.page_evaluate("""() => {WPP.on('conn.auth_code_change', window.checkQrCode);}""")
        await self.page_evaluate("""() => {WPP.on('conn.main_ready', window.checkInChat);}""")
        await self.__checkQrCode()
        await self.__checkInChat()

    async def start(self):
        try:
            if self.isStarted:
                return

            self.isStarted = True
            # ToDo:
            await self.initWhatsapp()
            await self.page.expose_function('checkQrCode', self.__checkQrCode)
            await self.page.expose_function('checkInChat', self.__checkInChat)

            # ToDo:
            # self.checkStartInterval = self.__setInterval(self.__checkStart, 5)
            # self.page.on('close', lambda: print("close"))
            # self.page.on('close', lambda: self.clearInterval(self.checkStartInterval))
            return True
        except:
            # traceback.print_exc()
            print("failed start")

    async def initWhatsapp(self):
        try:
            self.logger.info(f'{self.session}: Loading WhatsApp WEB')
            await self.page.goto(whatsappUrl, wait_until="domcontentloaded")
            self.logger.info(f'{self.session}: WhatsApp WEB loaded')
            # ToDo: unregisterServiceWorker, setWhatsappVersion,
            return self.page
        except:
            traceback.print_exc()

    async def __checkStart(self):
        # print("__checkStart")
        need_scan = await self.__needsToScan()
        # print(need_scan)

    async def __checkQrCode(self):
        need_scan = await self.__needsToScan()
        self.isLogged = not need_scan
        if not need_scan:
            self.attempt = 0
            return

        result = await self.__getQrCode()
        if not result or not result.get("urlCode") or self.urlCode == result.get("urlCode"):
            return

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

    async def __checkInChat(self):
        in_chat = await self.isInsideChat()
        self.isInChat = in_chat
        if not in_chat:
            return

        self.logger.info(f'{self.session}: http => Connected')
        self.statusFind('inChat', self.session)

    async def tryAutoClose(self):
        if self.autoCloseInterval:
            self.cancelAutoClose()

        if (self.autoClose > 0 or self.options.get(
                "deviceSyncTimeout") > 0) and not self.autoCloseInterval and not self.page.is_closed():
            self.logger.info(f'{self.session}: Closing the page')
            self.autoCloseCalled = True
            self.statusFind('autocloseCalled', self.session)
            try:
                if not self.page.is_closed():
                    await self.page.close()
            except:
                # traceback.print_exc()
                pass

    def startAutoClose(self, time=None):
        if not time:
            time = self.autoClose

        if time > 0 and not self.autoCloseInterval:
            seconds = round(time / 1000)
            self.logger.info(f'{self.session}: Auto close configured to {seconds}s')
            self.remain = seconds

            self.autoCloseInterval = self.__setInterval(self.autoCloseIntervalHandel, 5)

    def __setInterval(self, func, interval, *args, **kwargs):
        stopped = asyncio.Event()
        loop = kwargs.get('loop') or asyncio.get_event_loop()

        async def loop_():
            while not stopped.is_set():
                await func()
                await asyncio.sleep(interval)

        loop.create_task(loop_())
        return stopped

    def clearInterval(self, Interval):
        try:
            if Interval:
                Interval.set()
                print("Interval", Interval.is_set())
                # Interval.clear()
        except:
            traceback.print_exc()

    async def autoCloseIntervalHandel(self):
        # print("autoCloseIntervalHandel")
        if self.page.is_closed():
            self.cancelAutoClose()
            return
        self.remain -= 1
        if self.remain % 10 == 0 or self.remain <= 5:
            self.logger.info(f'{self.session}: http => Auto close remain: {self.remain}s')

        if self.remain <= 0:
            await self.tryAutoClose()

    def cancelAutoClose(self):
        self.clearInterval(self.autoCloseInterval)
        self.autoCloseInterval = None

    async def __getQrCode(self):
        qr_result = await self.scrapeImg()
        return qr_result

    async def waitForQrCodeScan(self):
        if not self.isStarted:
            raise Exception('waitForQrCodeScan error: Session not started')
        while not self.page.is_closed() and not self.isLogged:
            await sleep(200 / 1000)
            needScan = await self.__needsToScan()
            self.isLogged = not needScan

    async def waitForInChat(self):
        if not self.isStarted:
            raise Exception('waitForInChat error: Session not started')

        if not self.isLogged:
            return False

        start = datetime.now()
        while not self.page.is_closed() and self.isLogged and not self.isInChat:
            if 0 < self.options.get("deviceSyncTimeout") <= (datetime.now() - start).seconds:
                return False

            await sleep(1)

            inChat = await self.isInsideChat()
            self.isInChat = inChat

        return self.isInChat

    # @unsync
    async def waitForPageLoad(self):
        while not self.isInjected:
            await sleep(.2)
            # print("waitForPageLoad")
        await self.page_wait_for_function("() => WPP.isReady")

    async def waitForLogin(self):
        self.logger.info(f'{self.session}: http => Waiting page load')
        await self.waitForPageLoad()
        self.logger.info(f'{self.session}: http => Checking is logged...')
        authenticated = await self.isAuthenticated()
        self.startAutoClose()
        if authenticated is False:
            self.logger.info(f'{self.session}: http => Waiting for QRCode Scan...')
            self.statusFind('notLogged', self.session)
            await self.waitForQrCodeScan()
            self.logger.info(f'{self.session}: http => Checking QRCode status...')
            # // Wait for interface update
            await sleep(.2)
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
            # Reset the autoclose counter
            self.cancelAutoClose()
            #  Wait for interface update
            await sleep(.2)
            self.startAutoClose(self.options.get("deviceSyncTimeout"))

            self.logger.info(f'{self.session}: http => Checking phone is connected...')
            inChat = await self.waitForInChat()
            if not inChat:
                self.logger.warn(f'{self.session}: http => Phone not connected')
                self.statusFind('phoneNotConnected', self.session)
                await self.tryAutoClose()
                raise Exception("Phone not connected")
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

        if self.page.is_closed():
            self.logger.error(f'{self.session}: Page Closed')
            raise Exception("Page Closed")

        self.logger.error(f'{self.session}: Unknow error')
        raise Exception("Unknow error")

    async def getHostDevice(self):
        """@returns Current host device details"""
        return await self.page_evaluate("() => WAPI.getHost()")

    async def getWid(self):
        """@returns Current wid connected"""
        return await self.page_evaluate("() => WAPI.getWid()")

    async def getWAVersion(self):
        """Retrieves WA version"""
        await self.page_wait_for_function("() => WAPI.getWAVersion()")
        return await self.page_evaluate("() => WAPI.getWAVersion()")

    async def getWAJSVersion(self):
        await self.page_wait_for_function("() => WPP.version")
        return await self.page_evaluate("() => WPP.version")

    async def getConnectionState(self):
        return await self.page_evaluate("() => {return WPP.whatsapp.Socket.state;}")

    async def isConnected(self):
        """Retrieves if the phone is online. Please note that this may not be real time."""
        return await self.page_evaluate("() => WAPI.isConnected()")

    async def isLoggedIn(self):
        return await self.page_evaluate("() => WAPI.isLoggedIn()")

    async def getBatteryLevel(self):
        return await self.page_evaluate("() => WAPI.getBatteryLevel()")

    async def startPhoneWatchdog(self, interval=15000):
        return await self.page_evaluate("(interval) => WAPI.startPhoneWatchdog(interval)", interval)

    async def stopPhoneWatchdog(self):
        return await self.page_evaluate("() => WAPI.stopPhoneWatchdog()")

    async def isMultiDevice(self):
        return await self.page_evaluate("() => WPP.conn.isMultiDevice()")

    async def isAuthenticated(self):

        return await self.page_evaluate("() => WPP.conn.isRegistered()")

    async def __needsToScan(self):
        return not await self.isAuthenticated()

    def asciiQr(self, code):
        return pyqrcode.create(code).terminal(quiet_zone=1)

    async def scrapeImg(self):
        click = await self.page_evaluate("""() => {
              const selectorImg = document.querySelector('canvas');
              const selectorUrl = selectorImg.closest('[data-ref]');
              //const buttonReload = selectorUrl.querySelector('[role="button"]') as HTMLButtonElement;
              const buttonReload = selectorUrl.querySelector('button');
              if (buttonReload != null) {
                buttonReload.click();
                return true;
              }
              return false;
            }""")
        if click:
            await self.page_wait_for_function("""() => {
              const selectorImg = document.querySelector('canvas');
              const selectorUrl = selectorImg.closest('[data-ref]');
              return selectorUrl.getAttribute('data-ref');
            }""")

        result = await self.page_evaluate("""() => {
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
            }""")
        return result

    async def isInsideChat(self):
        result = await self.page_evaluate("() => WPP.conn.isMainReady()")
        return result if result else False

    async def inject_api(self):
        # {"percent": int, "message": str}
        try:
            injected = await self.page_evaluate("""() => {
                        return (typeof window.WAPI !== 'undefined' &&typeof window.Store !== 'undefined');}"""
                                                )
            if injected:
                print("- already injected ")
                return

            print(injected)
            await self.page_evaluate("() => (window?.webpackChunkwhatsapp_web_client?.length || 0) > 3")
            await self.page_wait_for_function("() => (window?.webpackChunkwhatsapp_web_client?.length || 0) > 3")
            await sleep(1)
            await self.page.add_script_tag(
                url="https://github.com/wppconnect-team/wa-js/releases/download/nightly/wppconnect-wa.js")
            await self.page_wait_for_function("() => window.WPP?.isReady")
            await self.page_evaluate("""() => {
                                  WPP.chat.defaultSendMessageOptions.createChat = true;
                                  WPP.conn.setKeepAlive(true);
                                }""")
            base_dir = Path(__file__).resolve().parent.parent.parent
            await self.page.add_script_tag(path=os.path.join(base_dir, 'js_lib/wapi.js'))
            await self._onLoadingScreen()
            # Make sure WAPI is initialized
            await self.page_wait_for_function("""() => {
            return (typeof window.WAPI !== 'undefined' && typeof window.Store !== 'undefined' && window.WPP.isReady);
            }""")
            return True
        except:
            print("- failed Inject ")
            traceback.print_exc()

    def loadingScreen(self, percent, message):
        print("loadingScreen", percent, message)
        if self.lastPercent != percent or self.lastPercentMessage != message:
            self.onLoadingScreen(percent, message)
            self.lastPercent = percent
            self.lastPercentMessage = message

    async def _onLoadingScreen(self):
        await self.page_evaluate("""function getElementByXpath(path) {
        return document.evaluate(path, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
            }""")
        try:
            await self.page.expose_function('loadingScreen', self.loadingScreen)
        except:
            # Function "loadingScreen" has been already registered
            pass
        await self.page_evaluate("""
        function (selectors) {
              let observer = new MutationObserver(function () {
                let window2 = window;

                let progressBar = window2.getElementByXpath(selectors.PROGRESS);
                let progressMessage = window2.getElementByXpath(
                  selectors.PROGRESS_MESSAGE
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
                                     "PROGRESS_MESSAGE": "//*[@id='app']/div/div/div[3]",
                                 })

    @staticmethod
    def valid_chatId(chatId):
        if chatId and (not chatId.endswith('@c.us') and not chatId.endswith('@g.us')):
            chatId += '@g.us' if len(chatId) > 15 else '@c.us'
        return chatId

    async def close(self):
        if not self.page.is_closed():
            await self.page.close()
        try:
            await self.browser.close()
        except:
            pass
