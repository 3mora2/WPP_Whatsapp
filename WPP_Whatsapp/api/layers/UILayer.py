from WPP_Whatsapp.api.layers.GroupLayer import GroupLayer


class UILayer(GroupLayer):

    def openChat(self, chatId):
        chatId = self.valid_chatId(chatId)
        return self.ThreadsafeBrowser.page_evaluate("(chatId) => WPP.chat.openChatBottom(chatId)", chatId)

    def openChatAt(self, chatId, messageId):
        chatId = self.valid_chatId(chatId)
        return self.ThreadsafeBrowser.page_evaluate("({chatId, messageId}) => WPP.chat.openChatAt(chatId, messageId)",
                                                    {"chatId": chatId, "messageId": messageId})
