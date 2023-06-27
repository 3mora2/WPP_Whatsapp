from WPP_Whatsapp.api.layers.SenderLayer import SenderLayer


class RetrieverLayer(SenderLayer):
    async def getSessionTokenBrowser(self, removePath):
        # @returns obj [token]
        if removePath:
            await self.page_evaluate("() => {window['pathSession'] = true;}")

        if await self.isMultiDevice():
            return await self.page_evaluate("""() => {
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
        return await self.page_evaluate("""() => {
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

    async def getTheme(self):
        # @returns string light or dark
        return await self.page_evaluate("() => WAPI.getTheme()")

    async def getAllChats(self, withNewMessageOnly=False):
        # @returns array of [Chat]
        if withNewMessageOnly:
            return await self.page_evaluate("() => WAPI.getAllChatsWithNewMsg()")

        return await self.page_evaluate("() => WAPI.getAllChats()")

    async def checkNumberStatus(self, contactId):
        # @returns contact detial as promise
        contactId = self.valid_chatId(contactId)
        return await self.page_evaluate("(contactId) => WAPI.checkNumberStatus(contactId)", contactId)

    async def getAllChatsWithMessages(self, withNewMessageOnly=False):
        # @returns array of [Chat]
        return await self.page_evaluate("""(withNewMessageOnly: boolean) =>
        WAPI.getAllChatsWithMessages(withNewMessageOnly)""", withNewMessageOnly)

    async def getAllGroups(self, withNewMessagesOnly):
        # @returns array of groups
        return await self.page_evaluate("""async ({ withNewMessagesOnly }) => {
        const chats = await WPP.chat.list({
          onlyGroups: true,
          onlyWithUnreadMessage: withNewMessagesOnly,
        });

        const groups = await Promise.all(
          chats.map((c) => WPP.group.ensureGroup(c.id))
        );

        return groups.map((g) => WAPI._serializeChatObj(g));
      }""", withNewMessagesOnly)

    async def getAllBroadcastList(self):
        # @returns array of broadcast list
        chats = await self.page_evaluate("""() => WAPI.getAllChats()""")
        if chats:
            return list(
                filter(lambda x: x.get("isBroadcast") and x.get("id").get("_serialized") != 'status@broadcast', chats))

    async def getContact(self, contactId):
        # @returns contact detial as promise
        contactId = self.valid_chatId(contactId)
        return await self.page_evaluate("(contactId) => WAPI.getContact(contactId)", contactId)

    async def getAllContacts(self):
        # @returns array of [Contact]
        return await self.page_evaluate("() => WAPI.getAllContacts()")

    async def getChatById(self, contactId):
        contactId = self.valid_chatId(contactId)
        return await self.page_evaluate("(contactId) => WAPI.getChatById(contactId)", contactId)

    async def getChat(self, contactId):
        contactId = self.valid_chatId(contactId)
        return self.getChatById(contactId)

    async def getProfilePicFromServer(self, chatId):
        # @returns url of the chat picture or undefined if there is no picture for the chat.
        chatId = self.valid_chatId(chatId)
        return await self.page_evaluate("(chatId) => WAPI._profilePicfunc(chatId)", chatId)

    async def loadEarlierMessages(self, contactId):
        contactId = self.valid_chatId(contactId)
        return await self.page_evaluate("(contactId) => WAPI.loadEarlierMessages(contactId)", contactId)

    async def getStatus(self, contactId):
        contactId = self.valid_chatId(contactId)
        return await self.page_evaluate("""async (contactId) => {
                                        const status = await WPP.contact.getStatus(contactId);
                                
                                        return {
                                          id: contactId,
                                          status: (status as any)?.status || status,
                                        };
                                      }""", contactId)

    async def getNumberProfile(self, contactId):
        contactId = self.valid_chatId(contactId)
        return await self.page_evaluate("(contactId) => WAPI.getNumberProfile(contactId)", contactId)

    async def getUnreadMessages(self, includeMe, includeNotifications, useUnreadCount):
        return await self.page_evaluate(
            """({ includeMe, includeNotifications, useUnreadCount }) =>
        WAPI.getUnreadMessages(includeMe, includeNotifications, useUnreadCount)""",
            {"includeMe": includeMe, "includeNotifications": includeNotifications, "useUnreadCount": useUnreadCount})

    async def getAllUnreadMessages(self):
        return await self.page_evaluate("() => WAPI.getAllUnreadMessages()")

    async def getAllNewMessages(self):
        # @deprecated Use getAllUnreadMessages
        return await self.page_evaluate("() => WAPI.getAllNewMessages()")

    async def getAllMessagesInChat(self, chatId, includeMe=False, includeNotifications=False):
        chatId = self.valid_chatId(chatId)
        """
        * Retrieves all messages already loaded in a chat
        * For loading every message use loadAndGetAllMessagesInChat
        """
        return await self.page_evaluate("""({ chatId, includeMe, includeNotifications }) =>
        WAPI.getAllMessagesInChat(chatId, includeMe, includeNotifications)""",
                                        {"chatId": chatId, "includeMe": includeMe,
                                         "includeNotifications": includeNotifications})

    async def loadAndGetAllMessagesInChat(self, chatId, includeMe=False, includeNotifications=False):
        chatId = self.valid_chatId(chatId)
        """
        * Loads and Retrieves all Messages in a chat
        """
        return await self.page_evaluate("""({ chatId, includeMe, includeNotifications }) =>
        WAPI.loadAndGetAllMessagesInChat(chatId, includeMe, includeNotifications)""",
                                        {"chatId": chatId, "includeMe": includeMe,
                                         "includeNotifications": includeNotifications})

    async def getChatIsOnline(self, chatId):
        chatId = self.valid_chatId(chatId)
        return await self.page_evaluate("(chatId) => WAPI.getChatIsOnline(chatId)", chatId)

    async def getLastSeen(self, chatId):
        chatId = self.valid_chatId(chatId)
        return await self.page_evaluate("(chatId) => WAPI.getLastSeen(chatId)", chatId)

    async def getPlatformFromMessage(self, msgId):
        """
        * Get the platform message from message ID
        * The platform can be:
            * android
            * iphone
            * web
            * unknown
        """
        return await self.page_evaluate("(msgId) => WPP.chat.getPlatformFromMessage(msgId)", msgId)

    async def getReactions(self, msgId):
        return await self.page_evaluate("(msgId) => WPP.chat.getReactions(msgId)", msgId)

    async def getVotes(self, msgId):
        return await self.page_evaluate("(msgId) => WPP.chat.getVotes(msgId)", msgId)
