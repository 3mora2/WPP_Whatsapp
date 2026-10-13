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


class GroupLayer(RetrieverLayer):
    def leaveGroup(self, groupId, timeout=60):
        return self.ThreadsafeBrowser.run_threadsafe(self.leaveGroup_, groupId, timeout_=timeout)

    def getGroupMembersIds(self, groupId, timeout=60):
        return self.ThreadsafeBrowser.run_threadsafe(self.getGroupMembersIds_, groupId, timeout_=timeout)

    def getGroupMembers(self, groupId, timeout=60):
        return self.ThreadsafeBrowser.run_threadsafe(self.getGroupMembers_, groupId, timeout_=timeout)

    def getGroupInviteLink(self, chatId, timeout=60):
        return self.ThreadsafeBrowser.run_threadsafe(self.getGroupInviteLink_, chatId, timeout_=timeout)

    def revokeGroupInviteLink(self, chatId, timeout=60):
        return self.ThreadsafeBrowser.run_threadsafe(self.revokeGroupInviteLink_, chatId, timeout_=timeout)

    def getGroupInfoFromInviteLink(self, invite_code, timeout=60):
        return self.ThreadsafeBrowser.run_threadsafe(self.getGroupInfoFromInviteLink_, invite_code, timeout_=timeout)

    def createGroup(self, groupName, contacts=None, timeout=60):
        return self.ThreadsafeBrowser.run_threadsafe(self.createGroup_, groupName, contacts, timeout_=timeout)

    def removeParticipant(self, groupId, participantId, timeout=60):
        return self.ThreadsafeBrowser.run_threadsafe(self.removeParticipant_, groupId, participantId, timeout_=timeout)

    def addParticipant(self, groupId, participantId, timeout=60):
        return self.ThreadsafeBrowser.run_threadsafe(self.addParticipant_, groupId, participantId, timeout_=timeout)

    def getGroupAdmins(self, chatId, timeout=60):
        return self.ThreadsafeBrowser.run_threadsafe(self.getGroupAdmins_, chatId, timeout_=timeout)

    def joinGroup(self, invite_code, timeout=60):
        return self.ThreadsafeBrowser.run_threadsafe(self.joinGroup_, invite_code, timeout_=timeout)

    def setGroupDescription(self, groupId: str, description: str, options: Optional[GroupDescriptionOptions] = None, timeout=60):
        """Set group description"""
        return self.ThreadsafeBrowser.run_threadsafe(
            self.setGroupDescription_, groupId, description, options, timeout_=timeout)

    def setGroupSubject(self, groupId: str, title: str, options: Optional[GroupSubjectOptions] = None, timeout=60):
        """Set group subject/title"""
        return self.ThreadsafeBrowser.run_threadsafe(
            self.setGroupSubject_, groupId, title, options, timeout_=timeout)

    def setGroupIcon(self, groupId: str, pathOrBase64: str, options: Optional[GroupIconOptions] = None, timeout=60):
        """Set group icon"""
        return self.ThreadsafeBrowser.run_threadsafe(
            self.setGroupIcon_, groupId, pathOrBase64, options, timeout_=timeout)

    def removeGroupIcon(self, groupId: str, timeout=60):
        """Remove group icon"""
        return self.ThreadsafeBrowser.run_threadsafe(
            self.removeGroupIcon_, groupId, timeout_=timeout)

    def setGroupProperty(self, groupId: str, property: str, value: bool, options: Optional[GroupPropertyOptions] = None, timeout=60):
        """Set group property (restrict, announce, ephemeral, noFrequentlyForwarded)"""
        return self.ThreadsafeBrowser.run_threadsafe(
            self.setGroupProperty_, groupId, property, value, options, timeout_=timeout)

    def setMessagesAdminsOnly(self, groupId: str, option: bool, timeout=60):
        """Allow only admins to send messages"""
        return self.ThreadsafeBrowser.run_threadsafe(
            self.setMessagesAdminsOnly_, groupId, option, timeout_=timeout)

    def getGroupMembershipRequests(self, groupId: str, timeout=60):
        """Get group membership requests"""
        return self.ThreadsafeBrowser.run_threadsafe(
            self.getGroupMembershipRequests_, groupId, timeout_=timeout)

    def approveGroupMembershipRequest(self, groupId: str, membershipIds: List[str], timeout=60):
        """Approve membership request"""
        return self.ThreadsafeBrowser.run_threadsafe(
            self.approveGroupMembershipRequest_, groupId, membershipIds, timeout_=timeout)

    def rejectGroupMembershipRequest(self, groupId: str, membershipIds: List[str], timeout=60):
        """Reject membership request"""
        return self.ThreadsafeBrowser.run_threadsafe(
            self.rejectGroupMembershipRequest_, groupId, membershipIds, timeout_=timeout)

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

    def promoteParticipant(self, groupId, participantId, timeout=60):
        """Promote one or more group participants."""
        return self.ThreadsafeBrowser.run_threadsafe(self.promoteParticipant_, groupId, participantId, timeout_=timeout)

    async def promoteParticipant_(self, groupId, participantId):
        groupId = self.valid_chatId(groupId)
        return await self._evaluate_js(
            'GroupLayer.promoteParticipant_.0', {"groupId": groupId, "participantId": participantId}, page=self.page)

    def demoteParticipant(self, groupId, participantId, timeout=60):
        """Demote one or more group admins."""
        return self.ThreadsafeBrowser.run_threadsafe(self.demoteParticipant_, groupId, participantId, timeout_=timeout)

    async def demoteParticipant_(self, groupId, participantId):
        groupId = self.valid_chatId(groupId)
        return await self._evaluate_js(
            'GroupLayer.demoteParticipant_.0', {"groupId": groupId, "participantId": participantId}, page=self.page)
