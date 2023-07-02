from WPP_Whatsapp.api.layers.SenderLayer import SenderLayer


class RetrieverLayer(SenderLayer):
    def getSessionTokenBrowser(self, removePath):
        # @returns obj [token]
        if removePath:
            self.ThreadsafeBrowser.sync_page_evaluate("() => {window['pathSession'] = true;}")

        if self.isMultiDevice():
            return self.ThreadsafeBrowser.sync_page_evaluate("""() => {
          if (window.localStorage) {
            return {
              WABrowserId:
                window.localStorage.getItem('WABrowserId') || 'MultiDevice',
              WASecretBundle: 'MultiDevice',
              WAToken1: 'MultiDevice',
              WAToken2: 'MultiDevice',
            };
          }
          return null;
        }""")
        return self.ThreadsafeBrowser.sync_page_evaluate("""() => {
        if (window.localStorage) {
          return {
            WABrowserId: window.localStorage.getItem('WABrowserId'),
            WASecretBundle: window.localStorage.getItem('WASecretBundle'),
            WAToken1: window.localStorage.getItem('WAToken1'),
            WAToken2: window.localStorage.getItem('WAToken2'),
          };
        }
        return null;
      }""")

    def getTheme(self):
        # @returns string light or dark
        return self.ThreadsafeBrowser.sync_page_evaluate("() => WAPI.getTheme()")

    def getAllChats(self, withNewMessageOnly=False):
        # @returns array of [Chat]
        if withNewMessageOnly:
            return self.ThreadsafeBrowser.sync_page_evaluate("() => WAPI.getAllChatsWithNewMsg()")

        return self.ThreadsafeBrowser.sync_page_evaluate("() => WAPI.getAllChats()")

    def checkNumberStatus(self, contactId):
        # @returns contact detial as promise
        contactId = self.valid_chatId(contactId)
        return self.ThreadsafeBrowser.sync_page_evaluate("(contactId) => WAPI.checkNumberStatus(contactId)", contactId)

    def getAllChatsWithMessages(self, withNewMessageOnly=False):
        # @returns array of [Chat]
        return self.ThreadsafeBrowser.sync_page_evaluate("""(withNewMessageOnly: boolean) =>
        WAPI.getAllChatsWithMessages(withNewMessageOnly)""", withNewMessageOnly)

    def getAllGroups(self, withNewMessagesOnly):
        # @returns array of groups
        return self.ThreadsafeBrowser.sync_page_evaluate("""async ({ withNewMessagesOnly }) => {
        const chats = await WPP.chat.list({
          onlyGroups: true,
          onlyWithUnreadMessage: withNewMessagesOnly,
        });

        const groups = await Promise.all(
          chats.map((c) => WPP.group.ensureGroup(c.id))
        );

        return groups.map((g) => WAPI._serializeChatObj(g));
      }""", withNewMessagesOnly)

    def getAllBroadcastList(self):
        # @returns array of broadcast list
        chats = self.ThreadsafeBrowser.sync_page_evaluate("""() => WAPI.getAllChats()""")
        if chats:
            return list(
                filter(lambda x: x.get("isBroadcast") and x.get("id").get("_serialized") != 'status@broadcast', chats))

    def getContact(self, contactId):
        # @returns contact detial as promise
        contactId = self.valid_chatId(contactId)
        return self.ThreadsafeBrowser.sync_page_evaluate("(contactId) => WAPI.getContact(contactId)", contactId)

    def getAllContacts(self):
        # @returns array of [Contact]
        return self.ThreadsafeBrowser.sync_page_evaluate("() => WAPI.getAllContacts()")

    def getChatById(self, contactId):
        contactId = self.valid_chatId(contactId)
        return self.ThreadsafeBrowser.sync_page_evaluate("(contactId) => WAPI.getChatById(contactId)", contactId)

    def getChat(self, contactId):
        contactId = self.valid_chatId(contactId)
        return self.getChatById(contactId)

    def getProfilePicFromServer(self, chatId):
        # @returns url of the chat picture or undefined if there is no picture for the chat.
        chatId = self.valid_chatId(chatId)
        return self.ThreadsafeBrowser.sync_page_evaluate("(chatId) => WAPI._profilePicfunc(chatId)", chatId)

    def loadEarlierMessages(self, contactId):
        contactId = self.valid_chatId(contactId)
        return self.ThreadsafeBrowser.sync_page_evaluate("(contactId) => WAPI.loadEarlierMessages(contactId)", contactId)

    def getStatus(self, contactId):
        contactId = self.valid_chatId(contactId)
        return self.ThreadsafeBrowser.sync_page_evaluate("""async (contactId) => {
                                        const status = await WPP.contact.getStatus(contactId);
                                
                                        return {
                                          id: contactId,
                                          status: (status as any)?.status || status,
                                        };
                                      }""", contactId)

    def getNumberProfile(self, contactId):
        contactId = self.valid_chatId(contactId)
        return self.ThreadsafeBrowser.sync_page_evaluate("(contactId) => WAPI.getNumberProfile(contactId)", contactId)

    def getUnreadMessages(self, includeMe, includeNotifications, useUnreadCount):
        return self.ThreadsafeBrowser.sync_page_evaluate(
            """({ includeMe, includeNotifications, useUnreadCount }) =>
        WAPI.getUnreadMessages(includeMe, includeNotifications, useUnreadCount)""",
            {"includeMe": includeMe, "includeNotifications": includeNotifications, "useUnreadCount": useUnreadCount})

    def getAllUnreadMessages(self):
        return self.ThreadsafeBrowser.sync_page_evaluate("() => WAPI.getAllUnreadMessages()")

    def getAllNewMessages(self):
        # @deprecated Use getAllUnreadMessages
        return self.ThreadsafeBrowser.sync_page_evaluate("() => WAPI.getAllNewMessages()")

    def getAllMessagesInChat(self, chatId, includeMe=False, includeNotifications=False):
        chatId = self.valid_chatId(chatId)
        """
        * Retrieves all messages already loaded in a chat
        * For loading every message use loadAndGetAllMessagesInChat
        """
        return self.ThreadsafeBrowser.sync_page_evaluate("""({ chatId, includeMe, includeNotifications }) =>
        WAPI.getAllMessagesInChat(chatId, includeMe, includeNotifications)""",
                                        {"chatId": chatId, "includeMe": includeMe,
                                         "includeNotifications": includeNotifications})

    def loadAndGetAllMessagesInChat(self, chatId, includeMe=False, includeNotifications=False):
        chatId = self.valid_chatId(chatId)
        """
        * Loads and Retrieves all Messages in a chat
        """
        return self.ThreadsafeBrowser.sync_page_evaluate("""({ chatId, includeMe, includeNotifications }) =>
        WAPI.loadAndGetAllMessagesInChat(chatId, includeMe, includeNotifications)""",
                                        {"chatId": chatId, "includeMe": includeMe,
                                         "includeNotifications": includeNotifications})

    def getChatIsOnline(self, chatId):
        chatId = self.valid_chatId(chatId)
        return self.ThreadsafeBrowser.sync_page_evaluate("(chatId) => WAPI.getChatIsOnline(chatId)", chatId)

    def getLastSeen(self, chatId):
        chatId = self.valid_chatId(chatId)
        return self.ThreadsafeBrowser.sync_page_evaluate("(chatId) => WAPI.getLastSeen(chatId)", chatId)

    def getPlatformFromMessage(self, msgId):
        """
        * Get the platform message from message ID
        * The platform can be:
            * android
            * iphone
            * web
            * unknown
        """
        return self.ThreadsafeBrowser.sync_page_evaluate("(msgId) => WPP.chat.getPlatformFromMessage(msgId)", msgId)

    def getReactions(self, msgId):
        return self.ThreadsafeBrowser.sync_page_evaluate("(msgId) => WPP.chat.getReactions(msgId)", msgId)

    def getVotes(self, msgId):
        return self.ThreadsafeBrowser.sync_page_evaluate("(msgId) => WPP.chat.getVotes(msgId)", msgId)
