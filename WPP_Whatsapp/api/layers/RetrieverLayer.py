from WPP_Whatsapp.api.layers.SenderLayer import SenderLayer


class RetrieverLayer(SenderLayer):
    def getSessionTokenBrowser(self, removePath, timeout=60):
        return self.ThreadsafeBrowser.run_threadsafe(
            self.getSessionTokenBrowser_, removePath, timeout_=timeout)

    def getTheme(self, timeout=60):
        return self.ThreadsafeBrowser.run_threadsafe(
            self.getTheme_, timeout_=timeout)

    def getAllChats(self, withNewMessageOnly=False, timeout=60):
        return self.ThreadsafeBrowser.run_threadsafe(
            self.getAllChats_, self, withNewMessageOnly, timeout_=timeout)

    def checkNumberStatus(self, contactId, timeout=60):
        return self.ThreadsafeBrowser.run_threadsafe(
            self.checkNumberStatus_, contactId, timeout_=timeout)

    def getAllChatsWithMessages(self, withNewMessageOnly=False, timeout=60):
        return self.ThreadsafeBrowser.run_threadsafe(
            self.getAllChatsWithMessages_, withNewMessageOnly, timeout_=timeout)

    def getAllGroups(self, withNewMessagesOnly, timeout=60):
        return self.ThreadsafeBrowser.run_threadsafe(
            self.getAllGroups_, withNewMessagesOnly, timeout_=timeout)

    def getAllBroadcastList(self, timeout=60):
        return self.ThreadsafeBrowser.run_threadsafe(
            self.getAllBroadcastList_, timeout_=timeout)

    def getContact(self, contactId, timeout=60):
        return self.ThreadsafeBrowser.run_threadsafe(
            self.getContact_, contactId, timeout_=timeout)

    def getAllContacts(self, timeout=60):
        return self.ThreadsafeBrowser.run_threadsafe(
            self.getAllContacts_, timeout_=timeout)

    def getChatById(self, contactId, timeout=60):
        return self.ThreadsafeBrowser.run_threadsafe(
            self.getChatById_, contactId, timeout_=timeout)

    def getChat(self, contactId, timeout=60):
        return self.ThreadsafeBrowser.run_threadsafe(
            self.getChat_, contactId, timeout_=timeout)

    def getProfilePicFromServer(self, chatId, timeout=60):
        return self.ThreadsafeBrowser.run_threadsafe(
            self.getProfilePicFromServer_, chatId, timeout_=timeout)

    def loadEarlierMessages(self, contactId, timeout=60):
        return self.ThreadsafeBrowser.run_threadsafe(
            self.loadEarlierMessages_, contactId, timeout_=timeout)

    def getStatus(self, contactId, timeout=60):
        return self.ThreadsafeBrowser.run_threadsafe(
            self.getStatus_, contactId, timeout_=timeout)

    def getNumberProfile(self, contactId, timeout=60):
        return self.ThreadsafeBrowser.run_threadsafe(
            self.getNumberProfile_, contactId, timeout_=timeout)

    def getUnreadMessages(self, includeMe, includeNotifications, useUnreadCount, timeout=60):
        return self.ThreadsafeBrowser.run_threadsafe(
            self.getUnreadMessages_, includeMe, includeNotifications, useUnreadCount, timeout_=timeout)

    def getAllUnreadMessages(self, timeout=60):
        return self.ThreadsafeBrowser.run_threadsafe(
            self.getAllUnreadMessages_, timeout_=timeout)

    def getAllNewMessages(self, timeout=60):
        return self.ThreadsafeBrowser.run_threadsafe(
            self.getAllNewMessages_, timeout_=timeout)

    def getAllMessagesInChat(self, chatId, includeMe=False, includeNotifications=False, timeout=60):
        return self.ThreadsafeBrowser.run_threadsafe(
            self.getAllMessagesInChat_, chatId, includeMe, includeNotifications, timeout_=timeout)

    def loadAndGetAllMessagesInChat(self, chatId, includeMe=False, includeNotifications=False, timeout=60):
        return self.ThreadsafeBrowser.run_threadsafe(
            self.loadAndGetAllMessagesInChat_, chatId, includeMe, includeNotifications, timeout_=timeout)

    def getChatIsOnline(self, chatId, timeout=60):
        return self.ThreadsafeBrowser.run_threadsafe(
            self.getChatIsOnline_, chatId, timeout_=timeout)

    def getLastSeen(self, chatId, timeout=60):
        return self.ThreadsafeBrowser.run_threadsafe(
            self.getLastSeen_, chatId, timeout_=timeout)

    def getPlatformFromMessage(self, msgId, timeout=60):
        return self.ThreadsafeBrowser.run_threadsafe(
            self.getPlatformFromMessage_, msgId, timeout_=timeout)

    def getReactions(self, msgId, timeout=60):
        return self.ThreadsafeBrowser.run_threadsafe(
            self.getReactions_, msgId, timeout_=timeout)

    def getVotes(self, msgId, timeout=60):
        return self.ThreadsafeBrowser.run_threadsafe(
            self.getVotes_, msgId, timeout_=timeout)

    ########################################################
    async def getSessionTokenBrowser_(self, removePath):
        # @returns obj [token]
        if removePath:
            await self.ThreadsafeBrowser.page_evaluate("() => {window['pathSession'] = true;}")

        if self.isMultiDevice():
            return await self.ThreadsafeBrowser.page_evaluate("""() => {
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
        return await self.ThreadsafeBrowser.page_evaluate("""() => {
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

    async def getTheme_(self):
        # @returns string light or dark
        return await self.ThreadsafeBrowser.page_evaluate("() => WAPI.getTheme()")

    async def getAllChats_(self, withNewMessageOnly=False):
        # @returns array of [Chat]
        if withNewMessageOnly:
            return await self.ThreadsafeBrowser.page_evaluate("() => WAPI.getAllChatsWithNewMsg()")

        return await self.ThreadsafeBrowser.page_evaluate("() => WAPI.getAllChats()")

    async def checkNumberStatus_(self, contactId):
        # @returns contact detial as promise
        contactId = self.valid_chatId(contactId)
        return await self.ThreadsafeBrowser.page_evaluate("(contactId) => WAPI.checkNumberStatus(contactId)", contactId)

    async def getAllChatsWithMessages_(self, withNewMessageOnly=False):
        # @returns array of [Chat]
        return await self.ThreadsafeBrowser.page_evaluate("""(withNewMessageOnly: boolean) =>
        WAPI.getAllChatsWithMessages(withNewMessageOnly)""", withNewMessageOnly)

    async def getAllGroups_(self, withNewMessagesOnly):
        # @returns array of groups
        return await self.ThreadsafeBrowser.page_evaluate("""async ({ withNewMessagesOnly }) => {
        const chats = await WPP.chat.list({
          onlyGroups: true,
          onlyWithUnreadMessage: withNewMessagesOnly,
        });

        const groups = await Promise.all(
          chats.map((c) => WPP.group.ensureGroup(c.id))
        );

        return groups.map((g) => WAPI._serializeChatObj(g));
      }""", withNewMessagesOnly)

    async def getAllBroadcastList_(self):
        # @returns array of broadcast list
        chats = await self.ThreadsafeBrowser.page_evaluate("""() => WAPI.getAllChats()""")
        if chats:
            return list(
                filter(lambda x: x.get("isBroadcast") and x.get("id").get("_serialized") != 'status@broadcast', chats))

    async def getContact_(self, contactId):
        # @returns contact detial as promise
        contactId = self.valid_chatId(contactId)
        return await self.ThreadsafeBrowser.page_evaluate("(contactId) => WAPI.getContact(contactId)", contactId)

    async def getAllContacts_(self):
        # @returns array of [Contact]
        return await self.ThreadsafeBrowser.page_evaluate("() => WAPI.getAllContacts()")

    async def getChatById_(self, contactId):
        contactId = self.valid_chatId(contactId)
        return await self.ThreadsafeBrowser.page_evaluate("(contactId) => WAPI.getChatById(contactId)", contactId)

    async def getChat_(self, contactId):
        contactId = self.valid_chatId(contactId)
        return self.getChatById(contactId)

    async def getProfilePicFromServer_(self, chatId):
        # @returns url of the chat picture or unasync defined if there is no picture for the chat.
        chatId = self.valid_chatId(chatId)
        return await self.ThreadsafeBrowser.page_evaluate("(chatId) => WAPI._profilePicfunc(chatId)", chatId)

    async def loadEarlierMessages_(self, contactId):
        contactId = self.valid_chatId(contactId)
        return await self.ThreadsafeBrowser.page_evaluate("(contactId) => WAPI.loadEarlierMessages(contactId)",
                                                          contactId)

    async def getStatus_(self, contactId):
        contactId = self.valid_chatId(contactId)
        return await self.ThreadsafeBrowser.page_evaluate("""async (contactId) => {
                                        const status = await WPP.contact.getStatus(contactId);
                                
                                        return {
                                          id: contactId,
                                          status: (status as any)?.status || status,
                                        };
                                      }""", contactId)

    async def getNumberProfile_(self, contactId):
        contactId = self.valid_chatId(contactId)
        return await self.ThreadsafeBrowser.page_evaluate("(contactId) => WAPI.getNumberProfile(contactId)", contactId)

    async def getUnreadMessages_(self, includeMe, includeNotifications, useUnreadCount):
        return await self.ThreadsafeBrowser.page_evaluate(
            """({ includeMe, includeNotifications, useUnreadCount }) =>
        WAPI.getUnreadMessages(includeMe, includeNotifications, useUnreadCount)""",
            {"includeMe": includeMe, "includeNotifications": includeNotifications, "useUnreadCount": useUnreadCount})

    async def getAllUnreadMessages_(self):
        return await self.ThreadsafeBrowser.page_evaluate("() => WAPI.getAllUnreadMessages()")

    async def getAllNewMessages_(self):
        # @deprecated Use getAllUnreadMessages
        return await self.ThreadsafeBrowser.page_evaluate("() => WAPI.getAllNewMessages()")

    async def getAllMessagesInChat_(self, chatId, includeMe=False, includeNotifications=False):
        chatId = self.valid_chatId(chatId)
        """
        * Retrieves all messages already loaded in a chat
        * For loading every message use loadAndGetAllMessagesInChat
        """
        return await self.ThreadsafeBrowser.page_evaluate("""({ chatId, includeMe, includeNotifications }) =>
        WAPI.getAllMessagesInChat(chatId, includeMe, includeNotifications)""",
                                                          {"chatId": chatId, "includeMe": includeMe,
                                                           "includeNotifications": includeNotifications})

    async def loadAndGetAllMessagesInChat_(self, chatId, includeMe=False, includeNotifications=False):
        chatId = self.valid_chatId(chatId)
        """
        * Loads and Retrieves all Messages in a chat
        """
        return await self.ThreadsafeBrowser.page_evaluate("""({ chatId, includeMe, includeNotifications }) =>
        WAPI.loadAndGetAllMessagesInChat(chatId, includeMe, includeNotifications)""",
                                                          {"chatId": chatId, "includeMe": includeMe,
                                                           "includeNotifications": includeNotifications})

    async def getChatIsOnline_(self, chatId):
        chatId = self.valid_chatId(chatId)
        return await self.ThreadsafeBrowser.page_evaluate("(chatId) => WAPI.getChatIsOnline(chatId)", chatId)

    async def getLastSeen_(self, chatId):
        chatId = self.valid_chatId(chatId)
        return await self.ThreadsafeBrowser.page_evaluate("(chatId) => WAPI.getLastSeen(chatId)", chatId)

    async def getPlatformFromMessage_(self, msgId):
        """
        * Get the platform message from message ID
        * The platform can be:
            * android
            * iphone
            * web
            * unknown
        """
        return await self.ThreadsafeBrowser.page_evaluate("(msgId) => WPP.chat.getPlatformFromMessage(msgId)", msgId)

    async def getReactions_(self, msgId):
        return await self.ThreadsafeBrowser.page_evaluate("(msgId) => WPP.chat.getReactions(msgId)", msgId)

    async def getVotes_(self, msgId):
        return await self.ThreadsafeBrowser.page_evaluate("(msgId) => WPP.chat.getVotes(msgId)", msgId)
