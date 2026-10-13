from WPP_Whatsapp.api.layers.GroupLayer import GroupLayer


class UILayer(GroupLayer):

    def openChat(self, chatId, timeout=60):
        """
        Opens given chat at last message (bottom)
        Will fire natural workflow events of whatsapp web
        @category UI
        @param chatId
        """
        return self.ThreadsafeBrowser.run_threadsafe(self.openChat_, chatId, timeout_=timeout)

    def openChatAt(self, chatId, messageId, timeout=60):
        """
        Opens chat at given message position
        @category UI
        @param chatId Chat id
        @param messageId Message id (For example: '06D3AB3D0EEB9D077A3F9A3EFF4DD030')
        """
        return self.ThreadsafeBrowser.run_threadsafe(self.openChatAt_, chatId, messageId, timeout_=timeout)

    def closeChat(self, timeout=60):
        """
          /**
           * Closes the currently opened chat (if any).
           * The boolean result reflects if there was any chat that got closed.
           * @category UI
           */
        """
        return self.ThreadsafeBrowser.run_threadsafe(self.closeChat_, timeout_=timeout)

    def getActiveChat(self, timeout=60):
        """
        Return the current active chat
        @category UI
        """
        return self.ThreadsafeBrowser.run_threadsafe(self.getActiveChat_,  timeout_=timeout)

    ################################################
    async def openChat_(self, chatId):
        """
        Opens given chat at last message (bottom)
        Will fire natural workflow events of whatsapp web
        @category UI
        @param chatId
        """
        chatId = await self.get_chat_id_(chatId)
        return await self.ThreadsafeBrowser.page_evaluate("(chatId) => WPP.chat.openChatBottom(chatId, undefined)", chatId, page=self.page)

    async def openChatAt_(self, chatId, messageId):
        """
        Opens chat at given message position
        @category UI
        @param chatId Chat id
        @param messageId Message id (For example: '06D3AB3D0EEB9D077A3F9A3EFF4DD030')
        """
        chatId = await self.get_chat_id_(chatId)
        return await self.ThreadsafeBrowser.page_evaluate(
            "({chatId, messageId}) => WPP.chat.openChatAt(chatId, messageId, undefined)",
            {"chatId": chatId, "messageId": messageId}, page=self.page)

    async def closeChat_(self):
        """
          /**
           * Closes the currently opened chat (if any).
           * The boolean result reflects if there was any chat that got closed.
           * @category UI
           */
        """
        return await self.ThreadsafeBrowser.page_evaluate("() => WPP.chat.closeChat()", page=self.page)

    async def getActiveChat_(self):
        """
        Return the current active chat
        @category UI
        """
        return await self.ThreadsafeBrowser.page_evaluate("() => WPP.chat.getActiveChat()", page=self.page)

    def getAutoDownloadSettings(self, timeout=60):
        """Get media auto-download settings."""
        return self.ThreadsafeBrowser.run_threadsafe(self.getAutoDownloadSettings_, timeout_=timeout)

    async def getAutoDownloadSettings_(self):
        return await self.ThreadsafeBrowser.page_evaluate(
            "() => WPP.conn.getAutoDownloadSettings()", page=self.page)

    def setAutoDownloadSettings(self, settings, timeout=60):
        """Set media auto-download settings; WhatsApp reloads to apply them."""
        return self.ThreadsafeBrowser.run_threadsafe(self.setAutoDownloadSettings_, settings, timeout_=timeout)

    async def setAutoDownloadSettings_(self, settings):
        return await self.ThreadsafeBrowser.page_evaluate(
            "({settings}) => WPP.conn.setAutoDownloadSettings(settings)", {"settings": settings}, page=self.page)
