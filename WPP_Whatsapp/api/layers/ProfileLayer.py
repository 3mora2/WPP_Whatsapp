from WPP_Whatsapp.api.layers.StatusLayer import StatusLayer


class ProfileLayer(StatusLayer):
    async def sendMute(self, chatId, time, type):
        """
          /**
           * @category Chat
           * @param contactsId Example: 0000@c.us | [000@c.us, 1111@c.us]
           * @param time duration of silence
           * @param type kind of silence "hours" "minutes" "year"
           * To remove the silence, just enter the contact parameter
           */
        """
        chatId = self.valid_chatId(chatId)
        return await self.page_evaluate("(id, time, type) => WAPI.sendMute(id, time, type)",
                                        {"id": chatId, "time": time, "type": type})

    async def setProfileStatus(self, status):
        """
          /**
           * Sets current user profile status
           * @category Profile
           * @param status
           */
        """
        return await self.page_evaluate("""({ status }) => {
            WPP.profile.setMyStatus(status);
          }""", status)

    async def setProfilePic(self, pathOrBase64, to):
        pass
        # ToDO:
        # base64 = ''
        # if pathOrBase64.startswith('data:'):
        #     base64 = pathOrBase64
        # else:
        #     if pathOrBase64 and os.path.exists(pathOrBase64):
        #         base64 = self.convert_to_base64(pathOrBase64)
        #
        # if not base64:
        #     print("Empty or invalid file or base64")
        #     return
        # mimeInfo = base64.split(";base64")[0].split(":")[-1]
        # if 'image' not in mimeInfo:
        #     print('Not an image, allowed formats png, jpeg and webp')
        #     return

    async def setProfileName(self, name):
        return await self.page_evaluate("({ name }) => {WAPI.setMyName(name);}", name)
