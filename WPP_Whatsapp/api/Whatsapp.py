import threading
import time

from WPP_Whatsapp.api.layers.HostLayer import HostLayer
from WPP_Whatsapp.api.const import defaultOptions, Logger
from WPP_Whatsapp.api.layers.BusinessLayer import BusinessLayer
from WPP_Whatsapp.api.layers.ListenerLayer import ListenerLayer


class Whatsapp(BusinessLayer):
    interval: threading.Event

    def __init__(self, session, threadsafe_browser, **kwargs):
        self.connected = None
        self.options = {}
        self.options.update(defaultOptions)
        for key, value in kwargs.items():
            if key in self.options:
                self.options[key] = value

        # self.autoCloseInterval = None
        self.autoCloseCalled = False
        self.isInitialized = False
        self.isInjected = False
        self.isStarted = False
        self.isLogged = False
        self.isInChat = False
        # self.checkStartInterval = None
        self.urlCode = ''
        self.status = ''
        self.attempt = 0
        self.lastPercent = ""
        self.lastPercentMessage = ""
        self.session = session
        self.page = threadsafe_browser.page
        self.browser = threadsafe_browser.browser
        self.ThreadsafeBrowser = threadsafe_browser
        self.logger = self.options.get("logger") or Logger
        self.logger.info(f'{self.session}: Initializing...')
        self.logQR = kwargs.get("logQR") or False
        self.autoClose = kwargs.get("autoClose") or self.options.get("autoClose") or 60
        HostLayer.__init__(self)
        ListenerLayer.__init__(self)
        self.handel()

    def handel(self):
        # self.interval = None
        if self.page:
            self.interval = self.__setInterval(self.__intervalHandel, 60)
            self.page.on('close', lambda: self.clearInterval(self.interval))

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

    def __intervalHandel(self):
        # Add window, when WPP not  create yet
        newConnected = self.ThreadsafeBrowser.sync_page_evaluate("() => window.WPP && window.WPP.conn.isRegistered()")

        if newConnected is None or newConnected == self.connected:
            return
        self.connected = newConnected

        if not newConnected:
            self.logger.info(f'{self.session}: Session Unpaired')
            self.statusFind('disconnectedMobile', self.session)

    async def afterPageScriptInjected(self):
        await self._afterPageScriptInjectedHost()
        await self._afterPageScriptInjectedListener()
        is_authenticated = await self.ThreadsafeBrowser.page_evaluate("() => WPP.conn.isRegistered()")
        self.connected = is_authenticated

    def useHere(self, timeout=120):
        return self.ThreadsafeBrowser.run_threadsafe(self.useHere_,  timeout_=timeout)


    def logout(self, timeout=120):
        return self.ThreadsafeBrowser.run_threadsafe(self.logout_,  timeout_=timeout)

    def getMessageById(self, messageId, timeout=120):
        return self.ThreadsafeBrowser.run_threadsafe(self.getMessageById_, messageId, timeout_=timeout)

    def getMessages(self, chatId, params=None, timeout=120):
        """
        :param chatId:
        :param params: (count, id, direction)
        :return:
        """
        return self.ThreadsafeBrowser.run_threadsafe(self.getMessages_, chatId, params, timeout_=timeout)

    def rejectCall(self, callId, timeout=120):
        return self.ThreadsafeBrowser.run_threadsafe(self.rejectCall_, callId, timeout_=timeout)

    #############################
    async def useHere_(self):
        return await self.ThreadsafeBrowser.page_evaluate("() => WAPI.takeOver()")

    async def logout_(self):
        return await self.ThreadsafeBrowser.page_evaluate("() => WPP.conn.logout()")

    async def getMessageById_(self, messageId):
        return await self.ThreadsafeBrowser.page_evaluate("(messageId) => WAPI.getMessageById(messageId)", messageId)

    async def getMessages_(self, chatId, params=None):
        """
        :param chatId:
        :param params: (count, id, direction)
        :return:
        """
        if not params:
            params = {}
        chatId = self.valid_chatId(chatId)
        return await self.ThreadsafeBrowser.page_evaluate("({ chatId, params }) => WAPI.getMessages(chatId, params)",
                                                    {"chatId": chatId, "params": params})

    async def rejectCall_(self, callId):
        return await self.ThreadsafeBrowser.page_evaluate(
            "({callId}) => WPP.call.rejectCall(callId)", callId)
