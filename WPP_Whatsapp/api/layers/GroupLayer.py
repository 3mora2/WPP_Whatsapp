from WPP_Whatsapp.api.layers.RetrieverLayer import RetrieverLayer


class GroupLayer(RetrieverLayer):
    async def leaveGroup(self, groupId):
        groupId = self.valid_chatId(groupId)
        return await self.page_evaluate("(groupId) => WPP.group.leave(groupId)", groupId)

    async def getGroupMembersIds(self, groupId):
        groupId = self.valid_chatId(groupId)
        return await self.page_evaluate("""(groupId) => Promise.resolve(WPP.group.getParticipants(groupId)).then(
          (participants) => participants.map((p) => p.id))""", groupId)

    async def getGroupMembers(self, groupId):
        groupId = self.valid_chatId(groupId)
        membersIds = await self.getGroupMembersIds(groupId)
        return [self.getContact(memberId.get("_serialized")) for memberId in membersIds]

    async def getGroupInviteLink(self, chatId):
        chatId = self.valid_chatId(chatId)
        code = await self.page_evaluate("(chatId) => WPP.group.getInviteCode(chatId)", chatId)

        return f"https://chat.whatsapp.com/{code}" if code else None

    async def revokeGroupInviteLink(self, chatId):
        chatId = self.valid_chatId(chatId)
        code = await self.page_evaluate("(chatId) => WPP.group.revokeInviteCode(chatId)", chatId)

        return f"https://chat.whatsapp.com/{code}" if code else None

    async def getGroupInfoFromInviteLink(self, invite_code):
        invite_code = invite_code.replace('chat.whatsapp.com/', '')
        invite_code = invite_code.replace('invite/', '')
        invite_code = invite_code.replace('https://', '')
        invite_code = invite_code.replace('http://', '')
        return await self.page_evaluate("(inviteCode) => WPP.group.getGroupInfoFromInviteCode(inviteCode)", invite_code)

    async def createGroup(self, groupName, contacts=[]):
        return await self.page_evaluate("({ groupName, contacts }) => WPP.group.create(groupName, contacts)",
                                        {"groupName": groupName, "contacts": contacts})

    async def removeParticipant(self, groupId, participantId):
        groupId = self.valid_chatId(groupId)
        await self.page_evaluate("""({ groupId, participantId }) =>
        WPP.group.removeParticipants(groupId, participantId)""", {"groupId": groupId, "participantId": participantId})
        return True

    async def addParticipant(self, groupId, participantId):
        groupId = self.valid_chatId(groupId)
        return await self.page_evaluate("""({ groupId, participantId }) =>
        WPP.group.addParticipants(groupId, participantId)""", {"groupId": groupId, "participantId": participantId})

    async def getGroupAdmins(self, chatId):
        chatId = self.valid_chatId(chatId)
        participants = await self.page_evaluate("""(chatId) =>
        Promise.resolve(WPP.group.getParticipants(chatId)).then(
          (participants) => participants.map((p) => p.toJSON())
        )""", chatId)
        # return [participant for participant in participants if participant.get("isAdmin")]
        return [participant.get("id") for participant in participants if participant.get("isAdmin")]

    async def joinGroup(self, invite_code):
        invite_code = invite_code.replace('chat.whatsapp.com/', '')
        invite_code = invite_code.replace('invite/', '')
        invite_code = invite_code.replace('https://', '')
        invite_code = invite_code.replace('http://', '')
        return await self.page_evaluate("(inviteCode) => WPP.group.joinGroup(inviteCode)", invite_code)
