from __future__ import annotations

from typing import List, Optional
from WPP_Whatsapp.api.layers.RetrieverLayer import RetrieverLayer
from WPP_Whatsapp.api.model import (
    GroupDescriptionOptions,
    GroupSubjectOptions,
    GroupIconOptions,
    GroupPropertyOptions,
    GroupMembershipRequestOptions,
)

from WPP_Whatsapp.core.sync_api import sync_wrapper


class GroupLayer(RetrieverLayer):
    @sync_wrapper("leaveGroup_")
    def leaveGroup(self, groupId, timeout=60):
        ...

    @sync_wrapper("getGroupMembersIds_")
    def getGroupMembersIds(self, groupId, timeout=60):
        ...

    @sync_wrapper("getGroupMembers_")
    def getGroupMembers(self, groupId, timeout=60):
        ...

    @sync_wrapper("getGroupInviteLink_")
    def getGroupInviteLink(self, chatId, timeout=60):
        ...

    @sync_wrapper("revokeGroupInviteLink_")
    def revokeGroupInviteLink(self, chatId, timeout=60):
        ...

    @sync_wrapper("getGroupInfoFromInviteLink_")
    def getGroupInfoFromInviteLink(self, invite_code, timeout=60):
        ...

    @sync_wrapper("createGroup_")
    def createGroup(self, groupName, contacts=None, timeout=60):
        ...

    @sync_wrapper("removeParticipant_")
    def removeParticipant(self, groupId, participantId, timeout=60):
        ...

    @sync_wrapper("addParticipant_")
    def addParticipant(self, groupId, participantId, timeout=60):
        ...

    @sync_wrapper("getGroupAdmins_")
    def getGroupAdmins(self, chatId, timeout=60):
        ...

    @sync_wrapper("joinGroup_")
    def joinGroup(self, invite_code, timeout=60):
        ...

    @sync_wrapper("setGroupDescription_")
    def setGroupDescription(self, groupId: str, description: str, options: Optional[GroupDescriptionOptions] = None, timeout=60):
        """Set group description"""
        ...

    @sync_wrapper("setGroupSubject_")
    def setGroupSubject(self, groupId: str, title: str, options: Optional[GroupSubjectOptions] = None, timeout=60):
        """Set group subject/title"""
        ...

    @sync_wrapper("setGroupIcon_")
    def setGroupIcon(self, groupId: str, pathOrBase64: str, options: Optional[GroupIconOptions] = None, timeout=60):
        """Set group icon"""
        ...

    @sync_wrapper("removeGroupIcon_")
    def removeGroupIcon(self, groupId: str, timeout=60):
        """Remove group icon"""
        ...

    @sync_wrapper("setGroupProperty_")
    def setGroupProperty(self, groupId: str, property: str, value: bool, options: Optional[GroupPropertyOptions] = None, timeout=60):
        """Set group property (restrict, announce, ephemeral, noFrequentlyForwarded)"""
        ...

    @sync_wrapper("setMessagesAdminsOnly_")
    def setMessagesAdminsOnly(self, groupId: str, option: bool, timeout=60):
        """Allow only admins to send messages"""
        ...

    @sync_wrapper("getGroupMembershipRequests_")
    def getGroupMembershipRequests(self, groupId: str, timeout=60):
        """Get group membership requests"""
        ...

    @sync_wrapper("approveGroupMembershipRequest_")
    def approveGroupMembershipRequest(self, groupId: str, membershipIds: List[str], timeout=60):
        """Approve membership request"""
        ...

    @sync_wrapper("rejectGroupMembershipRequest_")
    def rejectGroupMembershipRequest(self, groupId: str, membershipIds: List[str], timeout=60):
        """Reject membership request"""
        ...

    ##################################################################################
    async def leaveGroup_(self, groupId):
        groupId = self.valid_chatId(groupId)
        return await self._evaluate_js('GroupLayer.leaveGroup_.0', groupId, page=self.page)

    async def getGroupMembersIds_(self, groupId):
        groupId = self.valid_chatId(groupId)
        return await self._evaluate_js('GroupLayer.getGroupMembersIds_.0', groupId, page=self.page)

    async def getGroupMembers_(self, groupId):
        groupId = self.valid_chatId(groupId)
        membersIds = await self.getGroupMembersIds_(groupId)
        return [await self.getContact_((memberId.get("_serialized") if isinstance(memberId, dict) else memberId)) for memberId in membersIds]

    async def getGroupInviteLink_(self, chatId):
        chatId = self.valid_chatId(chatId)
        code = await self._evaluate_js('GroupLayer.getGroupInviteLink_.0', chatId, page=self.page)

        return f"https://chat.whatsapp.com/{code}" if code else None

    async def revokeGroupInviteLink_(self, chatId):
        chatId = self.valid_chatId(chatId)
        code = await self._evaluate_js('GroupLayer.revokeGroupInviteLink_.0', chatId, page=self.page)

        return f"https://chat.whatsapp.com/{code}" if code else None

    async def getGroupInfoFromInviteLink_(self, invite_code):
        invite_code = invite_code.replace('chat.whatsapp.com/', '')
        invite_code = invite_code.replace('invite/', '')
        invite_code = invite_code.replace('https://', '')
        invite_code = invite_code.replace('http://', '')
        return await self._evaluate_js('GroupLayer.getGroupInfoFromInviteLink_.0', invite_code, page=self.page)

    async def createGroup_(self, groupName, contacts=None):
        contacts = [self.valid_chatId(c) for c in (contacts or [])]
        return await self._evaluate_js('GroupLayer.createGroup_.0',
                                        {"groupName": groupName, "contacts": contacts}, page=self.page)

    async def removeParticipant_(self, groupId, participantId):
        groupId = self.valid_chatId(groupId)
        await self._evaluate_js('GroupLayer.removeParticipant_.0', {"groupId": groupId, "participantId": participantId}, page=self.page)
        return True

    async def addParticipant_(self, groupId, participantId):
        groupId = self.valid_chatId(groupId)
        return await self._evaluate_js('GroupLayer.addParticipant_.0', {"groupId": groupId, "participantId": participantId}, page=self.page)

    async def getGroupAdmins_(self, chatId):
        chatId = self.valid_chatId(chatId)
        participants = await self._evaluate_js('GroupLayer.getGroupAdmins_.0', chatId, page=self.page)
        # return [participant for participant in participants if participant.get("isAdmin")]
        return [participant.get("id") for participant in participants if participant.get("isAdmin")]

    async def joinGroup_(self, invite_code):
        invite_code = invite_code.replace('chat.whatsapp.com/', '')
        invite_code = invite_code.replace('invite/', '')
        invite_code = invite_code.replace('https://', '')
        invite_code = invite_code.replace('http://', '')
        return await self._evaluate_js('GroupLayer.joinGroup_.0', invite_code, page=self.page)

    async def setGroupDescription_(self, groupId: str, description: str, options: Optional[GroupDescriptionOptions] = None):
        """Set group description - async implementation"""
        groupId = self.valid_chatId(groupId)
        return await self._evaluate_js(
            'GroupLayer.setGroupDescription_.0',
            {"groupId": groupId, "description": description},
            page=self.page
        )

    async def setGroupSubject_(self, groupId: str, title: str, options: Optional[GroupSubjectOptions] = None):
        """Set group subject - async implementation"""
        groupId = self.valid_chatId(groupId)
        return await self._evaluate_js(
            'GroupLayer.setGroupSubject_.0',
            {"groupId": groupId, "subject": title},
            page=self.page
        )

    async def setGroupIcon_(self, groupId: str, pathOrBase64: str, options: Optional[GroupIconOptions] = None):
        """Set group icon - async implementation"""
        groupId = self.valid_chatId(groupId)
        pathOrBase64 = await self._media_to_base64(pathOrBase64, "image")
        return await self._evaluate_js(
            'GroupLayer.setGroupIcon_.0',
            {"groupId": groupId, "pathOrBase64": pathOrBase64},
            page=self.page
        )

    async def removeGroupIcon_(self, groupId: str):
        """Remove group icon - async implementation"""
        groupId = self.valid_chatId(groupId)
        return await self._evaluate_js(
            'GroupLayer.removeGroupIcon_.0',
            {"groupId": groupId},
            page=self.page
        )

    async def setGroupProperty_(self, groupId: str, property: str, value: bool, options: Optional[GroupPropertyOptions] = None):
        """Set group property - async implementation"""
        groupId = self.valid_chatId(groupId)
        property_map = {
            "restrict": "restrict",
            "announce": "announce",
            "ephemeral": "ephemeral",
            "noFrequentlyForwarded": "noFrequentlyForwarded"
        }
        return await self._evaluate_js(
            'GroupLayer.setGroupProperty_.0',
            {"groupId": groupId, "property": property_map.get(property, property), "value": value},
            page=self.page
        )

    async def setMessagesAdminsOnly_(self, groupId: str, option: bool):
        """Set messages admins only - async implementation"""
        groupId = self.valid_chatId(groupId)
        return await self._evaluate_js(
            'GroupLayer.setMessagesAdminsOnly_.0',
            {"groupId": groupId, "value": option},
            page=self.page
        )

    async def getGroupMembershipRequests_(self, groupId: str):
        """Get group membership requests - async implementation"""
        groupId = self.valid_chatId(groupId)
        return await self._evaluate_js(
            'GroupLayer.getGroupMembershipRequests_.0',
            {"groupId": groupId},
            page=self.page
        )

    async def approveGroupMembershipRequest_(self, groupId: str, membershipIds: List[str]):
        """Approve membership request - async implementation"""
        groupId = self.valid_chatId(groupId)
        return await self._evaluate_js(
            'GroupLayer.approveGroupMembershipRequest_.0',
            {"groupId": groupId, "membershipIds": membershipIds},
            page=self.page
        )

    async def rejectGroupMembershipRequest_(self, groupId: str, membershipIds: List[str]):
        """Reject membership request - async implementation"""
        groupId = self.valid_chatId(groupId)
        return await self._evaluate_js(
            'GroupLayer.rejectGroupMembershipRequest_.0',
            {"groupId": groupId, "membershipIds": membershipIds},
            page=self.page
        )

    @sync_wrapper("promoteParticipant_")
    def promoteParticipant(self, groupId, participantId, timeout=60):
        """Promote one or more group participants."""
        ...

    async def promoteParticipant_(self, groupId, participantId):
        groupId = self.valid_chatId(groupId)
        return await self._evaluate_js(
            'GroupLayer.promoteParticipant_.0', {"groupId": groupId, "participantId": participantId}, page=self.page)

    @sync_wrapper("demoteParticipant_")
    def demoteParticipant(self, groupId, participantId, timeout=60):
        """Demote one or more group admins."""
        ...

    async def demoteParticipant_(self, groupId, participantId):
        groupId = self.valid_chatId(groupId)
        return await self._evaluate_js(
            'GroupLayer.demoteParticipant_.0', {"groupId": groupId, "participantId": participantId}, page=self.page)
