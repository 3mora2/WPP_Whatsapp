import asyncio
import logging
import os
import threading
import time
from time import sleep
from datetime import datetime
from pathlib import Path
from playwright.async_api import Page
from WPP_Whatsapp.api.const import whatsappUrl
from WPP_Whatsapp.api.helpers.function import asciiQr
from WPP_Whatsapp.PlaywrightSafeThread import ThreadsafeBrowser


class HostLayer:
    page: Page
    session: str
    logger: logging
    ThreadsafeBrowser: "ThreadsafeBrowser"
    options: dict
    autoCloseInterval: threading.Event
    autoCloseCalled: bool
    isInitialized: bool
    isInjected: bool
    isStarted: bool
    isLogged: bool
    isInChat: bool
    urlCode: str
    status: str
    attempt: int
    lastPercent: str
    lastPercentMessage: str
    session: str
    autoClose: int
    checkStartInterval: threading.Event
    logQR: bool
    remain: int

    def __init__(self):
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

    async def on_close(self):
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
        self.logger.info(f'{self.session}: Start WPPConfig')
        await self.ThreadsafeBrowser.page_evaluate("""(options) => {window.WPPConfig = options;}""", options)
        # await self.ThreadsafeBrowser.page.page_evaluate("""(options) => {window.WPPConfig = options;}""", options)
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
        await self.ThreadsafeBrowser.page_evaluate("""() => {WPP.on('conn.auth_code_change', window.checkQrCode);}""")
        await self.ThreadsafeBrowser.page_evaluate("""() => {WPP.on('conn.main_ready', window.checkInChat);}""")
        await self.__checkQrCode()
        await self.__checkInChat()

    def start(self):
        if self.isStarted:
            return

        self.isStarted = True
        # ToDo:
        self.initWhatsapp()
        self.ThreadsafeBrowser.sync_expose_function('checkQrCode', self.__checkQrCode)
        self.ThreadsafeBrowser.sync_expose_function('checkInChat', self.__checkInChat)
        # ToDo:
        # self.checkStartInterval = self.__setInterval(self.__checkStart, 10)
        # self.page.on('close', lambda: self.clearInterval(self.checkStartInterval))
        return True

    def initWhatsapp(self):
        self.logger.info(f'{self.session}: Loading WhatsApp WEB')
        self.ThreadsafeBrowser.sync_goto(whatsappUrl, wait_until="domcontentloaded")
        self.logger.info(f'{self.session}: WhatsApp WEB loaded')
        # ToDo: unregisterServiceWorker, setWhatsappVersion,

    async def __checkStart(self):
        await self.__needsToScan()

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
            if not self.page.is_closed():
                await self.ThreadsafeBrowser.close()

    def sync_tryAutoClose(self):
        if self.autoCloseInterval:
            self.cancelAutoClose()

        if (self.autoClose > 0 or self.options.get(
                "deviceSyncTimeout") > 0) and not self.autoCloseInterval and not self.page.is_closed():
            self.logger.info(f'{self.session}: Closing the page')
            self.autoCloseCalled = True
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

            self.autoCloseInterval = self.__setInterval(self.autoCloseIntervalHandel, 5)

    @staticmethod
    def __setInterval(func, interval, *args, **kwargs):
        stopped = threading.Event()

        def _loop_():
            while not stopped.is_set():
                func()
                time.sleep(interval)

        th = threading.Thread(target=_loop_)
        th.start()
        return stopped

    def clearInterval(self, Interval):
        self.logger.debug(f'{self.session}: clearInterval {Interval}')
        if Interval:
            Interval.set()

    def autoCloseIntervalHandel(self):
        if self.page.is_closed():
            self.cancelAutoClose()
            return

        self.remain -= 1
        if self.remain % 10 == 0 or self.remain <= 5:
            self.logger.info(f'{self.session}: http => Auto close remain: {self.remain}s')

        if self.remain <= 0:
            self.sync_tryAutoClose()

    def cancelAutoClose(self):
        self.clearInterval(self.autoCloseInterval)
        # self.autoCloseInterval = None

    async def __getQrCode(self):
        qr_result = await self.scrapeImg()
        return qr_result

    def waitForQrCodeScan(self):
        if not self.isStarted:
            raise Exception('waitForQrCodeScan error: Session not started')
        while not self.page.is_closed() and not self.isLogged:
            # sleep(200 / 1000)
            self.ThreadsafeBrowser.sleep(200 / 1000)
            needScan = self.__sync_needsToScan()
            self.isLogged = not needScan

    def waitForInChat(self):
        if not self.isStarted:
            raise Exception('waitForInChat error: Session not started')

        if not self.isLogged:
            return False

        start = datetime.now()
        while not self.page.is_closed() and self.isLogged and not self.isInChat:
            if 0 < self.options.get("deviceSyncTimeout") <= (datetime.now() - start).seconds:
                return False

            sleep(1)

            inChat = self.sync_isInsideChat()
            self.isInChat = inChat

        return self.isInChat

    def waitForPageLoad(self):
        while not self.isInjected:
            sleep(.2)

        self.ThreadsafeBrowser.sync_page_wait_for_function("() => WPP.isReady")

    def waitForLogin(self):
        self.logger.info(f'{self.session}: http => Waiting page load')
        self.waitForPageLoad()
        self.logger.info(f'{self.session}: http => Checking is logged...')
        authenticated = self.sync_isAuthenticated()
        self.logger.debug(f'{self.session}: http => {authenticated=}')
        self.startAutoClose()
        if authenticated is False:
            self.logger.info(f'{self.session}: http => Waiting for QRCode Scan...')
            self.statusFind('notLogged', self.session)
            self.waitForQrCodeScan()
            self.logger.info(f'{self.session}: http => Checking QRCode status...')
            # // Wait for interface update
            sleep(.2)
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
            sleep(.2)
            self.startAutoClose(self.options.get("deviceSyncTimeout"))

            self.logger.info(f'{self.session}: http => Checking phone is connected...')
            inChat = self.waitForInChat()
            if not inChat:
                self.logger.warn(f'{self.session}: http => Phone not connected')
                self.statusFind('phoneNotConnected', self.session)
                self.sync_tryAutoClose()
                raise Exception("Phone not connected")
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

        if self.page.is_closed():
            self.logger.error(f'{self.session}: Page Closed')
            raise Exception("Page Closed")

        self.logger.error(f'{self.session}: Unknow error')
        raise Exception("Unknow error")

    def getHostDevice(self):
        """@returns Current host device details"""
        return self.ThreadsafeBrowser.sync_page_evaluate("() => WAPI.getHost()")

    def getWid(self):
        """@returns Current wid connected"""
        return self.ThreadsafeBrowser.sync_page_evaluate("() => WAPI.getWid()")

    async def getWAVersion(self):
        """Retrieves WA version"""
        await self.ThreadsafeBrowser.page_wait_for_function("() => WAPI.getWAVersion()")
        return await self.ThreadsafeBrowser.page_evaluate("() => WAPI.getWAVersion()")

    async def getWAJSVersion(self):
        await self.ThreadsafeBrowser.page_wait_for_function("() => WPP.version")
        return await self.ThreadsafeBrowser.page_evaluate("() => WPP.version")

    def getConnectionState(self):
        return self.ThreadsafeBrowser.sync_page_evaluate("() => {return WPP.whatsapp.Socket.state;}")

    def isConnected(self):
        """Retrieves if the phone is online. Please note that this may not be real time."""
        return self.ThreadsafeBrowser.sync_page_evaluate("() => WAPI.isConnected()")

    def isLoggedIn(self):
        return self.ThreadsafeBrowser.sync_page_evaluate("() => WAPI.isLoggedIn()")

    def getBatteryLevel(self):
        return self.ThreadsafeBrowser.sync_page_evaluate("() => WAPI.getBatteryLevel()")

    def startPhoneWatchdog(self, interval=15000):
        return self.ThreadsafeBrowser.sync_page_evaluate("(interval) => WAPI.startPhoneWatchdog(interval)", interval)

    def stopPhoneWatchdog(self):
        return self.ThreadsafeBrowser.sync_page_evaluate("() => WAPI.stopPhoneWatchdog()")

    def isMultiDevice(self):
        return self.ThreadsafeBrowser.sync_page_evaluate("() => WPP.conn.isMultiDevice()")

    async def isAuthenticated(self):
        try:
            return await self.ThreadsafeBrowser.page_evaluate("() => WPP.conn.isRegistered()")
        except Exception as e:
            self.logger.debug(e)
            return False

    def sync_isAuthenticated(self):
        try:
            return self.ThreadsafeBrowser.sync_page_evaluate("() => WPP.conn.isRegistered()")
        except Exception as e:
            self.logger.debug(e)
            return False

    async def __needsToScan(self):
        return not await self.isAuthenticated()

    def __sync_needsToScan(self):
        return not self.sync_isAuthenticated()

    @staticmethod
    def asciiQr(code):
        return asciiQr(code=code)

    async def scrapeImg(self):
        await self.ThreadsafeBrowser.page_wait_for_function("()=>document.querySelector('canvas')?.closest")
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
            }""")
        if click:
            await self.ThreadsafeBrowser.page_wait_for_function("""() => {
              const selectorImg = document.querySelector('canvas');
              const selectorUrl = selectorImg.closest('[data-ref]');
              return selectorUrl.getAttribute('data-ref');
            }""")

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
            }""")
        return result

    async def isInsideChat(self):
        result = await self.ThreadsafeBrowser.page_evaluate("() => WPP.conn.isMainReady()")
        return result if result else False

    def sync_isInsideChat(self):
        result = self.ThreadsafeBrowser.sync_page_evaluate("() => WPP.conn.isMainReady()")
        return result if result else False

    async def inject_api(self):
        self.logger.debug(f'{self.session}: start inject')
        injected = await self.ThreadsafeBrowser.page_evaluate("""() => {
                    return (typeof window.WAPI !== 'undefined' &&typeof window.Store !== 'undefined');}"""
                                                              )
        if injected:
            self.logger.info(f'{self.session}: already injected')
            return

        self.logger.info(f'{self.session}: injected state: {injected}')
        await self.ThreadsafeBrowser.page_evaluate("() => (window?.webpackChunkwhatsapp_web_client?.length || 0) > 3")
        await self.ThreadsafeBrowser.page_wait_for_function(
            "() => (window?.webpackChunkwhatsapp_web_client?.length || 0) > 3")
        await asyncio.sleep(1)
        await self.ThreadsafeBrowser.add_script_tag(
            url="https://github.com/wppconnect-team/wa-js/releases/download/nightly/wppconnect-wa.js")
        await self.ThreadsafeBrowser.page_wait_for_function("() => window.WPP?.isReady")
        await self.ThreadsafeBrowser.page_evaluate("""() => {
                              WPP.chat.defaultSendMessageOptions.createChat = true;
                              WPP.conn.setKeepAlive(true);
                            }""")
        base_dir = Path(__file__).resolve().parent.parent.parent
        await self.ThreadsafeBrowser.add_script_tag(path=os.path.join(base_dir, 'js_lib', 'wapi.js'))
        # await self.ThreadsafeBrowser.add_script_tag(
        #     url="https://raw.githubusercontent.com/3mora2/WPP_Whatsapp/main/WPP_Whatsapp/js_lib/wapi.js")
        await self._onLoadingScreen()
        # Make sure WAPI is initialized
        await self.ThreadsafeBrowser.page_wait_for_function("""() => {
        return (typeof window.WAPI !== 'undefined' && typeof window.Store !== 'undefined' && window.WPP.isReady);
        }""")
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
            }""")
        try:
            await self.ThreadsafeBrowser.expose_function('loadingScreen', self.loadingScreen)
        except:
            # Function "loadingScreen" has been already registered
            pass
        await self.ThreadsafeBrowser.page_evaluate("""
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
        chatId = chatId.replace("+", "")
        if chatId and (not chatId.endswith('@c.us') and not chatId.endswith('@g.us')):
            chatId += '@g.us' if len(chatId) > 15 else '@c.us'
        return chatId

    def close(self):
        self.ThreadsafeBrowser.sync_close()
