from __future__ import annotations

from typing import Optional
from WPP_Whatsapp.api.layers.StatusLayer import StatusLayer
from WPP_Whatsapp.api.model import BusinessProfileOptions

from WPP_Whatsapp.core.sync_api import sync_wrapper


class ProfileLayer(StatusLayer):
    @sync_wrapper("sendMute_")
    def sendMute(self, chatId, time, type_, timeout=60):
        ...

    @sync_wrapper("setTheme_")
    def setTheme(self, type_, timeout=60):
        ...

    @sync_wrapper("setProfileStatus_")
    def setProfileStatus(self, status, timeout=60):
        """
          /**
           * Sets current user profile status
           * @category Profile
           * @param status
           */
        """
        ...

    @sync_wrapper("getProfileStatus_")
    def getProfileStatus(self, timeout=60):
        ...

    @sync_wrapper("getProfileName_")
    def getProfileName(self, timeout=60):
        """Get profile name"""
        ...

    @sync_wrapper("setProfilePic_")
    def setProfilePic(self, pathOrBase64, to=None, timeout=60):
        ...

    @sync_wrapper("setProfileName_")
    def setProfileName(self, name, timeout=60):
        ...

    @sync_wrapper("removeMyProfilePicture_")
    def removeMyProfilePicture(self, timeout=60):
        ...

    @sync_wrapper("editBusinessProfile_")
    def editBusinessProfile(self, options: BusinessProfileOptions, timeout=60):
        """Update business profile"""
        ...

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
        return await self._evaluate_js('ProfileLayer.sendMute_.0',
                                                          {"id": chatId, "time": time, "type": type}, page=self.page)

    async def setTheme_(self, type_):
        """
           * Change the theme
           * @category Host
           * @param string types "dark" or "light"
        """
        return await self._evaluate_js('ProfileLayer.setTheme_.0', type_, page=self.page)

    async def setProfileStatus_(self, status):
        """
          /**
           * Sets current user profile status
           * @category Profile
           * @param status
           */
        """
        return await self._evaluate_js(
            'ProfileLayer.setProfileStatus_.0', status, page=self.page)

    async def getProfileStatus_(self):
        return await self._evaluate_js('ProfileLayer.getProfileStatus_.0', page=self.page)

    async def getProfileName_(self):
        """Get profile name - async implementation"""
        return await self._evaluate_js('ProfileLayer.getProfileName_.0', page=self.page)

    async def editBusinessProfile_(self, options: BusinessProfileOptions):
        """Edit business profile - async implementation"""
        options = dict(options)
        for old, new in [('websites', 'website'), ('hours', 'businessHours')]:
            if old in options and new not in options:
                options[new] = options.pop(old)
        return await self._evaluate_js(
            'ProfileLayer.editBusinessProfile_.0',
            {"options": options},
            page=self.page
        )
    async def setProfilePic_(self, pathOrBase64, to=None):
        base64 = await self._media_to_base64(pathOrBase64, 'image')
        if to:
            return await self._evaluate_js(
                'ProfileLayer.setProfilePic_.1',
                {"to": self.valid_chatId(to), "base64": base64}, page=self.page)
        return await self._evaluate_js(
            'ProfileLayer.setProfilePic_.0', base64, page=self.page)
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
        return await self._evaluate_js(
            'ProfileLayer.setProfileName_.0', name, page=self.page)

    async def removeMyProfilePicture_(self):
        return await self._evaluate_js('ProfileLayer.removeMyProfilePicture_.0', page=self.page)
