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

    ######################################
    async def unblockContact_(self, contactId):
        contactId = self.valid_chatId(contactId)
        await self.ThreadsafeBrowser.page_evaluate("(contactId) => WPP.blocklist.unblockContact(contactId)", contactId)
        return True

    async def blockContact_(self, contactId):
        contactId = self.valid_chatId(contactId)
        await self.ThreadsafeBrowser.page_evaluate("(contactId) => WPP.blocklist.blockContact(contactId)", contactId)
        return True

    async def markUnseenMessage_(self, contactId):
        contactId = self.valid_chatId(contactId)
        await self.ThreadsafeBrowser.page_evaluate("(contactId) => WPP.chat.markIsUnread(contactId)", contactId)

    async def deleteChat_(self, chatId):
        chatId = self.valid_chatId(chatId)
        result = await self.ThreadsafeBrowser.page_evaluate("(chatId) => WPP.chat.delete(chatId)", chatId)
        return result and result.get("status") == 200

    async def archiveChat_(self, chatId, option=True):
        chatId = self.valid_chatId(chatId)
        return await self.ThreadsafeBrowser.page_evaluate("({ chatId, option }) => WPP.chat.archive(chatId, option)",
                                        {"chatId": chatId, "option": option})

    async def pinChat_(self, chatId, option, nonExistent=False):
        chatId = self.valid_chatId(chatId)
        if nonExistent:
            await self.ThreadsafeBrowser.page_evaluate("({ chatId }) => WPP.chat.find(chatId)", chatId)

        return await self.ThreadsafeBrowser.page_evaluate("({ chatId, option }) => WPP.chat.pin(chatId, option)",
                                        {"chatId": chatId, "option": option})

    async def starMessage_(self, messagesId, star=True):
        await self.ThreadsafeBrowser.page_evaluate("({ messagesId, star }) => WAPI.starMessages(messagesId, star)",
                                 {"messagesId": messagesId, "star": star})
