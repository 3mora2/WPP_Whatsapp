from WPP_Whatsapp.api.layers.GroupLayer import GroupLayer

from WPP_Whatsapp.core.sync_api import sync_wrapper


class UILayer(GroupLayer):

    @sync_wrapper("openChat_")
    def openChat(self, chatId, timeout=60):
        """
        Opens given chat at last message (bottom)
        Will fire natural workflow events of whatsapp web
        @category UI
        @param chatId
        """
        ...

    @sync_wrapper("openChatAt_")
    def openChatAt(self, chatId, messageId, timeout=60):
        """
        Opens chat at given message position
        @category UI
        @param chatId Chat id
        @param messageId Message id (For example: '06D3AB3D0EEB9D077A3F9A3EFF4DD030')
        """
        ...

    @sync_wrapper("closeChat_")
    def closeChat(self, timeout=60):
        """
          /**
           * Closes the currently opened chat (if any).
           * The boolean result reflects if there was any chat that got closed.
           * @category UI
           */
        """
        ...

    @sync_wrapper("getActiveChat_")
    def getActiveChat(self, timeout=60):
        """
        Return the current active chat
        @category UI
        """
        ...

    ################################################
    async def openChat_(self, chatId):
        """
        Opens given chat at last message (bottom)
        Will fire natural workflow events of whatsapp web
        @category UI
        @param chatId
        """
        chatId = await self.get_chat_id_(chatId)
        return await self._evaluate_js('UILayer.openChat_.0', chatId, page=self.page)

    async def openChatAt_(self, chatId, messageId):
        """
        Opens chat at given message position
        @category UI
        @param chatId Chat id
        @param messageId Message id (For example: '06D3AB3D0EEB9D077A3F9A3EFF4DD030')
        """
        chatId = await self.get_chat_id_(chatId)
        return await self._evaluate_js(
            'UILayer.openChatAt_.0',
            {"chatId": chatId, "messageId": messageId}, page=self.page)

    async def closeChat_(self):
        """
          /**
           * Closes the currently opened chat (if any).
           * The boolean result reflects if there was any chat that got closed.
           * @category UI
           */
        """
        return await self._evaluate_js('UILayer.closeChat_.0', page=self.page)

    async def getActiveChat_(self):
        """
        Return the current active chat
        @category UI
        """
        return await self._evaluate_js('UILayer.getActiveChat_.0', page=self.page)

    @sync_wrapper("getAutoDownloadSettings_")
    def getAutoDownloadSettings(self, timeout=60):
        """Get media auto-download settings."""
        ...

    async def getAutoDownloadSettings_(self):
        return await self._evaluate_js(
            'UILayer.getAutoDownloadSettings_.0', page=self.page)

    @sync_wrapper("setAutoDownloadSettings_")
    def setAutoDownloadSettings(self, settings, timeout=60):
        """Set media auto-download settings; WhatsApp reloads to apply them."""
        ...

    async def setAutoDownloadSettings_(self, settings):
        return await self._evaluate_js(
            'UILayer.setAutoDownloadSettings_.0', {"settings": settings}, page=self.page)
