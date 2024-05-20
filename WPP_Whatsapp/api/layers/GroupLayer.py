from WPP_Whatsapp.api.layers.RetrieverLayer import RetrieverLayer


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

    def createGroup(self, groupName, contacts=[], timeout=60):
        return self.ThreadsafeBrowser.run_threadsafe(self.createGroup_, groupName, contacts, timeout_=timeout)

    def removeParticipant(self, groupId, participantId, timeout=60):
        return self.ThreadsafeBrowser.run_threadsafe(self.removeParticipant_, groupId, participantId, timeout_=timeout)

    def addParticipant(self, groupId, participantId, timeout=60):
        return self.ThreadsafeBrowser.run_threadsafe(self.addParticipant_, groupId, participantId, timeout_=timeout)

    def getGroupAdmins(self, chatId, timeout=60):
        return self.ThreadsafeBrowser.run_threadsafe(self.getGroupAdmins_, chatId, timeout_=timeout)

    def joinGroup(self, invite_code, timeout=60):
        return self.ThreadsafeBrowser.run_threadsafe(self.joinGroup_, invite_code, timeout_=timeout)

    ##################################################################################
    async def leaveGroup_(self, groupId):
        groupId = self.valid_chatId(groupId)
        return await self.ThreadsafeBrowser.page_evaluate("(groupId) => WPP.group.leave(groupId)", groupId, page=self.page)

    async def getGroupMembersIds_(self, groupId):
        groupId = self.valid_chatId(groupId)
        return await self.ThreadsafeBrowser.page_evaluate("""(groupId) => Promise.resolve(WPP.group.getParticipants(groupId)).then(
          (participants) => participants.map((p) => p.id))""", groupId, page=self.page)

    async def getGroupMembers_(self, groupId):
        groupId = self.valid_chatId(groupId)
        membersIds = await self.getGroupMembersIds_(groupId)
        return [await self.getContact_(memberId.get("_serialized")) for memberId in membersIds]

    async def getGroupInviteLink_(self, chatId):
        chatId = self.valid_chatId(chatId)
        code = await self.ThreadsafeBrowser.page_evaluate("(chatId) => WPP.group.getInviteCode(chatId)", chatId, page=self.page)

        return f"https://chat.whatsapp.com/{code}" if code else None

    async def revokeGroupInviteLink_(self, chatId):
        chatId = self.valid_chatId(chatId)
        code = await self.ThreadsafeBrowser.page_evaluate("(chatId) => WPP.group.revokeInviteCode(chatId)", chatId, page=self.page)

        return f"https://chat.whatsapp.com/{code}" if code else None

    async def getGroupInfoFromInviteLink_(self, invite_code):
        invite_code = invite_code.replace('chat.whatsapp.com/', '')
        invite_code = invite_code.replace('invite/', '')
        invite_code = invite_code.replace('https://', '')
        invite_code = invite_code.replace('http://', '')
        return await self.ThreadsafeBrowser.page_evaluate("(inviteCode) => WPP.group.getGroupInfoFromInviteCode(inviteCode)", invite_code, page=self.page)

    async def createGroup_(self, groupName, contacts=[]):
        return await self.ThreadsafeBrowser.page_evaluate("({ groupName, contacts }) => WPP.group.create(groupName, contacts)",
                                        {"groupName": groupName, "contacts": contacts}, page=self.page)

    async def removeParticipant_(self, groupId, participantId):
        groupId = self.valid_chatId(groupId)
        await self.ThreadsafeBrowser.page_evaluate("""({ groupId, participantId }) =>
        WPP.group.removeParticipants(groupId, participantId)""", {"groupId": groupId, "participantId": participantId}, page=self.page)
        return True

    async def addParticipant_(self, groupId, participantId):
        groupId = self.valid_chatId(groupId)
        return await self.ThreadsafeBrowser.page_evaluate("""({ groupId, participantId }) =>
        WPP.group.addParticipants(groupId, participantId)""", {"groupId": groupId, "participantId": participantId}, page=self.page)

    async def getGroupAdmins_(self, chatId):
        chatId = self.valid_chatId(chatId)
        participants = await self.ThreadsafeBrowser.page_evaluate("""(chatId) =>
        Promise.resolve(WPP.group.getParticipants(chatId)).then(
          (participants) => participants.map((p) => p.toJSON())
        )""", chatId, page=self.page)
        # return [participant for participant in participants if participant.get("isAdmin")]
        return [participant.get("id") for participant in participants if participant.get("isAdmin")]

    async def joinGroup_(self, invite_code):
        invite_code = invite_code.replace('chat.whatsapp.com/', '')
        invite_code = invite_code.replace('invite/', '')
        invite_code = invite_code.replace('https://', '')
        invite_code = invite_code.replace('http://', '')
        return await self.ThreadsafeBrowser.page_evaluate("(inviteCode) => WPP.group.join(inviteCode)", invite_code, page=self.page)
