import asyncio
from Whatsapp.api.layers.BusinessLayer import BusinessLayer


class Whatsapp(BusinessLayer):
    connected = None

    def __init__(self, session, browser, loop=None):
        self.session = session
        self.page = browser.page
        self.browser = browser.browser
        self.Browser = browser
        # asyncio.set_event_loop(loop)
        # self.loop = loop
        # self.page_evaluate = self.Browser.page_evaluate
        # self.page_evaluate = self.Browser.page_wait_for_function
        super().__init__()
        self.handel()

    def handel(self):
        self.interval = None
        if self.page:
            self.page.on('close', lambda: self.clearInterval(self.interval))

        # self.interval = self.__setInterval(self.__intervalHandel, 60)

    @staticmethod
    def __setInterval(func, interval, *args, **kwargs):
        loop = kwargs.get('loop') or asyncio.get_event_loop()
        stopped = asyncio.Event()

        async def loop_():
            while not stopped.is_set():
                func()
                # asyncio.sleep(interval)

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
        is_authenticated = await self.page_evaluate("() => WPP.conn.isRegistered()")
        self.connected = is_authenticated

    async def useHere(self):
        return self.page_evaluate("() => WAPI.takeOver()")

    async def logout(self):
        return self.page_evaluate("() => WPP.conn.logout()")

    async def getMessageById(self, messageId):
        return self.page_evaluate("(messageId) => WAPI.getMessageById(messageId)", messageId)

    async def getMessages(self, chatId, params={}):
        """
        :param chatId:
        :param params: (count, id, direction)
        :return:
        """
        chatId = self.valid_chatId(chatId)
        return self.page_evaluate("({ chatId, params }) => WAPI.getMessages(chatId, params)",
                                  {"chatId": chatId, "params": params})

    async def rejectCall(self, callId):
        return self.page_evaluate(
            "({callId}) => WPP.call.rejectCall(callId)", callId)