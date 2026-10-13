from __future__ import annotations

from WPP_Whatsapp.api.layers.ControlsLayer import ControlsLayer
from WPP_Whatsapp.api.layers.CommunityLayer import CommunityLayer
from WPP_Whatsapp.api.layers.NewsletterLayer import NewsletterLayer

from WPP_Whatsapp.core.sync_api import sync_wrapper


class BusinessLayer(ControlsLayer, CommunityLayer, NewsletterLayer):
    @sync_wrapper("getBusinessProfilesProducts_")
    def getBusinessProfilesProducts(self, id_: str, timeout=60):
        """Query the product catalog for a business profile."""
        ...

    @sync_wrapper("getBusinessProfile_")
    def getBusinessProfile(self, id, timeout=60):
        """Get a contact business profile."""
        ...

    async def getBusinessProfile_(self, id):
        return await self._evaluate_js(
            'BusinessLayer.getBusinessProfile_.0', {"id": id}, page=self.page)

    @sync_wrapper("sendImageWithProduct_")
    def sendImageWithProduct(self, to, base64, caption, businessId, productId, timeout=60):
        """Send an image containing product information."""
        ...

    async def sendImageWithProduct_(self, to, base64, caption, businessId, productId):
        to = self.valid_chatId(to)
        return await self._evaluate_js(
            'BusinessLayer.sendImageWithProduct_.0', {"to": to, "base64": base64, "caption": caption, "businessId": businessId, "productId": productId}, page=self.page)
