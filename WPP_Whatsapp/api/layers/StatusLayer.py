from WPP_Whatsapp.api.layers.LabelsLayer import LabelsLayer
from WPP_Whatsapp.api.helpers.download_file import downloadFileToBase64


class StatusLayer(LabelsLayer):
    def sendImageStatus(self, pathOrBase64: str, timeout=60):
        """
          /**
           * Send a image message to status stories
           * @category Status
           *
           * @example
           * ```javascript
           * client.sendImageStatus('data:image/jpeg;base64,<a long base64 file...>');
           * ```
           * @param pathOrBase64 Path or base 64 image
           */
        """
        return self.ThreadsafeBrowser.run_threadsafe(
            self.sendImageStatus_, pathOrBase64, timeout_=timeout)

    def sendVideoStatus(self, pathOrBase64: str, timeout=60):
        """
          /**
           * Send a video message to status stories
           * @category Status
           *
           * @example
           * ```javascript
           * client.sendVideoStatus('data:video/mp4;base64,<a long base64 file...>');
           * ```
           * @param pathOrBase64 Path or base 64 image
           */
        """
        return self.ThreadsafeBrowser.run_threadsafe(
            self.sendVideoStatus_, pathOrBase64, timeout_=timeout)

    def sendTextStatus(self, text: str, options: dict = {}, timeout=60):
        """
          /**
           * Send a text to status stories
           * @category Status
           *
           * @example
           * ```javascript
           * client.sendTextStatus(`Bootstrap primary color: #0275d8`, { backgroundColor: '#0275d8', font: 2});
           * ```
           * @param pathOrBase64 Path or base 64 image
           */
        """
        return self.ThreadsafeBrowser.run_threadsafe(
            self.sendTextStatus_, text, options, timeout_=timeout)

    def sendReadStatus(self, chatId: str, statusId: str, timeout=60):
        """/**
           * Mark status as read/seen
           * @category Status
           *
           * @example
           * ```javascript
           * client.sendReadStatus('[phone_number]@c.us', 'false_status@broadcast_3A169E0FD4BC6E92212F_[]@c.us');
           * ```
           * @param chatId Chat ID of contact
           * @param statusId ID of status msg
           */"""
        return self.ThreadsafeBrowser.run_threadsafe(
            self.sendReadStatus_, chatId, statusId, timeout_=timeout)

    ##########################################################################
    async def sendImageStatus_(self, pathOrBase64: str):
        """
          /**
           * Send a image message to status stories
           * @category Status
           *
           * @example
           * ```javascript
           * client.sendImageStatus('data:image/jpeg;base64,<a long base64 file...>');
           * ```
           * @param pathOrBase64 Path or base 64 image
           */
        """
        base64 = ''
        if pathOrBase64.startswith('data:'):
            base64 = pathOrBase64
        else:
            file_content = await downloadFileToBase64(pathOrBase64, [
                'image/gif',
                'image/png',
                'image/jpg',
                'image/jpeg',
                'image/webp',
            ])
            if not file_content:
                file_content = self.fileToBase64(pathOrBase64)
            if file_content:
                base64 = file_content

        if not base64:
            error = ValueError('Empty or invalid file or base64')
            error.code = 'empty_file'
            raise error

        mime_info = self.base64MimeTypeV2(base64)
        if not mime_info or 'image' not in mime_info:
            error = ValueError('Not an image, allowed formats png, jpeg and webp')
            error.code = 'invalid_image'
            raise error

        return await self.ThreadsafeBrowser.page_evaluate(
            """({base64}) => WPP.status.sendImageStatus(base64);""",
            {"base64": base64}, page=self.page
        )

    async def sendVideoStatus_(self, pathOrBase64: str):
        """
          /**
           * Send a video message to status stories
           * @category Status
           *
           * @example
           * ```javascript
           * client.sendVideoStatus('data:video/mp4;base64,<a long base64 file...>');
           * ```
           * @param pathOrBase64 Path or base 64 image
           */
        """
        base64 = ''
        if pathOrBase64.startswith('data:'):
            base64 = pathOrBase64
        else:
            file_content = await downloadFileToBase64(pathOrBase64)
            if not file_content:
                file_content = self.fileToBase64(pathOrBase64)
            if file_content:
                base64 = file_content

        if not base64:
            error = ValueError('Empty or invalid file or base64')
            error.code = 'empty_file'
            raise error

        return await self.ThreadsafeBrowser.page_evaluate(
            """({base64}) => WPP.status.sendVideoStatus(base64);""",
            {"base64": base64}, page=self.page
        )

    async def sendTextStatus_(self, text: str, options: str):
        """
          /**
           * Send a text to status stories
           * @category Status
           *
           * @example
           * ```javascript
           * client.sendTextStatus(`Bootstrap primary color: #0275d8`, { backgroundColor: '#0275d8', font: 2});
           * ```
           * @param pathOrBase64 Path or base 64 image
           */
        """
        return await self.ThreadsafeBrowser.page_evaluate(
            """({text, options}) => WPP.status.sendTextStatus(text, options);""",
            {"text": text, "options": options}, page=self.page
        )

    async def sendReadStatus_(self, chatId: str, statusId: str):
        """/**
           * Mark status as read/seen
           * @category Status
           *
           * @example
           * ```javascript
           * client.sendReadStatus('[phone_number]@c.us', 'false_status@broadcast_3A169E0FD4BC6E92212F_[]@c.us');
           * ```
           * @param chatId Chat ID of contact
           * @param statusId ID of status msg
           */"""
        return await self.ThreadsafeBrowser.page_evaluate(
            """({ chatId, statusId }) => WPP.status.sendReadStatus(chatId, statusId);""",
            {"chatId": chatId, "statusId": statusId}, page=self.page
        )
