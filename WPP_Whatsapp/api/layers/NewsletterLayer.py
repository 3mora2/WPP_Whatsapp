from __future__ import annotations

from typing import Optional
from WPP_Whatsapp.api.layers.HostLayer import HostLayer
from WPP_Whatsapp.api.model import NewsletterOptions

from WPP_Whatsapp.core.sync_api import sync_wrapper


class NewsletterLayer(HostLayer):
    """Layer for managing WhatsApp Newsletters"""

    @sync_wrapper("createNewsletter_")
    def createNewsletter(self, name: str, options: Optional[NewsletterOptions] = None, timeout=60):
        """
        Create a new newsletter

        @param name: Newsletter name
        @param options: Additional options (description, picture)
        @return: Newsletter ID
        """
        ...

    @sync_wrapper("editNewsletter_")
    def editNewsletter(self, id: str, options: Optional[NewsletterOptions] = None, timeout=60):
        """
        Edit a newsletter

        @param id: Newsletter ID
        @param options: Options to update (name, description, picture)
        @return: Success status
        """
        ...

    @sync_wrapper("destroyNewsletter_")
    def destroyNewsletter(self, id: str, timeout=60):
        """
        Destroy a newsletter

        @param id: Newsletter ID
        @return: Success status
        """
        ...

    @sync_wrapper("muteNewsletter_")
    def muteNewsletter(self, id: str, timeout=60):
        """
        Mute a newsletter

        @param id: Newsletter ID
        @return: Success status
        """
        ...

    # ##########################################################################
    # Async implementations
    # ##########################################################################

    async def createNewsletter_(self, name: str, options: Optional[NewsletterOptions] = None):
        """Create a new newsletter - async implementation"""
        if options is None:
            options = {}

        result = await self._evaluate_js(
            'NewsletterLayer.createNewsletter_.0',
            {"name": name, "options": options},
            page=self.page
        )
        return result

    async def editNewsletter_(self, id: str, options: Optional[NewsletterOptions] = None):
        """Edit a newsletter - async implementation"""
        if options is None:
            options = {}

        result = await self._evaluate_js(
            'NewsletterLayer.editNewsletter_.0',
            {"id": id, "options": options},
            page=self.page
        )
        return result

    async def destroyNewsletter_(self, id: str):
        """Destroy a newsletter - async implementation"""
        result = await self._evaluate_js(
            'NewsletterLayer.destroyNewsletter_.0',
            {"id": id},
            page=self.page
        )
        return result

    async def muteNewsletter_(self, id: str):
        """Mute a newsletter - async implementation"""
        result = await self._evaluate_js(
            'NewsletterLayer.muteNewsletter_.0',
            {"id": id},
            page=self.page
        )
        return result

    def muteNesletter(self, id, timeout=60):
        """Compatibility with the original WPPConnect spelling."""
        return self.muteNewsletter(id, timeout=timeout)

    async def muteNesletter_(self, id):
        return await self.muteNewsletter_(id)
