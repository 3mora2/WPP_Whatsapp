from WPP_Whatsapp.api.layers.CatalogLayer import CatalogLayer

from WPP_Whatsapp.core.sync_api import sync_wrapper


class ListsLayer(CatalogLayer):
    """Custom chat lists supported by personal and business accounts."""

    @sync_wrapper("createList_")
    def createList(self, name, chatIds=None, colorIndex=None, timeout=60):
        """Create a custom chat list."""
        ...

    async def createList_(self, name, chatIds=None, colorIndex=None):
        chatIds = [self.valid_chatId(c) for c in (chatIds or [])]
        return await self._evaluate_js(
            'ListsLayer.createList_.0', {"name": name, "chatIds": chatIds, "colorIndex": colorIndex}, page=self.page)

    @sync_wrapper("getAllLists_")
    def getAllLists(self, timeout=60):
        """Get all custom chat lists."""
        ...

    async def getAllLists_(self):
        return await self._evaluate_js(
            'ListsLayer.getAllLists_.0', page=self.page)

    @sync_wrapper("addChatsToList_")
    def addChatsToList(self, listId, chatIds, timeout=60):
        """Add chats to a custom list."""
        ...

    async def addChatsToList_(self, listId, chatIds):
        chatIds = [self.valid_chatId(c) for c in (chatIds or [])]
        return await self._evaluate_js(
            'ListsLayer.addChatsToList_.0', {"listId": listId, "chatIds": chatIds}, page=self.page)

    @sync_wrapper("removeChatsFromList_")
    def removeChatsFromList(self, listId, chatIds, timeout=60):
        """Remove chats from a custom list."""
        ...

    async def removeChatsFromList_(self, listId, chatIds):
        chatIds = [self.valid_chatId(c) for c in (chatIds or [])]
        return await self._evaluate_js(
            'ListsLayer.removeChatsFromList_.0', {"listId": listId, "chatIds": chatIds}, page=self.page)

    @sync_wrapper("renameList_")
    def renameList(self, listId, newName, timeout=60):
        """Rename a custom list."""
        ...

    async def renameList_(self, listId, newName):
        return await self._evaluate_js(
            'ListsLayer.renameList_.0', {"listId": listId, "newName": newName}, page=self.page)

    @sync_wrapper("deleteList_")
    def deleteList(self, listId, timeout=60):
        """Delete a custom list."""
        ...

    async def deleteList_(self, listId):
        return await self._evaluate_js(
            'ListsLayer.deleteList_.0', {"listId": listId}, page=self.page)
