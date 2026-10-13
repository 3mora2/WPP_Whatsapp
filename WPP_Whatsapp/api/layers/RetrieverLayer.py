from WPP_Whatsapp.api.layers.SenderLayer import SenderLayer
from WPP_Whatsapp.api.model import ChatListOptions

from WPP_Whatsapp.core.sync_api import sync_wrapper


class RetrieverLayer(SenderLayer):
    @sync_wrapper("getListMutes_")
    def getListMutes(self, type_, timeout=60):
        ...

    @sync_wrapper("getSessionTokenBrowser_")
    def getSessionTokenBrowser(self, removePath, timeout=60):
        ...

    @sync_wrapper("getTheme_")
    def getTheme(self, timeout=60):
        ...

    @sync_wrapper("getBlockList_")
    def getBlockList(self, timeout=60):
        ...

    @sync_wrapper("getAllChats_")
    def getAllChats(self, withNewMessageOnly=False, timeout=60):
        ...

    def listChats(self, options=None, timeout=60):
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
        if options is None:
            options = {}
        return self.ThreadsafeBrowser.run_threadsafe(self.listChats_(options), timeout_=timeout)

    @sync_wrapper("checkNumberStatus_")
    def checkNumberStatus(self, contactId, timeout=60):
        ...

    @sync_wrapper("getAllChatsWithMessages_")
    def getAllChatsWithMessages(self, withNewMessageOnly=False, timeout=60):
        ...

    @sync_wrapper("getAllGroups_")
    def getAllGroups(self, withNewMessagesOnly=False, timeout=60):
        ...

    @sync_wrapper("getAllBroadcastList_")
    def getAllBroadcastList(self, timeout=60):
        ...

    @sync_wrapper("getContact_")
    def getContact(self, contactId, timeout=60):
        ...

    @sync_wrapper("getAllContacts_")
    def getAllContacts(self, timeout=60):
        ...

    @sync_wrapper("getChatById_")
    def getChatById(self, contactId, timeout=60):
        ...

    @sync_wrapper("getChat_")
    def getChat(self, contactId, timeout=60):
        ...

    @sync_wrapper("getProfilePicFromServer_")
    def getProfilePicFromServer(self, chatId, timeout=60):
        ...

    @sync_wrapper("loadEarlierMessages_")
    def loadEarlierMessages(self, contactId, timeout=60):
        ...

    @sync_wrapper("getStatus_")
    def getStatus(self, contactId, timeout=60):
        ...

    @sync_wrapper("getNumberProfile_")
    def getNumberProfile(self, contactId, timeout=60):
        ...

    @sync_wrapper("getUnreadMessages_")
    def getUnreadMessages(self, includeMe, includeNotifications, useUnreadCount, timeout=60):
        ...

    @sync_wrapper("getAllUnreadMessages_")
    def getAllUnreadMessages(self, timeout=60):
        ...

    @sync_wrapper("getAllNewMessages_")
    def getAllNewMessages(self, timeout=60):
        ...

    @sync_wrapper("getAllMessagesInChat_")
    def getAllMessagesInChat(self, chatId, includeMe=False, includeNotifications=False, timeout=60):
        ...

    @sync_wrapper("loadAndGetAllMessagesInChat_")
    def loadAndGetAllMessagesInChat(self, chatId, includeMe=False, includeNotifications=False, timeout=60):
        ...

    @sync_wrapper("getChatIsOnline_")
    def getChatIsOnline(self, chatId, timeout=60):
        ...

    @sync_wrapper("getLastSeen_")
    def getLastSeen(self, chatId, timeout=60):
        ...

    @sync_wrapper("getPlatformFromMessage_")
    def getPlatformFromMessage(self, msgId, timeout=60):
        ...

    @sync_wrapper("getReactions_")
    def getReactions(self, msgId, timeout=60):
        ...

    @sync_wrapper("getVotes_")
    def getVotes(self, msgId, timeout=60):
        ...

    @sync_wrapper("getOrder_")
    def getOrder(self, msgId, timeout=60):
        ...

    @sync_wrapper("getGroupSizeLimit_")
    def getGroupSizeLimit(self, timeout=60):
        ...

    @sync_wrapper("getCommonGroups_")
    def getCommonGroups(self, wid, timeout=60):
        ...

    @sync_wrapper("getPnLidEntry_")
    def getPnLidEntry(self, phoneOrLid:str, timeout=60):
        ...

    ########################################################
    async def getListMutes_(self, type_):
        # @returns string light or dark
        return await self._evaluate_js('RetrieverLayer.getListMutes_.0', type_,
                                                          page=self.page)

    async def getSessionTokenBrowser_(self, removePath):
        # @returns obj [token]
        if removePath:
            await self._evaluate_js('RetrieverLayer.getSessionTokenBrowser_.2', page=self.page)

        if await self._evaluate_js('RetrieverLayer.getSessionTokenBrowser_.0', page=self.page):
            return await self._evaluate_js('RetrieverLayer.getSessionTokenBrowser_.3', page=self.page)
        return await self._evaluate_js('RetrieverLayer.getSessionTokenBrowser_.1', page=self.page)

    async def getTheme_(self):
        # @returns string light or dark
        return await self._evaluate_js('RetrieverLayer.getTheme_.0', page=self.page)

    async def getBlockList_(self):
        return await self._evaluate_js('RetrieverLayer.getBlockList_.0',
                                                          page=self.page)

    async def getAllChats_(self, withNewMessageOnly=False):
        # @returns array of [Chat]
        if withNewMessageOnly:
            return await self._evaluate_js('RetrieverLayer.getAllChats_.1', page=self.page)

        return await self._evaluate_js('RetrieverLayer.getAllChats_.0', page=self.page)

    async def listChats_(self, options:ChatListOptions=None):
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
        if options is None:
            options = {}
        return await self._evaluate_js(
            'RetrieverLayer.listChats_.0', {"options": options}, page=self.page)

    async def checkNumberStatus_(self, contactId):
        # @returns contact detial as promise
        contactId = self.valid_chatId(contactId)
        return await self._evaluate_js(
            'RetrieverLayer.checkNumberStatus_.0', contactId, page=self.page)
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
        return await self._evaluate_js('RetrieverLayer.getAllChatsWithMessages_.0', withNewMessageOnly, page=self.page)

    async def getAllGroups_(self, withNewMessagesOnly):
        # @returns array of groups
        return await self._evaluate_js('RetrieverLayer.getAllGroups_.0', {"withNewMessagesOnly": withNewMessagesOnly}, page=self.page)

    async def getAllBroadcastList_(self):
        # @returns array of broadcast list
        chats = await self._evaluate_js('RetrieverLayer.getAllBroadcastList_.0', page=self.page)
        if chats:
            return list(
                filter(lambda x: x.get("isBroadcast") and x.get("id").get("_serialized") != 'status@broadcast', chats))

    async def getContact_(self, contactId):
        # @returns contact detial as promise
        contactId = self.valid_chatId(contactId)
        return await self._evaluate_js('RetrieverLayer.getContact_.0', contactId,
                                                          page=self.page)

    async def getAllContacts_(self):
        # @returns array of [Contact]
        return await self._evaluate_js('RetrieverLayer.getAllContacts_.0', page=self.page)

    async def getChatById_(self, contactId):
        contactId = self.valid_chatId(contactId)
        return await self._evaluate_js('RetrieverLayer.getChatById_.0', contactId,
                                                          page=self.page)

    async def getChat_(self, contactId):
        contactId = self.valid_chatId(contactId)
        return await self.getChatById_(contactId)

    async def getProfilePicFromServer_(self, chatId):
        # @returns url of the chat picture or unasync defined if there is no picture for the chat.
        chatId = self.valid_chatId(chatId)
        return await self._evaluate_js('RetrieverLayer.getProfilePicFromServer_.0', chatId,
                                                          page=self.page)

    async def loadEarlierMessages_(self, contactId):
        contactId = await self.get_chat_id_(contactId)
        return await self._evaluate_js('RetrieverLayer.loadEarlierMessages_.0',
                                                          contactId, page=self.page)

    async def getStatus_(self, contactId):
        contactId = self.valid_chatId(contactId)
        return await self._evaluate_js('RetrieverLayer.getStatus_.0', contactId, page=self.page)

    async def getNumberProfile_(self, contactId: str):
        contactId = self.valid_chatId(contactId)
        return await self._evaluate_js('RetrieverLayer.getNumberProfile_.0', contactId,
                                                          page=self.page)

    async def getUnreadMessages_(self, includeMe, includeNotifications, useUnreadCount):
        return await self._evaluate_js(
            'RetrieverLayer.getUnreadMessages_.0',
            {"includeMe": includeMe, "includeNotifications": includeNotifications, "useUnreadCount": useUnreadCount},
            page=self.page)

    async def getAllUnreadMessages_(self):
        return await self._evaluate_js('RetrieverLayer.getAllUnreadMessages_.0', page=self.page)

    async def getAllNewMessages_(self):
        # @deprecated Use getAllUnreadMessages
        return await self._evaluate_js('RetrieverLayer.getAllNewMessages_.0', page=self.page)

    async def getAllMessagesInChat_(self, chatId: str, includeMe=False, includeNotifications=False):
        chatId = await self.get_chat_id_(chatId)
        """
        * Retrieves all messages already loaded in a chat
        * For loading every message use loadAndGetAllMessagesInChat
        """
        return await self._evaluate_js('RetrieverLayer.getAllMessagesInChat_.0',
                                                          {"chatId": chatId, "includeMe": includeMe,
                                                           "includeNotifications": includeNotifications},
                                                          page=self.page)

    async def loadAndGetAllMessagesInChat_(self, chatId: str, includeMe=False, includeNotifications=False):
        chatId = await self.get_chat_id_(chatId)
        """
        * Loads and Retrieves all Messages in a chat
        """
        return await self._evaluate_js('RetrieverLayer.loadAndGetAllMessagesInChat_.0',
                                                          {"chatId": chatId, "includeMe": includeMe,
                                                           "includeNotifications": includeNotifications},
                                                          page=self.page)

    async def getChatIsOnline_(self, chatId: str):
        chatId = self.valid_chatId(chatId)
        return await self._evaluate_js('RetrieverLayer.getChatIsOnline_.0', chatId,
                                                          page=self.page)

    async def getLastSeen_(self, chatId: str):
        chatId = self.valid_chatId(chatId)
        return await self._evaluate_js('RetrieverLayer.getLastSeen_.0', chatId,
                                                          page=self.page)

    async def getPlatformFromMessage_(self, msgId: str):
        """
        * Get the platform message from message ID
        * The platform can be:
            * android
            * iphone
            * web
            * unknown
        """
        return await self._evaluate_js('RetrieverLayer.getPlatformFromMessage_.0', msgId,
                                                          page=self.page)

    async def getReactions_(self, msgId: str):
        return await self._evaluate_js('RetrieverLayer.getReactions_.0', msgId,
                                                          page=self.page)

    async def getVotes_(self, msgId: str):
        return await self._evaluate_js('RetrieverLayer.getVotes_.0', msgId, page=self.page)

    async def getGroupSizeLimit_(self):
        return await self._evaluate_js('RetrieverLayer.getGroupSizeLimit_.0', page=self.page)

    async def getOrder_(self, msgId: str):
        return await self._evaluate_js('RetrieverLayer.getOrder_.0', msgId, page=self.page)

    async def getCommonGroups_(self, wid: str):
        return await self._evaluate_js('RetrieverLayer.getCommonGroups_.0', {"wid": wid},
                                                          page=self.page)

    async def getPnLidEntry_(self, phoneOrLid: str):
        return await self._evaluate_js('RetrieverLayer.getPnLidEntry_.0',
                                                          phoneOrLid,
                                                          page=self.page)

    @sync_wrapper("getMessagesFromRowId_")
    def getMessagesFromRowId(self, options, timeout=60):
        """Read IndexedDB messages after options.minRowId."""
        ...

    async def getMessagesFromRowId_(self, options):
        options = {} if options is None else options
        return await self._evaluate_js(
            'RetrieverLayer.getMessagesFromRowId_.0', {"options": options}, page=self.page)
