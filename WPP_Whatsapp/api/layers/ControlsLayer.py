from WPP_Whatsapp.api.layers.UILayer import UILayer


class ControlsLayer(UILayer):

    async def unblockContact(self, contactId):
        contactId = self.valid_chatId(contactId)
        await self.page_evaluate("(contactId) => WPP.blocklist.unblockContact(contactId)", contactId)
        return True

    async def blockContact(self, contactId):
        contactId = self.valid_chatId(contactId)
        await self.page_evaluate("(contactId) => WPP.blocklist.blockContact(contactId)", contactId)
        return True

    async def markUnseenMessage(self, contactId):
        contactId = self.valid_chatId(contactId)
        await self.page_evaluate("(contactId) => WPP.chat.markIsUnread(contactId)", contactId)

    async def deleteChat(self, chatId):
        chatId = self.valid_chatId(chatId)
        result = await self.page_evaluate("(chatId) => WPP.chat.delete(chatId)", chatId)
        return result and result.get("status") == 200

    async def archiveChat(self, chatId, option=True):
        chatId = self.valid_chatId(chatId)
        return await self.page_evaluate("({ chatId, option }) => WPP.chat.archive(chatId, option)",
                                        {"chatId": chatId, "option": option})

    async def pinChat(self, chatId, option, nonExistent=False):
        chatId = self.valid_chatId(chatId)
        if nonExistent:
            await self.page_evaluate("({ chatId }) => WPP.chat.find(chatId)", chatId)

        return await self.page_evaluate("({ chatId, option }) => WPP.chat.pin(chatId, option)",
                                        {"chatId": chatId, "option": option})

    async def starMessage(self, messagesId, star=True):
        await self.page_evaluate("({ messagesId, star }) => WAPI.starMessages(messagesId, star)",
                                 {"messagesId": messagesId, "star": star})
