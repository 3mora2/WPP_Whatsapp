from __future__ import annotations

from typing import List, Optional
from WPP_Whatsapp.api.layers.HostLayer import HostLayer
from WPP_Whatsapp.api.model import CommunityOptions, CommunityParticipantOptions

from WPP_Whatsapp.core.sync_api import sync_wrapper


class CommunityLayer(HostLayer):
    """Layer for managing WhatsApp Communities"""

    @sync_wrapper("createCommunity_")
    def createCommunity(self, name: str, description: str, groupIds: List[str], options: Optional[CommunityOptions] = None, timeout=60):
        """
        Create a new community

        @param name: Community name
        @param description: Community description
        @param groupIds: List of group IDs to add to the community
        @param options: Additional options
        @return: Community ID
        """
        ...

    @sync_wrapper("deactivateCommunity_")
    def deactivateCommunity(self, communityId: str, timeout=60):
        """
        Deactivate a community

        @param communityId: Community ID
        @return: Success status
        """
        ...

    @sync_wrapper("addSubgroupsCommunity_")
    def addSubgroupsCommunity(self, communityId: str, groupsIds: List[str], timeout=60):
        """
        Add groups to community

        @param communityId: Community ID
        @param groupsIds: List of group IDs to add
        @return: Success status
        """
        ...

    @sync_wrapper("removeSubgroupsCommunity_")
    def removeSubgroupsCommunity(self, communityId: str, groupsIds: List[str], timeout=60):
        """
        Remove groups from community

        @param communityId: Community ID
        @param groupsIds: List of group IDs to remove
        @return: Success status
        """
        ...

    @sync_wrapper("promoteCommunityParticipant_")
    def promoteCommunityParticipant(self, communityId: str, participantId: str | List[str], timeout=60):
        """
        Promote participant to community admin

        @param communityId: Community ID
        @param participantId: Participant ID or list of IDs
        @return: Success status
        """
        ...

    @sync_wrapper("demoteCommunityParticipant_")
    def demoteCommunityParticipant(self, communityId: str, participantId: str | List[str], timeout=60):
        """
        Demote community admin to participant

        @param communityId: Community ID
        @param participantId: Participant ID or list of IDs
        @return: Success status
        """
        ...

    @sync_wrapper("getCommunityParticipants_")
    def getCommunityParticipants(self, communityId: str, timeout=60):
        """
        Get all participants of a community

        @param communityId: Community ID
        @return: List of participant IDs
        """
        ...

    # ##########################################################################
    # Async implementations
    # ##########################################################################

    async def createCommunity_(self, name: str, description: str, groupIds: List[str], options: Optional[CommunityOptions] = None):
        """Create a new community - async implementation"""
        if options is None:
            options = {}

        result = await self._evaluate_js(
            'CommunityLayer.createCommunity_.0',
            {"name": name, "description": description, "groupIds": groupIds, "options": options},
            page=self.page
        )
        return result

    async def deactivateCommunity_(self, communityId: str):
        """Deactivate a community - async implementation"""
        result = await self._evaluate_js(
            'CommunityLayer.deactivateCommunity_.0',
            {"communityId": communityId},
            page=self.page
        )
        return result

    async def addSubgroupsCommunity_(self, communityId: str, groupsIds: List[str]):
        """Add groups to community - async implementation"""
        result = await self._evaluate_js(
            'CommunityLayer.addSubgroupsCommunity_.0',
            {"communityId": communityId, "groupsIds": groupsIds},
            page=self.page
        )
        return result

    async def removeSubgroupsCommunity_(self, communityId: str, groupsIds: List[str]):
        """Remove groups from community - async implementation"""
        result = await self._evaluate_js(
            'CommunityLayer.removeSubgroupsCommunity_.0',
            {"communityId": communityId, "groupsIds": groupsIds},
            page=self.page
        )
        return result

    async def promoteCommunityParticipant_(self, communityId: str, participantId: str | List[str]):
        """Promote participant to community admin - async implementation"""
        if isinstance(participantId, str):
            participantId = [participantId]

        result = await self._evaluate_js(
            'CommunityLayer.promoteCommunityParticipant_.0',
            {"communityId": communityId, "participantIds": participantId},
            page=self.page
        )
        return result

    async def demoteCommunityParticipant_(self, communityId: str, participantId: str | List[str]):
        """Demote community admin to participant - async implementation"""
        if isinstance(participantId, str):
            participantId = [participantId]

        result = await self._evaluate_js(
            'CommunityLayer.demoteCommunityParticipant_.0',
            {"communityId": communityId, "participantIds": participantId},
            page=self.page
        )
        return result

    async def getCommunityParticipants_(self, communityId: str):
        """Get all participants of a community - async implementation"""
        result = await self._evaluate_js(
            'CommunityLayer.getCommunityParticipants_.0',
            {"communityId": communityId},
            page=self.page
        )
        return result
