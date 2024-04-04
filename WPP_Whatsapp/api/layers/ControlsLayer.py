from WPP_Whatsapp.api.layers.UILayer import UILayer


class ControlsLayer(UILayer):

    def unblockContact(self, contactId, timeout=60):
        return self.ThreadsafeBrowser.run_threadsafe(self.unblockContact_, contactId, timeout_=timeout)

    def blockContact(self, contactId, timeout=60):
        return self.ThreadsafeBrowser.run_threadsafe(self.blockContact_, contactId, timeout_=timeout)

    def markUnseenMessage(self, contactId, timeout=60):
        return self.ThreadsafeBrowser.run_threadsafe(self.markUnseenMessage_, contactId, timeout_=timeout)

    def deleteChat(self, chatId, timeout=60):
        return self.ThreadsafeBrowser.run_threadsafe(self.deleteChat_, chatId, timeout_=timeout)

    def archiveChat(self, chatId, option=True, timeout=60):
        return self.ThreadsafeBrowser.run_threadsafe(self.archiveChat_, chatId, option, timeout_=timeout)

    def pinChat(self, chatId, option, nonExistent=False, timeout=60):
        return self.ThreadsafeBrowser.run_threadsafe(self.pinChat_, chatId, option, nonExistent, timeout_=timeout)

    def starMessage(self, messagesId, star=True, timeout=60):
        return self.ThreadsafeBrowser.run_threadsafe(self.starMessage_, messagesId, star, timeout_=timeout)

    def clearChat(self, chatId: str, keepStarred=True, timeout=60):
        """
          /**
           * Deletes all messages of given chat
           * @category Chat
           * @param chatId
           * @param keepStarred Keep starred messages
           * @returns boolean
           */
        """
        return self.ThreadsafeBrowser.run_threadsafe(self.clearChat_, chatId, keepStarred, timeout_=timeout)

    def deleteMessage(self, chatId: str, messageId: list[str] | str, onlyLocal=False, deleteMediaInDevice=True,
                      timeout=60):
        """
          /**
           * Deletes message of given message id
           * @category Chat
           * @param chatId The chat id from which to delete the message.
           * @param messageId The specific message id of the message to be deleted
           * @param onlyLocal If it should only delete locally (message remains on the other recipienct's phone).
            Defaults to false.
           */
        """
        return self.ThreadsafeBrowser.run_threadsafe(self.deleteMessage_, chatId, messageId, onlyLocal,
                                                     deleteMediaInDevice, timeout_=timeout)

    async def editMessage(self, msgId: str, newText: str, options=None, timeout=60):
        if options is None:
            options = {}
        return self.ThreadsafeBrowser.run_threadsafe(self.editMessage_, msgId, newText, options, timeout_=timeout)

    async def setLimit(self, key, value: bool | int, timeout=60):
        return self.ThreadsafeBrowser.run_threadsafe(self.setLimit_, key, value, timeout_=timeout)

    ######################################
    async def unblockContact_(self, contactId):
        contactId = self.valid_chatId(contactId)
        await self.ThreadsafeBrowser.page_evaluate("(contactId) => WPP.blocklist.unblockContact(contactId)", contactId, page=self.page)
        return True

    async def blockContact_(self, contactId):
        contactId = self.valid_chatId(contactId)
        await self.ThreadsafeBrowser.page_evaluate("(contactId) => WPP.blocklist.blockContact(contactId)", contactId, page=self.page)
        return True

    async def markUnseenMessage_(self, contactId):
        contactId = self.valid_chatId(contactId)
        await self.ThreadsafeBrowser.page_evaluate("(contactId) => WPP.chat.markIsUnread(contactId)", contactId, page=self.page)

    async def deleteChat_(self, chatId):
        chatId = self.valid_chatId(chatId)
        result = await self.ThreadsafeBrowser.page_evaluate("(chatId) => WPP.chat.delete(chatId)", chatId, page=self.page)
        return result and result.get("status") == 200

    async def archiveChat_(self, chatId, option=True):
        chatId = self.valid_chatId(chatId)
        return await self.ThreadsafeBrowser.page_evaluate("({ chatId, option }) => WPP.chat.archive(chatId, option)",
                                                          {"chatId": chatId, "option": option}, page=self.page)

    async def pinChat_(self, chatId, option, nonExistent=False):
        chatId = self.valid_chatId(chatId)
        if nonExistent:
            await self.ThreadsafeBrowser.page_evaluate("({ chatId }) => WPP.chat.find(chatId)", chatId, page=self.page)

        return await self.ThreadsafeBrowser.page_evaluate("({ chatId, option }) => WPP.chat.pin(chatId, option)",
                                                          {"chatId": chatId, "option": option}, page=self.page)

    async def clearChat_(self, chatId: str, keepStarred=True):
        """
          /**
           * Deletes all messages of given chat
           * @category Chat
           * @param chatId
           * @param keepStarred Keep starred messages
           * @returns boolean
           */
        """

        result = await self.ThreadsafeBrowser.page_evaluate(
            "({ chatId, keepStarred }) => WPP.chat.clear(chatId, keepStarred)",
            {"chatId": chatId, "keepStarred": keepStarred}, page=self.page)

        return result.get("status") == 200

    async def deleteMessage_(self, chatId: str, messageId: list[str] | str, onlyLocal=False, deleteMediaInDevice=True):
        """
          /**
           * Deletes message of given message id
           * @category Chat
           * @param chatId The chat id from which to delete the message.
           * @param messageId The specific message id of the message to be deleted
           * @param onlyLocal If it should only delete locally (message remains on the other recipienct's phone).
            Defaults to false.
           */
        """
        await self.ThreadsafeBrowser.page_evaluate(
            """({ chatId, messageId, onlyLocal, deleteMediaInDevice }) => WPP.chat.deleteMessage(
            chatId,messageId,deleteMediaInDevice,!onlyLocal
            )""",
            {"chatId": chatId, "messageId": messageId, "onlyLocal": onlyLocal,
             "deleteMediaInDevice": deleteMediaInDevice}, page=self.page)
        return True

    async def editMessage_(self, msgId: str, newText: str, options=None):
        if options is None:
            options = {}
        editResult = await self.ThreadsafeBrowser.page_evaluate(
            "({ msgId, newText, options }) =>  WPP.chat.editMessage(msgId, newText, options)",
            {"msgId": msgId, "newText": newText, "options": options}, page=self.page
        )
        result = await self.ThreadsafeBrowser.page_evaluate(
            "async ({ messageId }) => { return JSON.parse(JSON.stringify(await WAPI.getMessageById(messageId)));}",
            {"messageId": editResult.get("id")}, page=self.page
        )
        if result.get("body") != newText:
            raise Exception(editResult)

        return result

    async def starMessage_(self, messagesId, star=True):
        return await self.ThreadsafeBrowser.page_evaluate("({ messagesId, star }) => WAPI.starMessages(messagesId, star)",
                                                   {"messagesId": messagesId, "star": star}, page=self.page)

    async def setLimit_(self, key, value: bool | int):
        return await self.ThreadsafeBrowser.page_evaluate(
            "({ key, value }) => WPP.conn.setLimit(key as any, value)",
            {"key": key, "value": value}, page=self.page
        )
