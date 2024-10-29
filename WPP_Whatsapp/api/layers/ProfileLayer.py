from WPP_Whatsapp.api.layers.StatusLayer import StatusLayer


class ProfileLayer(StatusLayer):
    def sendMute(self, chatId, time, type_, timeout=60):
        return self.ThreadsafeBrowser.run_threadsafe(
            self.sendMute_, chatId, time, type_, timeout_=timeout)

    def setTheme(self, type_, timeout=60):
        return self.ThreadsafeBrowser.run_threadsafe(
            self.setTheme_, type_, timeout_=timeout)

    def setProfileStatus(self, status, timeout=60):
        """
          /**
           * Sets current user profile status
           * @category Profile
           * @param status
           */
        """
        return self.ThreadsafeBrowser.run_threadsafe(
            self.setProfileStatus_, status, timeout_=timeout)

    def getProfileStatus(self, timeout=60):
        return self.ThreadsafeBrowser.run_threadsafe(
            self.getProfileStatus_, timeout_=timeout)
    def setProfilePic(self, pathOrBase64, to, timeout=60):
        return self.ThreadsafeBrowser.run_threadsafe(
            self.setProfilePic_, pathOrBase64, to, timeout_=timeout)

    def setProfileName(self, name, timeout=60):
        return self.ThreadsafeBrowser.run_threadsafe(
            self.setProfileName_, name, timeout_=timeout)

    def removeMyProfilePicture(self, timeout=60):
        return self.ThreadsafeBrowser.run_threadsafe(
            self.removeMyProfilePicture_, timeout_=timeout)

    ##########################################
    async def sendMute_(self, chatId, time, type):
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
        return await self.ThreadsafeBrowser.page_evaluate("(id, time, type) => WAPI.sendMute(id, time, type)",
                                                          {"id": chatId, "time": time, "type": type}, page=self.page)

    async def setTheme_(self, type_):
        """
           * Change the theme
           * @category Host
           * @param string types "dark" or "light"
        """
        return await self.ThreadsafeBrowser.page_evaluate("(type_) => WAPI.setTheme(type_)", type_, page=self.page)

    async def setProfileStatus_(self, status):
        """
          /**
           * Sets current user profile status
           * @category Profile
           * @param status
           */
        """
        return await self.ThreadsafeBrowser.page_evaluate("""({ status }) => {
            WPP.profile.setMyStatus(status);
          }""", status, page=self.page)

    async def getProfileStatus_(self):
        return await self.ThreadsafeBrowser.page_evaluate("""() => WPP.profile.getMyStatus());""", page=self.page)
    async def setProfilePic_(self, pathOrBase64, to):
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

    async def setProfileName_(self, name):
        return await self.ThreadsafeBrowser.page_evaluate("({ name }) => {WAPI.setMyName(name);}", name, page=self.page)

    async def removeMyProfilePicture_(self):
        return await self.ThreadsafeBrowser.page_evaluate("() => WPP.profile.removeMyProfilePicture()", page=self.page)
