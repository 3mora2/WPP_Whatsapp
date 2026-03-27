from __future__ import annotations

from typing import Optional
from WPP_Whatsapp.api.layers.HostLayer import HostLayer
from WPP_Whatsapp.api.model import NewsletterOptions


class NewsletterLayer(HostLayer):
    """Layer for managing WhatsApp Newsletters"""

    def createNewsletter(self, name: str, options: Optional[NewsletterOptions] = None, timeout=60):
        """
        Create a new newsletter

        @param name: Newsletter name
        @param options: Additional options (description, picture)
        @return: Newsletter ID
        """
        return self.ThreadsafeBrowser.run_threadsafe(
            self.createNewsletter_, name, options, timeout_=timeout)

    def editNewsletter(self, id: str, options: Optional[NewsletterOptions] = None, timeout=60):
        """
        Edit a newsletter

        @param id: Newsletter ID
        @param options: Options to update (name, description, picture)
        @return: Success status
        """
        return self.ThreadsafeBrowser.run_threadsafe(
            self.editNewsletter_, id, options, timeout_=timeout)

    def destroyNewsletter(self, id: str, timeout=60):
        """
        Destroy a newsletter

        @param id: Newsletter ID
        @return: Success status
        """
        return self.ThreadsafeBrowser.run_threadsafe(
            self.destroyNewsletter_, id, timeout_=timeout)

    def muteNewsletter(self, id: str, timeout=60):
        """
        Mute a newsletter

        @param id: Newsletter ID
        @return: Success status
        """
        return self.ThreadsafeBrowser.run_threadsafe(
            self.muteNewsletter_, id, timeout_=timeout)

    # ##########################################################################
    # Async implementations
    # ##########################################################################

    async def createNewsletter_(self, name: str, options: Optional[NewsletterOptions] = None):
        """Create a new newsletter - async implementation"""
        if options is None:
            options = {}

        result = await self.ThreadsafeBrowser.page_evaluate(
            """({ name, options }) => {
                return WPP.newsletter.create({
                    name,
                    ...options
                });
            }""",
            {"name": name, "options": options},
            page=self.page
        )
        return result

    async def editNewsletter_(self, id: str, options: Optional[NewsletterOptions] = None):
        """Edit a newsletter - async implementation"""
        if options is None:
            options = {}

        result = await self.ThreadsafeBrowser.page_evaluate(
            """({ id, options }) => {
                return WPP.newsletter.update(id, options);
            }""",
            {"id": id, "options": options},
            page=self.page
        )
        return result

    async def destroyNewsletter_(self, id: str):
        """Destroy a newsletter - async implementation"""
        result = await self.ThreadsafeBrowser.page_evaluate(
            """({ id }) => {
                return WPP.newsletter.destroy(id);
            }""",
            {"id": id},
            page=self.page
        )
        return result

    async def muteNewsletter_(self, id: str):
        """Mute a newsletter - async implementation"""
        result = await self.ThreadsafeBrowser.page_evaluate(
            """({ id }) => {
                return WPP.newsletter.mute(id);
            }""",
            {"id": id},
            page=self.page
        )
        return result
