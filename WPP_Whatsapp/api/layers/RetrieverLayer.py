from WPP_Whatsapp.api.layers.SenderLayer import SenderLayer
from WPP_Whatsapp.api.model import ChatListOptions


class RetrieverLayer(SenderLayer):
    def getSessionTokenBrowser(self, removePath, timeout=60):
        return self.ThreadsafeBrowser.run_threadsafe(self.getSessionTokenBrowser_(removePath), timeout_=timeout)

    def getTheme(self, timeout=60):
        return self.ThreadsafeBrowser.run_threadsafe(self.getTheme_(), timeout_=timeout)

    def getAllChats(self, withNewMessageOnly=False, timeout=60):
        return self.ThreadsafeBrowser.run_threadsafe(self.getAllChats_(withNewMessageOnly), timeout_=timeout)

    def listChats(self, options: ChatListOptions = {}, timeout=60):
        """
          /**
           * Return list of chats
           *  * @example
           * ```javascript
           * // All chats
           * const chats = await client.listChats();
           *
           * // Some chats
           * const chats = client.listChats({count: 20});
           *
           * // 20 chats before specific chat
           * const chats = client.listChats({count: 20, direction: 'before', id: '[number]@c.us'});
           *
           * // Only users chats
           * const chats = await client.listChats({onlyUsers: true});
           *
           * // Only groups chats
           * const chats = await client.listChats({onlyGroups: true});
           *
           * // Only with label Text
           * const chats = await client.listChats({withLabels: ['Test']});
           *
           * // Only with label id
           * const chats = await client.listChats({withLabels: ['1']});
           *
           * // Only with label with one of text or id
           * const chats = await client.listChats({withLabels: ['Alfa','5']});
           * ```
           * @category Chat
           * @returns array of [Chat]
           */
        """
        return self.ThreadsafeBrowser.run_threadsafe(self.listChats_(options), timeout_=timeout)

    def checkNumberStatus(self, contactId, timeout=60):
        return self.ThreadsafeBrowser.run_threadsafe(self.checkNumberStatus_(contactId), timeout_=timeout)

    def getAllChatsWithMessages(self, withNewMessageOnly=False, timeout=60):
        return self.ThreadsafeBrowser.run_threadsafe(self.getAllChatsWithMessages_(withNewMessageOnly), timeout_=timeout)

    def getAllGroups(self, withNewMessagesOnly=False, timeout=60):
        return self.ThreadsafeBrowser.run_threadsafe(self.getAllGroups_(withNewMessagesOnly), timeout_=timeout)

    def getAllBroadcastList(self, timeout=60):
        return self.ThreadsafeBrowser.run_threadsafe(self.getAllBroadcastList_(), timeout_=timeout)

    def getContact(self, contactId, timeout=60):
        return self.ThreadsafeBrowser.run_threadsafe(self.getContact_(contactId), timeout_=timeout)

    def getAllContacts(self, timeout=60):
        return self.ThreadsafeBrowser.run_threadsafe(self.getAllContacts_(), timeout_=timeout)

    def getChatById(self, contactId, timeout=60):
        return self.ThreadsafeBrowser.run_threadsafe(self.getChatById_(contactId), timeout_=timeout)

    def getChat(self, contactId, timeout=60):
        return self.ThreadsafeBrowser.run_threadsafe(self.getChat_(contactId), timeout_=timeout)

    def getProfilePicFromServer(self, chatId, timeout=60):
        return self.ThreadsafeBrowser.run_threadsafe(self.getProfilePicFromServer_(chatId), timeout_=timeout)

    def loadEarlierMessages(self, contactId, timeout=60):
        return self.ThreadsafeBrowser.run_threadsafe(self.loadEarlierMessages_(contactId), timeout_=timeout)

    def getStatus(self, contactId, timeout=60):
        return self.ThreadsafeBrowser.run_threadsafe(self.getStatus_(contactId), timeout_=timeout)

    def getNumberProfile(self, contactId, timeout=60):
        return self.ThreadsafeBrowser.run_threadsafe(self.getNumberProfile_(contactId), timeout_=timeout)

    def getUnreadMessages(self, includeMe, includeNotifications, useUnreadCount, timeout=60):
        return self.ThreadsafeBrowser.run_threadsafe(
            self.getUnreadMessages_(includeMe, includeNotifications, useUnreadCount), timeout_=timeout)

    def getAllUnreadMessages(self, timeout=60):
        return self.ThreadsafeBrowser.run_threadsafe(self.getAllUnreadMessages_(), timeout_=timeout)

    def getAllNewMessages(self, timeout=60):
        return self.ThreadsafeBrowser.run_threadsafe(self.getAllNewMessages_(), timeout_=timeout)

    def getAllMessagesInChat(self, chatId, includeMe=False, includeNotifications=False, timeout=60):
        return self.ThreadsafeBrowser.run_threadsafe(
            self.getAllMessagesInChat_(chatId, includeMe, includeNotifications), timeout_=timeout)

    def loadAndGetAllMessagesInChat(self, chatId, includeMe=False, includeNotifications=False, timeout=60):
        return self.ThreadsafeBrowser.run_threadsafe(
            self.loadAndGetAllMessagesInChat_(chatId, includeMe, includeNotifications), timeout_=timeout)

    def getChatIsOnline(self, chatId, timeout=60):
        return self.ThreadsafeBrowser.run_threadsafe(self.getChatIsOnline_(chatId), timeout_=timeout)

    def getLastSeen(self, chatId, timeout=60):
        return self.ThreadsafeBrowser.run_threadsafe(self.getLastSeen_(chatId), timeout_=timeout)

    def getPlatformFromMessage(self, msgId, timeout=60):
        return self.ThreadsafeBrowser.run_threadsafe(self.getPlatformFromMessage_(msgId), timeout_=timeout)

    def getReactions(self, msgId, timeout=60):
        return self.ThreadsafeBrowser.run_threadsafe(self.getReactions_(msgId), timeout_=timeout)

    def getVotes(self, msgId, timeout=60):
        return self.ThreadsafeBrowser.run_threadsafe(self.getVotes_(msgId), timeout_=timeout)

    ########################################################
    async def getSessionTokenBrowser_(self, removePath):
        # @returns obj [token]
        if removePath:
            await self.ThreadsafeBrowser.page_evaluate("() => {window['pathSession'] = true;}", page=self.page)

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
        }""", page=self.page)
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
      }""", page=self.page)

    async def getTheme_(self):
        # @returns string light or dark
        return await self.ThreadsafeBrowser.page_evaluate("() => WAPI.getTheme()", page=self.page)

    async def getAllChats_(self, withNewMessageOnly=False):
        # @returns array of [Chat]
        if withNewMessageOnly:
            return await self.ThreadsafeBrowser.page_evaluate("() => WAPI.getAllChatsWithNewMsg()", page=self.page)

        return await self.ThreadsafeBrowser.page_evaluate("() => WAPI.getAllChats()", page=self.page)

    async def listChats_(self, options: ChatListOptions = {}):
        """
          /**
           * Return list of chats
           *  * @example
           * ```javascript
           * // All chats
           * const chats = await client.listChats();
           *
           * // Some chats
           * const chats = client.listChats({count: 20});
           *
           * // 20 chats before specific chat
           * const chats = client.listChats({count: 20, direction: 'before', id: '[number]@c.us'});
           *
           * // Only users chats
           * const chats = await client.listChats({onlyUsers: true});
           *
           * // Only groups chats
           * const chats = await client.listChats({onlyGroups: true});
           *
           * // Only with label Text
           * const chats = await client.listChats({withLabels: ['Test']});
           *
           * // Only with label id
           * const chats = await client.listChats({withLabels: ['1']});
           *
           * // Only with label with one of text or id
           * const chats = await client.listChats({withLabels: ['Alfa','5']});
           * ```
           * @category Chat
           * @returns array of [Chat]
           */
        """
        return await self.ThreadsafeBrowser.page_evaluate(
            """
        async ({ options }) => {
        const chats = await WPP.chat.list(options);

        const serialized = chats.map((c) => WAPI._serializeChatObj(c));
        return serialized;
      }
        """, {"options": options}, page=self.page)

    async def checkNumberStatus_(self, contactId):
        # @returns contact detial as promise
        contactId = self.valid_chatId(contactId)
        return await self.ThreadsafeBrowser.page_evaluate(
            "(contactId) => WAPI.checkNumberStatus(contactId)", contactId, page=self.page)
        # result = await self.ThreadsafeBrowser.page_evaluate(
        #     "(contactId) => WPP.contact.queryExists(contactId)",
        #     contactId, page=self.page)
        # if not result:
        #     return {
        #         "id": contactId,
        #         "isBusiness": False,
        #         "canReceiveMessage": False,
        #         "numberExists": False,
        #         "status": 404,
        #         "result": result
        #     }
        # else:
        #     return {
        #         "id": result.get("wid"),
        #         "isBusiness": result.get("biz"),
        #         "canReceiveMessage": True,
        #         "numberExists": True,
        #         "status": 200,
        #         "result": result
        #     }

    async def getAllChatsWithMessages_(self, withNewMessageOnly=False):
        # @returns array of [Chat]
        return await self.ThreadsafeBrowser.page_evaluate("""(withNewMessageOnly: boolean) =>
        WAPI.getAllChatsWithMessages(withNewMessageOnly)""", withNewMessageOnly, page=self.page)

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
      }""", withNewMessagesOnly, page=self.page)

    async def getAllBroadcastList_(self):
        # @returns array of broadcast list
        chats = await self.ThreadsafeBrowser.page_evaluate("""() => WAPI.getAllChats()""", page=self.page)
        if chats:
            return list(
                filter(lambda x: x.get("isBroadcast") and x.get("id").get("_serialized") != 'status@broadcast', chats))

    async def getContact_(self, contactId):
        # @returns contact detial as promise
        contactId = self.valid_chatId(contactId)
        return await self.ThreadsafeBrowser.page_evaluate("(contactId) => WAPI.getContact(contactId)", contactId,
                                                          page=self.page)

    async def getAllContacts_(self):
        # @returns array of [Contact]
        return await self.ThreadsafeBrowser.page_evaluate("() => WAPI.getAllContacts()", page=self.page)

    async def getChatById_(self, contactId):
        contactId = self.valid_chatId(contactId)
        return await self.ThreadsafeBrowser.page_evaluate("(contactId) => WAPI.getChatById(contactId)", contactId,
                                                          page=self.page)

    async def getChat_(self, contactId):
        contactId = self.valid_chatId(contactId)
        return self.getChatById(contactId)

    async def getProfilePicFromServer_(self, chatId):
        # @returns url of the chat picture or unasync defined if there is no picture for the chat.
        chatId = self.valid_chatId(chatId)
        return await self.ThreadsafeBrowser.page_evaluate("(chatId) => WAPI._profilePicfunc(chatId)", chatId,
                                                          page=self.page)

    async def loadEarlierMessages_(self, contactId):
        contactId = self.valid_chatId(contactId)
        return await self.ThreadsafeBrowser.page_evaluate("(contactId) => WAPI.loadEarlierMessages(contactId)",
                                                          contactId, page=self.page)

    async def getStatus_(self, contactId):
        contactId = self.valid_chatId(contactId)
        return await self.ThreadsafeBrowser.page_evaluate("""async (contactId) => {
                                        const status = await WPP.contact.getStatus(contactId);
                                
                                        return {
                                          id: contactId,
                                          status: (status as any)?.status || status,
                                        };
                                      }""", contactId, page=self.page)

    async def getNumberProfile_(self, contactId):
        contactId = self.valid_chatId(contactId)
        return await self.ThreadsafeBrowser.page_evaluate("(contactId) => WAPI.getNumberProfile(contactId)", contactId,
                                                          page=self.page)

    async def getUnreadMessages_(self, includeMe, includeNotifications, useUnreadCount):
        return await self.ThreadsafeBrowser.page_evaluate(
            """({ includeMe, includeNotifications, useUnreadCount }) =>
        WAPI.getUnreadMessages(includeMe, includeNotifications, useUnreadCount)""",
            {"includeMe": includeMe, "includeNotifications": includeNotifications, "useUnreadCount": useUnreadCount},
            page=self.page)

    async def getAllUnreadMessages_(self):
        return await self.ThreadsafeBrowser.page_evaluate("() => WAPI.getAllUnreadMessages()", page=self.page)

    async def getAllNewMessages_(self):
        # @deprecated Use getAllUnreadMessages
        return await self.ThreadsafeBrowser.page_evaluate("() => WAPI.getAllNewMessages()", page=self.page)

    async def getAllMessagesInChat_(self, chatId, includeMe=False, includeNotifications=False):
        chatId = self.valid_chatId(chatId)
        """
        * Retrieves all messages already loaded in a chat
        * For loading every message use loadAndGetAllMessagesInChat
        """
        return await self.ThreadsafeBrowser.page_evaluate("""({ chatId, includeMe, includeNotifications }) =>
        WAPI.getAllMessagesInChat(chatId, includeMe, includeNotifications)""",
                                                          {"chatId": chatId, "includeMe": includeMe,
                                                           "includeNotifications": includeNotifications},
                                                          page=self.page)

    async def loadAndGetAllMessagesInChat_(self, chatId, includeMe=False, includeNotifications=False):
        chatId = self.valid_chatId(chatId)
        """
        * Loads and Retrieves all Messages in a chat
        """
        return await self.ThreadsafeBrowser.page_evaluate("""({ chatId, includeMe, includeNotifications }) =>
        WAPI.loadAndGetAllMessagesInChat(chatId, includeMe, includeNotifications)""",
                                                          {"chatId": chatId, "includeMe": includeMe,
                                                           "includeNotifications": includeNotifications},
                                                          page=self.page)

    async def getChatIsOnline_(self, chatId):
        chatId = self.valid_chatId(chatId)
        return await self.ThreadsafeBrowser.page_evaluate("(chatId) => WAPI.getChatIsOnline(chatId)", chatId,
                                                          page=self.page)

    async def getLastSeen_(self, chatId):
        chatId = self.valid_chatId(chatId)
        return await self.ThreadsafeBrowser.page_evaluate("(chatId) => WAPI.getLastSeen(chatId)", chatId,
                                                          page=self.page)

    async def getPlatformFromMessage_(self, msgId):
        """
        * Get the platform message from message ID
        * The platform can be:
            * android
            * iphone
            * web
            * unknown
        """
        return await self.ThreadsafeBrowser.page_evaluate("(msgId) => WPP.chat.getPlatformFromMessage(msgId)", msgId,
                                                          page=self.page)

    async def getReactions_(self, msgId):
        return await self.ThreadsafeBrowser.page_evaluate("(msgId) => WPP.chat.getReactions(msgId)", msgId,
                                                          page=self.page)

    async def getVotes_(self, msgId):
        return await self.ThreadsafeBrowser.page_evaluate("(msgId) => WPP.chat.getVotes(msgId)", msgId, page=self.page)
