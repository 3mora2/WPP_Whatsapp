from __future__ import annotations

import asyncio
from threading import Event

from WPP_Whatsapp.api.const import defaultOptions, Logger
from WPP_Whatsapp.api.helpers.jsFunction import setInterval
from WPP_Whatsapp.api.layers.BusinessLayer import BusinessLayer
from WPP_Whatsapp.api.layers.HostLayer import HostLayer
from WPP_Whatsapp.api.layers.ListenerLayer import ListenerLayer
from WPP_Whatsapp.core.compat import install_compatibility
from WPP_Whatsapp.core.options import validate_options


class Whatsapp:
    interval: Event

    def diagnostics(self):
        """Return an allowlisted support report without message or profile data."""
        from WPP_Whatsapp.core.diagnostics import snapshot
        return snapshot(self.lifecycle.state, self)

    def __init__(self, session, threadsafe_browser, page, loop=None, version=None, wa_js_version=None, **kwargs):
        kwargs = validate_options(kwargs)
        self.connected = None
        self.options = {}
        self.options.update(defaultOptions)
        self.options.update(kwargs)
        # for key, value in kwargs.items():
        #     if key in self.options:
        #         self.options[key] = value
        # self.autoCloseInterval = None
        self.version = version  # or self.options.get('whatsappVersion')
        self.wa_js_version = wa_js_version
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

        self.page = page
        self.ThreadsafeBrowser = threadsafe_browser
        self.loop = loop or self.ThreadsafeBrowser.loop

        self.logger = self.options.get("logger") or Logger
        self.logger.info(f'{self.session}: Initializing...')
        self.logQR = kwargs.get("logQR") or False
        self.autoClose = kwargs.get("autoClose", self.options.get("autoClose", 60))
        if self.autoClose is None:
            self.autoClose = 60
        HostLayer.__init__(self)
        ListenerLayer.__init__(self)
        self.handel()

    def handel(self):
        # self.interval = None
        if self.page:
            self.interval = setInterval(self.loop, self.__intervalHandel, 60)
            self.page.on('close', self.clear_all_interval)

    async def clear_all_interval(self, *args, **kwargs):
        Logger.info("clear all intervals")
        if hasattr(self, "interval"):
            self.clearInterval(self.interval)
        if hasattr(self, "autoCloseInterval"):
            self.clearInterval(self.autoCloseInterval)
        if hasattr(self, "checkStartInterval"):
            self.clearInterval(self.checkStartInterval)

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

    async def __intervalHandel(self):
        try:
            # Add window, when WPP not  create yet
            newConnected = await self._evaluate_js(
                'Whatsapp.__intervalHandel.0', page=self.page
            )
        except:
            newConnected = None

        if newConnected is None or newConnected == self.connected:
            return
        self.connected = newConnected

        if not newConnected:
            self.logger.info(f'{self.session}: Session Unpaired')
            if self.statusFind:
                self.statusFind('disconnectedMobile', self.session)

    async def afterPageScriptInjected(self):
        await self._afterPageScriptInjectedHost()
        await self._afterPageScriptInjectedListener()
        is_authenticated = await self._evaluate_js(
            'Whatsapp.afterPageScriptInjected.0', page=self.page)
        self.connected = is_authenticated

    def downloadFile(self, data: str, timeout=120):
        return self.ThreadsafeBrowser.run_threadsafe(self.downloadFile_, data, timeout_=timeout)

    def downloadMedia(self, messageId: str | dict, timeout=120):
        return self.ThreadsafeBrowser.run_threadsafe(self.downloadMedia_, messageId, timeout_=timeout)

    def takeScreenshot(self, timeout_=120, **kwargs):
        return self.ThreadsafeBrowser.run_threadsafe(self.takeScreenshot_, **kwargs, timeout_=timeout_)

    def useHere(self, timeout=120):
        return self.ThreadsafeBrowser.run_threadsafe(self.useHere_, timeout_=timeout)

    def logout(self, timeout=120):
        return self.ThreadsafeBrowser.run_threadsafe(self.logout_, timeout_=timeout)

    def getMessageById(self, messageId, timeout=120):
        return self.ThreadsafeBrowser.run_threadsafe(self.getMessageById_, messageId, timeout_=timeout)

    def getMessages(self, chatId, params=None, timeout=120):
        """
        :param chatId:
        :param params: (count, id, direction)
        :return:
        """
        return self.ThreadsafeBrowser.run_threadsafe(self.getMessages_(chatId, params), timeout_=timeout)

    def rejectCall(self, callId="", timeout=120):
        return self.ThreadsafeBrowser.run_threadsafe(self.rejectCall_(callId), timeout_=timeout)

    #############################
    async def downloadFile_(self, data: str):
        """
          /**
           * Decrypts message file
           * @param data Message object
           * @returns Decrypted file buffer (null otherwise)
           */
        """
        return await self._evaluate_js(
            'Whatsapp.downloadFile_.0', data,
            page=self.page)

    async def downloadMedia_(self, messageId: str | dict):
        """
          /**
           * Download and returns the media content in base64 format
           * @param messageId Message ou id
           * @returns Base64 of media
           */
        """
        if not isinstance(messageId, str):
            messageId = messageId.get("id")
        return await self._evaluate_js(
            'Whatsapp.downloadMedia_.0', messageId,
            page=self.page)

    async def takeScreenshot_(self, **kwargs):
        return await self.ThreadsafeBrowser.create_task(
            self.page.screenshot(**kwargs)
        )

    async def useHere_(self):
        return await self._evaluate_js('Whatsapp.useHere_.0', page=self.page)

    async def logout_(self):
        return await self._evaluate_js('Whatsapp.logout_.0', page=self.page)

    async def getMessageById_(self, messageId):
        return await self._evaluate_js('Whatsapp.getMessageById_.0', messageId,
                                                          page=self.page)

    async def getMessages_(self, chatId, params=None):
        """
        :param chatId:
        :param params: (count, id, direction)
        :return:
        """
        if not params:
            params = {}
        chatId = await self.get_chat_id_(chatId)
        return await self._evaluate_js('Whatsapp.getMessages_.0',
                                                          {"chatId": chatId, "params": params}, page=self.page)

    async def rejectCall_(self, callId=""):
        return await self._evaluate_js(
            'Whatsapp.rejectCall_.0', callId, page=self.page)

    # Context Manager Support
    def __enter__(self):
        """Context manager entry (sync)"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit (sync)"""
        self.close()

    async def __aenter__(self):
        """Context manager entry (async)"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit (async)"""
        await self.close_async()

    def close(self):
        """Close the session (sync)"""
        if getattr(self, '_closed_resources', False):
            return
        self._closed_resources = True
        self.isClosed = True
        for name in ('interval', 'autoCloseInterval', 'checkStartInterval'):
            interval = getattr(self, name, None)
            if interval is not None:
                interval.set()
        self.logger.info(f'{self.session}: Closing session...')
        if hasattr(self, 'ThreadsafeBrowser'):
            try:
                self.ThreadsafeBrowser.run_threadsafe(self._shutdown_session, timeout_=30)
            finally:
                if getattr(self, '_owns_transport', True):
                    self.ThreadsafeBrowser.sync_close()
                else:
                    self.ThreadsafeBrowser.run_threadsafe(self.page.context.close())

    async def close_async(self):
        """Close the session (async)"""
        if getattr(self, '_closed_resources', False):
            return
        self._closed_resources = True
        self.isClosed = True
        try:
            await self.ThreadsafeBrowser.create_task(self._shutdown_session())
        finally:
            self.logger.info(f'{self.session}: Closing session...')
            if getattr(self, '_owns_transport', True):
                await self.ThreadsafeBrowser.close()
            else:
                await self.ThreadsafeBrowser.create_task(self.page.context.close())

    async def _shutdown_session(self):
        if getattr(self, '_shutdown_done', False):
            return
        self._shutdown_done = True
        from WPP_Whatsapp.core.lifecycle import SessionState
        if hasattr(self, 'lifecycle') and self.lifecycle.state != SessionState.CLOSED:
            self.lifecycle.transition(SessionState.CLOSING)
        try:
            await self.close_listeners()
        finally:
            await self.clear_all_interval()
            tracker = getattr(self, '_delivery_tracker', None)
            if tracker is not None:
                await tracker.aclose()

    @property
    def async_services(self):
        from WPP_Whatsapp.core.services import ServiceHub
        if not hasattr(self, '_service_hub'):
            self._service_hub = ServiceHub(self)
        return self._service_hub

    @property
    def services(self):
        from WPP_Whatsapp.core.services import SyncServices
        return SyncServices(self.async_services)


install_compatibility(Whatsapp, BusinessLayer)
