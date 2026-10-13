from __future__ import annotations

from WPP_Whatsapp.api.layers.UILayer import UILayer

from WPP_Whatsapp.core.sync_api import sync_wrapper


class ControlsLayer(UILayer):

    @sync_wrapper("unblockContact_")
    def unblockContact(self, contactId, timeout=60):
        ...

    @sync_wrapper("blockContact_")
    def blockContact(self, contactId, timeout=60):
        ...

    @sync_wrapper("markUnseenMessage_")
    def markUnseenMessage(self, contactId, timeout=60):
        ...

    @sync_wrapper("deleteChat_")
    def deleteChat(self, chatId, timeout=60):
        ...

    @sync_wrapper("archiveChat_")
    def archiveChat(self, chatId, option=True, timeout=60):
        ...

    @sync_wrapper("pinChat_")
    def pinChat(self, chatId, option, nonExistent=False, timeout=60):
        ...

    @sync_wrapper("starMessage_")
    def starMessage(self, messagesId, star=True, timeout=60):
        ...

    @sync_wrapper("clearChat_")
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
        ...

    @sync_wrapper("deleteMessage_")
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
        ...

    def editMessage(self, msgId: str, newText: str, options=None, timeout=60):
        if options is None:
            options = {}
        return self.ThreadsafeBrowser.run_threadsafe(self.editMessage_, msgId, newText, options, timeout_=timeout)

    @sync_wrapper("setLimit_")
    def setLimit(self, key, value: bool | int, timeout=60):
        ...

    ######################################
    async def unblockContact_(self, contactId):
        contactId = self.valid_chatId(contactId)
        await self._evaluate_js('ControlsLayer.unblockContact_.0', contactId, page=self.page)
        return True

    async def blockContact_(self, contactId):
        contactId = self.valid_chatId(contactId)
        await self._evaluate_js('ControlsLayer.blockContact_.0', contactId, page=self.page)
        return True

    async def markUnseenMessage_(self, contactId):
        contactId = self.valid_chatId(contactId)
        await self._evaluate_js('ControlsLayer.markUnseenMessage_.0', contactId, page=self.page)

    async def deleteChat_(self, chatId):
        chatId = self.valid_chatId(chatId)
        result = await self._evaluate_js('ControlsLayer.deleteChat_.0', chatId, page=self.page)
        return result and result.get("status") == 200

    async def archiveChat_(self, chatId, option=True):
        chatId = self.valid_chatId(chatId)
        return await self._evaluate_js('ControlsLayer.archiveChat_.0',
                                                          {"chatId": chatId, "option": option}, page=self.page)

    async def pinChat_(self, chatId, option, nonExistent=False):
        chatId = self.valid_chatId(chatId)
        if nonExistent:
            await self._evaluate_js('ControlsLayer.pinChat_.1', chatId, page=self.page)

        return await self._evaluate_js('ControlsLayer.pinChat_.0',
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

        chatId = self.valid_chatId(chatId)
        result = await self._evaluate_js(
            'ControlsLayer.clearChat_.0',
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
        chatId = self.valid_chatId(chatId)
        await self._evaluate_js(
            'ControlsLayer.deleteMessage_.0',
            {"chatId": chatId, "messageId": messageId, "onlyLocal": onlyLocal,
             "deleteMediaInDevice": deleteMediaInDevice}, page=self.page)
        return True

    async def editMessage_(self, msgId: str, newText: str, options=None):
        if options is None:
            options = {}
        editResult = await self._evaluate_js(
            'ControlsLayer.editMessage_.0',
            {"msgId": msgId, "newText": newText, "options": options}, page=self.page
        )
        result = await self._evaluate_js(
            'ControlsLayer.editMessage_.1',
            {"messageId": editResult.get("id")}, page=self.page
        )
        if result.get("body") != newText:
            raise Exception(editResult)

        return result

    async def starMessage_(self, messagesId, star=True):
        return await self._evaluate_js('ControlsLayer.starMessage_.0',
                                                   {"messagesId": messagesId, "star": star}, page=self.page)

    async def setLimit_(self, key, value: bool | int):
        return await self._evaluate_js(
            'ControlsLayer.setLimit_.0',
            {"key": key, "value": value}, page=self.page
        )

    @sync_wrapper("setTemporaryMessages_")
    def setTemporaryMessages(self, chatId, value, timeout=60):
        """Enable or disable temporary messages."""
        ...

    async def setTemporaryMessages_(self, chatId, value):
        chatId = self.valid_chatId(chatId)
        return await self._evaluate_js(
            'ControlsLayer.setTemporaryMessages_.0', {"chatId": chatId, "value": value}, page=self.page)
