from __future__ import annotations

from WPP_Whatsapp.api.layers.ControlsLayer import ControlsLayer
from WPP_Whatsapp.api.layers.CommunityLayer import CommunityLayer
from WPP_Whatsapp.api.layers.NewsletterLayer import NewsletterLayer


class BusinessLayer(ControlsLayer, CommunityLayer, NewsletterLayer):
    def getBusinessProfilesProducts(self, id_: str):
        """
            * Query product catalog
            * @param id Business profile id ('00000@c.us')
        """
