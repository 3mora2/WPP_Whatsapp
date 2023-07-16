from WPP_Whatsapp.api.layers.GroupLayer import GroupLayer


class UILayer(GroupLayer):

    def openChat(self, chatId):
        """
        Opens given chat at last message (bottom)
        Will fire natural workflow events of whatsapp web
        @category UI
        @param chatId
        """
        chatId = self.valid_chatId(chatId)
        return self.ThreadsafeBrowser.sync_page_evaluate("(chatId) => WPP.chat.openChatBottom(chatId)", chatId)

    def openChatAt(self, chatId, messageId):
        """
        Opens chat at given message position
        @category UI
        @param chatId Chat id
        @param messageId Message id (For example: '06D3AB3D0EEB9D077A3F9A3EFF4DD030')
        """
        chatId = self.valid_chatId(chatId)
        return self.ThreadsafeBrowser.sync_page_evaluate("({chatId, messageId}) => WPP.chat.openChatAt(chatId, messageId)",
                                                    {"chatId": chatId, "messageId": messageId})

    def getActiveChat(self):
        """
        Return the current active chat
        @category UI
        """
        return self.ThreadsafeBrowser.sync_page_evaluate("() => WPP.chat.getActiveChat()")
