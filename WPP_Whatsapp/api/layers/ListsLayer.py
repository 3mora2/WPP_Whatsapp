from WPP_Whatsapp.api.layers.CatalogLayer import CatalogLayer


class ListsLayer(CatalogLayer):
    """Custom chat lists supported by personal and business accounts."""

    def createList(self, name, chatIds=None, colorIndex=None, timeout=60):
        """Create a custom chat list."""
        return self.ThreadsafeBrowser.run_threadsafe(self.createList_, name, chatIds, colorIndex, timeout_=timeout)

    async def createList_(self, name, chatIds=None, colorIndex=None):
        chatIds = [self.valid_chatId(c) for c in (chatIds or [])]
        return await self.ThreadsafeBrowser.page_evaluate(
            "({name, chatIds, colorIndex}) => WPP.lists.create(name, chatIds, colorIndex ?? undefined)", {"name": name, "chatIds": chatIds, "colorIndex": colorIndex}, page=self.page)

    def getAllLists(self, timeout=60):
        """Get all custom chat lists."""
        return self.ThreadsafeBrowser.run_threadsafe(self.getAllLists_, timeout_=timeout)

    async def getAllLists_(self):
        return await self.ThreadsafeBrowser.page_evaluate(
            "() => WPP.lists.list()", page=self.page)

    def addChatsToList(self, listId, chatIds, timeout=60):
        """Add chats to a custom list."""
        return self.ThreadsafeBrowser.run_threadsafe(self.addChatsToList_, listId, chatIds, timeout_=timeout)

    async def addChatsToList_(self, listId, chatIds):
        chatIds = [self.valid_chatId(c) for c in (chatIds or [])]
        return await self.ThreadsafeBrowser.page_evaluate(
            "({listId, chatIds}) => WPP.lists.addChats(listId, chatIds)", {"listId": listId, "chatIds": chatIds}, page=self.page)

    def removeChatsFromList(self, listId, chatIds, timeout=60):
        """Remove chats from a custom list."""
        return self.ThreadsafeBrowser.run_threadsafe(self.removeChatsFromList_, listId, chatIds, timeout_=timeout)

    async def removeChatsFromList_(self, listId, chatIds):
        chatIds = [self.valid_chatId(c) for c in (chatIds or [])]
        return await self.ThreadsafeBrowser.page_evaluate(
            "({listId, chatIds}) => WPP.lists.removeChats(listId, chatIds)", {"listId": listId, "chatIds": chatIds}, page=self.page)

    def renameList(self, listId, newName, timeout=60):
        """Rename a custom list."""
        return self.ThreadsafeBrowser.run_threadsafe(self.renameList_, listId, newName, timeout_=timeout)

    async def renameList_(self, listId, newName):
        return await self.ThreadsafeBrowser.page_evaluate(
            "({listId, newName}) => WPP.lists.rename(listId, newName)", {"listId": listId, "newName": newName}, page=self.page)

    def deleteList(self, listId, timeout=60):
        """Delete a custom list."""
        return self.ThreadsafeBrowser.run_threadsafe(self.deleteList_, listId, timeout_=timeout)

    async def deleteList_(self, listId):
        return await self.ThreadsafeBrowser.page_evaluate(
            "({listId}) => WPP.lists.remove(listId)", {"listId": listId}, page=self.page)
