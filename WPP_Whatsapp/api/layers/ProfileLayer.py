from WPP_Whatsapp.api.layers.StatusLayer import StatusLayer


class ProfileLayer(StatusLayer):
    def sendMute(self, chatId, time, type):
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
        return self.ThreadsafeBrowser.sync_page_evaluate("(id, time, type) => WAPI.sendMute(id, time, type)",
                                                         {"id": chatId, "time": time, "type": type})

    def setTheme(self, type_):
        """
           * Change the theme
           * @category Host
           * @param string types "dark" or "light"
        """
        return self.ThreadsafeBrowser.sync_page_evaluate("(type_) => WAPI.setTheme(type_)", type_)

    def setProfileStatus(self, status):
        """
          /**
           * Sets current user profile status
           * @category Profile
           * @param status
           */
        """
        return self.ThreadsafeBrowser.sync_page_evaluate("""({ status }) => {
            WPP.profile.setMyStatus(status);
          }""", status)

    def setProfilePic(self, pathOrBase64, to):
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

    def setProfileName(self, name):
        return self.ThreadsafeBrowser.sync_page_evaluate("({ name }) => {WAPI.setMyName(name);}", name)

    def removeMyProfilePicture(self):
        return self.ThreadsafeBrowser.sync_page_evaluate("() => WPP.profile.removeMyProfilePicture()")
