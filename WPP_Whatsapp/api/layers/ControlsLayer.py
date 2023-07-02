from WPP_Whatsapp.api.layers.UILayer import UILayer


class ControlsLayer(UILayer):

    def unblockContact(self, contactId):
        contactId = self.valid_chatId(contactId)
        self.ThreadsafeBrowser.sync_page_evaluate("(contactId) => WPP.blocklist.unblockContact(contactId)", contactId)
        return True

    def blockContact(self, contactId):
        contactId = self.valid_chatId(contactId)
        self.ThreadsafeBrowser.sync_page_evaluate("(contactId) => WPP.blocklist.blockContact(contactId)", contactId)
        return True

    def markUnseenMessage(self, contactId):
        contactId = self.valid_chatId(contactId)
        self.ThreadsafeBrowser.sync_page_evaluate("(contactId) => WPP.chat.markIsUnread(contactId)", contactId)

    def deleteChat(self, chatId):
        chatId = self.valid_chatId(chatId)
        result = self.ThreadsafeBrowser.sync_page_evaluate("(chatId) => WPP.chat.delete(chatId)", chatId)
        return result and result.get("status") == 200

    def archiveChat(self, chatId, option=True):
        chatId = self.valid_chatId(chatId)
        return self.ThreadsafeBrowser.sync_page_evaluate("({ chatId, option }) => WPP.chat.archive(chatId, option)",
                                        {"chatId": chatId, "option": option})

    def pinChat(self, chatId, option, nonExistent=False):
        chatId = self.valid_chatId(chatId)
        if nonExistent:
            self.ThreadsafeBrowser.sync_page_evaluate("({ chatId }) => WPP.chat.find(chatId)", chatId)

        return self.ThreadsafeBrowser.sync_page_evaluate("({ chatId, option }) => WPP.chat.pin(chatId, option)",
                                        {"chatId": chatId, "option": option})

    def starMessage(self, messagesId, star=True):
        self.ThreadsafeBrowser.sync_page_evaluate("({ messagesId, star }) => WAPI.starMessages(messagesId, star)",
                                 {"messagesId": messagesId, "star": star})
