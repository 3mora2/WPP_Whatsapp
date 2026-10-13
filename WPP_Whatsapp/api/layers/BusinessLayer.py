from __future__ import annotations

from WPP_Whatsapp.api.layers.ControlsLayer import ControlsLayer
from WPP_Whatsapp.api.layers.CommunityLayer import CommunityLayer
from WPP_Whatsapp.api.layers.NewsletterLayer import NewsletterLayer


class BusinessLayer(ControlsLayer, CommunityLayer, NewsletterLayer):
    def getBusinessProfilesProducts(self, id_: str, timeout=60):
        """Query the product catalog for a business profile."""
        return self.ThreadsafeBrowser.run_threadsafe(
            self.getBusinessProfilesProducts_, id_, timeout_=timeout)

    def getBusinessProfile(self, id, timeout=60):
        """Get a contact business profile."""
        return self.ThreadsafeBrowser.run_threadsafe(self.getBusinessProfile_, id, timeout_=timeout)

    async def getBusinessProfile_(self, id):
        return await self.ThreadsafeBrowser.page_evaluate(
            "({id}) => WPP.contact.getBusinessProfile(id)", {"id": id}, page=self.page)

    def sendImageWithProduct(self, to, base64, caption, businessId, productId, timeout=60):
        """Send an image containing product information."""
        return self.ThreadsafeBrowser.run_threadsafe(self.sendImageWithProduct_, to, base64, caption, businessId, productId, timeout_=timeout)

    async def sendImageWithProduct_(self, to, base64, caption, businessId, productId):
        to = self.valid_chatId(to)
        return await self.ThreadsafeBrowser.page_evaluate(
            "({to, base64, caption, businessId, productId}) => WAPI.sendImageWithProduct(base64, to, caption, businessId, productId)", {"to": to, "base64": base64, "caption": caption, "businessId": businessId, "productId": productId}, page=self.page)
