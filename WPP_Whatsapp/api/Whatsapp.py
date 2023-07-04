import asyncio
import inspect

from WPP_Whatsapp.api.layers.HostLayer import HostLayer
from WPP_Whatsapp.api.const import defaultOptions, Logger
from WPP_Whatsapp.api.layers.BusinessLayer import BusinessLayer
from WPP_Whatsapp.api.layers.ListenerLayer import ListenerLayer


class Whatsapp(BusinessLayer):
    connected = None

    def __init__(self, session, threadsafe_browser, *args, **kwargs):
        self.session = session
        self.page = threadsafe_browser.page
        self.browser = threadsafe_browser.browser
        self.ThreadsafeBrowser = threadsafe_browser
        # self.loop = kwargs.get("loop")  # or asyncio.new_event_loop()
        # if not self.loop:
        #     raise Exception("Not Add Loop")
        # asyncio.set_event_loop(self.loop)
        self.session = session
        self.options.update(defaultOptions)
        self.logger = self.options.get("logger") or Logger
        self.logger.info(f'{self.session}: Initializing...')
        self.logQR = kwargs.get("logQR") or False
        self.autoClose = kwargs.get("autoClose") or self.options.get("autoClose") or 0
        HostLayer.__init__(self)
        ListenerLayer.__init__(self)
        self.handel()

    def handel(self):
        self.interval = None
        if self.page:
            self.page.on('close', lambda: self.clearInterval(self.interval))

        self.interval = self.__setInterval(self.__intervalHandel, 60)

    @staticmethod
    def __setInterval(func, interval, *args, **kwargs):
        loop = kwargs.get('loop') or asyncio.get_event_loop()
        stopped = asyncio.Event()

        async def loop_():
            while not stopped.is_set():
                if inspect.iscoroutinefunction(func):
                    await func()
                    await asyncio.sleep(interval)
                else:
                    func()
                    await asyncio.sleep(interval)

        loop.create_task(loop_())
        return stopped

    async def __intervalHandel(self):
        newConnected = self.page_evaluate("() => WPP && WPP.conn.isRegistered()")

        if newConnected is None or newConnected == self.connected:
            return
        self.connected = newConnected

        if not newConnected:
            self.logger.info(f'{self.session}: Session Unpaired')
            # asyncio.sleep(1)
            self.statusFind('desconnectedMobile', self.session)

    async def afterPageScriptInjected(self):
        await self._afterPageScriptInjectedHost()
        await self._afterPageScriptInjectedListener()
        is_authenticated = await self.ThreadsafeBrowser.page_evaluate("() => WPP.conn.isRegistered()")
        self.connected = is_authenticated

    def useHere(self):
        return self.ThreadsafeBrowser.page_evaluate("() => WAPI.takeOver()")

    async def logout(self):
        return self.ThreadsafeBrowser.page_evaluate("() => WPP.conn.logout()")

    async def getMessageById(self, messageId):
        return self.ThreadsafeBrowser.page_evaluate("(messageId) => WAPI.getMessageById(messageId)", messageId)

    async def getMessages(self, chatId, params=None):
        """
        :param chatId:
        :param params: (count, id, direction)
        :return:
        """
        if not params:
            params = {}
        chatId = self.valid_chatId(chatId)
        return self.ThreadsafeBrowser.page_evaluate("({ chatId, params }) => WAPI.getMessages(chatId, params)",
                                                    {"chatId": chatId, "params": params})

    async def rejectCall(self, callId):
        return self.ThreadsafeBrowser.page_evaluate(
            "({callId}) => WPP.call.rejectCall(callId)", callId)
