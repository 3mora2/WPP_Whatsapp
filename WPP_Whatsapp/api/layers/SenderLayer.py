from __future__ import annotations

import os
import asyncio
from typing import Optional, List, Union
from WPP_Whatsapp.api.layers.ListenerLayer import ListenerLayer
from WPP_Whatsapp.api.helpers.download_file import downloadFileToBase64
from WPP_Whatsapp.utils.ffmpeg import convertToMP4GIF
from WPP_Whatsapp.api.model import (
    SendTextOptions,
    SendFileOptions,
    SendImageOptions,
    SendVideoOptions,
    SendAudioOptions,
    SendStickerOptions,
    SendLocationOptions,
    SendListMessageOptions,
    ForwardMessageOptions,
    MentionOptions,
    PollOptions,
    OrderItem,
    OrderMessageOptions,
)


class SenderLayer(ListenerLayer):

    def sendLinkPreview(self, chatId, url, text='', timeout=120):
        """
        * Automatically sends a link with the auto generated link preview. You can also add a custom message to be added.
        * Deprecated: please use {@link sendText}
        """
        return self.ThreadsafeBrowser.run_threadsafe(self.sendLinkPreview_, chatId, url, text, timeout_=timeout)

    def sendText(self, to: str, content: str, options: Optional[SendTextOptions] = None, timeout=60):
        """
           Sends a text message to given chat
           @category Chat
           @param to chat to: xxxxx@us.c
           @param content text message
           @param options dict
           @param timeout
           @example
           // Simple message
           client.sendText('<number>@c.us', 'A simple message')
           :return: dict
        """
        return self.ThreadsafeBrowser.run_threadsafe(self.sendText_, to, content, options, timeout_=timeout)

    def sendPixKey(self, to, params, options=None, timeout=60):
        return self.ThreadsafeBrowser.run_threadsafe(self.sendPixKey_, to, params, options, timeout_=timeout)

    def sendMessageOptions(self, chat, content, options=None, timeout=60):
        return self.ThreadsafeBrowser.run_threadsafe(self.sendMessageOptions_, chat, content, options, timeout_=timeout)

    def sendImage(self, to: str, filePath: str, filename: str = "", caption: str = "", quotedMessageId: Optional[str] = None, isViewOnce: Optional[bool] = None, options: Optional[SendImageOptions] = None, timeout=120):
        return self.ThreadsafeBrowser.run_threadsafe(
            self.sendImage_, to, filePath, filename, caption,
            quotedMessageId, isViewOnce, options, timeout_=timeout)

    def reply(self, to, content, quotedMsg, timeout=60):
        """
            @param to chat to: xxxxx@us.c
            @param content text message
            @param quotedMsg: @param quotedMsg Message id to reply to.
            @example
           // Simple message
           client.reply('<number>@c.us', 'A simple message', '<message-id>')
        """
        return self.ThreadsafeBrowser.run_threadsafe(
            self.reply_, to, content, quotedMsg, timeout_=timeout)

    def sendPtt(self, to: str, pathOrBase64: str, filename: str = None, caption: str = None,
                quotedMessageId: str = None, messageId: str = None):
        return self.ThreadsafeBrowser.run_threadsafe(
            self.sendPtt_, to, pathOrBase64, filename, caption, quotedMessageId, messageId)

    def sendFile(self, to, pathOrBase64, nameOrOptions=None, caption="", timeout=60):
        return self.ThreadsafeBrowser.run_threadsafe(
            self.sendFile_, to, pathOrBase64, nameOrOptions, caption, timeout_=timeout)

    def sendVideoAsGif(self, to: str, filePath: str, filename: str = "", caption: str = "", timeout=60):
        return self.ThreadsafeBrowser.run_threadsafe(
            self.sendVideoAsGif_, to, filePath, filename, caption, timeout_=timeout)

    def sendGif(self, to, filePath, filename="", caption="", timeout=60):
        return self.ThreadsafeBrowser.run_threadsafe(
            self.sendGif_, to, filePath, filename, caption, timeout_=timeout)

    def sendContactVcard(self, to, contactsId, name=None, timeout=60):
        """
          /**
           * Sends contact card to iven chat id
           * @category Chat
           * @param to Chat id
           * @param contactsId Example: 0000@c.us | [000@c.us, 1111@c.us]
           */
        """
        return self.ThreadsafeBrowser.run_threadsafe(
            self.sendContactVcard_, to, contactsId, name, timeout_=timeout)

    def forwardMessages(self, toChatId: str, msgId: Union[str, List[str]], options: Optional[ForwardMessageOptions] = None, timeout=60):
        if options is None:
            options = {}
        # options = {
        #     "displayCaptionText": bool;
        # "multicast": bool;
        # }
        return self.ThreadsafeBrowser.run_threadsafe(
            self.forwardMessages_, toChatId, msgId, options, timeout_=timeout)

    def forwardMessagesV2(self, toChatId: str, messages: Union[str, List[str]], options: Optional[ForwardMessageOptions] = None, timeout=60):
        return self.ThreadsafeBrowser.run_threadsafe(
            self.forwardMessagesV2_, toChatId, messages, options, timeout_=timeout)

    def sendLocation(self, to: str, options: SendLocationOptions, timeout=60):
        return self.ThreadsafeBrowser.run_threadsafe(
            self.sendLocation_, to, options, timeout_=timeout)

    def sendSeen(self, chatId, timeout=60):
        return self.ThreadsafeBrowser.run_threadsafe(
            self.sendSeen_, chatId, timeout_=timeout)

    def startTyping(self, to, duration=None, timeout=60):
        return self.ThreadsafeBrowser.run_threadsafe(
            self.startTyping_, to, duration, timeout_=timeout)

    def stopTyping(self, to, timeout=60):
        return self.ThreadsafeBrowser.run_threadsafe(
            self.stopTyping_, to, timeout_=timeout)

    def sendImageAsSticker(self, to: str, pathOrBase64: str, options: Optional[SendStickerOptions] = None, timeout=60):
        return self.ThreadsafeBrowser.run_threadsafe(
            self.sendImageAsSticker_, to, pathOrBase64, options, timeout_=timeout)

    def setOnlinePresence(self, online=True, timeout=60):
        return self.ThreadsafeBrowser.run_threadsafe(
            self.setOnlinePresence_, online, timeout_=timeout)

    def sendMentioned(self, to: str, message: str, mentioned: List[str], options: Optional[MentionOptions] = None, timeout=60):
        return self.ThreadsafeBrowser.run_threadsafe(self.sendMentioned_, to, message, mentioned, options, timeout_=timeout)

    def sendListMessage(self, to: str, options: SendListMessageOptions, timeout=60):
        """
          /**
           * Sends a list message
           *
           * ```typescript
           *   // Example
           *   client.sendListMessage('<number>@c.us', {
           *     buttonText: 'Click here',
           *     description: 'Choose one option',
           *     sections: [
           *       {
           *         title: 'Section 1',
           *         rows: [
           *           {
           *             rowId: 'my_custom_id',
           *             title: 'Test 1',
           *             description: 'Description 1',
           *           },
           *           {
           *             rowId: '2',
           *             title: 'Test 2',
           *             description: 'Description 2',
           *           },
           *         ],
           *       },
           *     ],
           *   });
           * ```
           *
           * @category Chat
           */
        """
        return self.ThreadsafeBrowser.run_threadsafe(self.sendListMessage_(to, options), timeout_=timeout)

    def setChatState(self, chatId, chatState, timeout=60):
        """
          /**
           * Sets the chat state
           * Deprecated in favor of Use startTyping or startRecording functions
           * @category Chat
           * @param chatState   Typing = 0, Recording = 1, Paused = 2
           * @param chatId
           * @deprecated Deprecated in favor of Use startTyping or startRecording functions
           */
        """
        return self.ThreadsafeBrowser.run_threadsafe(
            self.setChatState_, chatId, chatState, timeout_=timeout)

    def sendPollMessage(self, chatId: str, name: str, choices: List[str], options: Optional[PollOptions] = None, timeout=60):
        """
        Send a poll message

        @param chatId: Chat ID
        @param name: Poll question
        @param choices: List of poll options
        @param options: Poll options (selectableCount, etc)
        @return: Success status
        """
        return self.ThreadsafeBrowser.run_threadsafe(
            self.sendPollMessage_, chatId, name, choices, options, timeout_=timeout)

    def sendOrderMessage(self, to: str, items: List[OrderItem], options: Optional[OrderMessageOptions] = None, timeout=60):
        """
        Send an order message

        @param to: Chat ID
        @param items: List of order items
        @param options: Order options
        @return: Success status
        """
        return self.ThreadsafeBrowser.run_threadsafe(
            self.sendOrderMessage_, to, items, options, timeout_=timeout)

    def sendWatermarkMessage(self, to: str, content: str, watermark: str = "Sent via WPPConnect", options: Optional[SendTextOptions] = None, timeout=60):
        """
        Send a text message with watermark/branding

        @param to: Chat ID
        @param content: Message content
        @param watermark: Watermark text to append
        @param options: Message options
        @return: Success status
        """
        return self.ThreadsafeBrowser.run_threadsafe(
            self.sendWatermarkMessage_, to, content, watermark, options, timeout_=timeout)

    ####################################################### async ######################################################

    async def sendPollMessage_(self, chatId: str, name: str, choices: List[str], options: Optional[PollOptions] = None):
        """Send a poll message - async implementation"""
        if options is None:
            options = {}
        chatId = self.valid_chatId(chatId)
        return await self._evaluate_js(
            'SenderLayer.sendPollMessage_.0',
            {"chatId": chatId, "name": name, "choices": choices, "options": options},
            page=self.page
        )

    async def sendOrderMessage_(self, to: str, items: List[OrderItem], options: Optional[OrderMessageOptions] = None):
        """Send an order message - async implementation"""
        if options is None:
            options = {}
        to = self.valid_chatId(to)
        normalized_items = []
        for item in items:
            item = dict(item)
            if 'productId' in item:
                item.setdefault('id', item.pop('productId'))
                item.setdefault('type', 'product')
            if 'quantity' in item:
                item.setdefault('qnt', item.pop('quantity'))
            normalized_items.append(item)
        items = normalized_items
        return await self._evaluate_js(
            'SenderLayer.sendOrderMessage_.0',
            {"to": to, "items": items, "options": options},
            page=self.page
        )

    async def sendWatermarkMessage_(self, to: str, content: str, watermark: str = "Sent via WPPConnect", options: Optional[SendTextOptions] = None):
        """Send a watermark message - async implementation"""
        if options is None:
            options = {}
        to = self.valid_chatId(to)
        watermarked_content = f"{content}\n\n_{watermark}_"
        return await self._evaluate_js(
            'SenderLayer.sendWatermarkMessage_.0',
            {"to": to, "content": watermarked_content, "options": options},
            page=self.page
        )

    async def sendLinkPreview_(self, chatId, url, text=''):
        message = text if url in text else f"{text}\n{url}"
        chatId = self.valid_chatId(chatId)
        result = await self._evaluate_js('SenderLayer.sendLinkPreview_.0', {"chatId": chatId, "message": message}, page=self.page)
        return result

    async def sendText_(self, to, content, options=None):
        if not options:
            options = {}
        if 'mentions' in options and 'mentionedList' not in options:
            options = {**options, 'mentionedList': options['mentions']}
        to = self.valid_chatId(to)
        send_result = await self._evaluate_js('SenderLayer.sendText_.0', {"to": to, "content": content, "options": options}, page=self.page)
        self.logger.debug(f'{self.session}: Send Message {send_result=}')

        return send_result

    async def sendPixKey_(self, to, params, options=None):
        if not options:
            options = {}
        to = self.valid_chatId(to)
        send_result = await self._evaluate_js('SenderLayer.sendPixKey_.0', {"to": to, "params": params, "options": options}, page=self.page)
        self.logger.debug(f'{self.session}: Send Message {send_result=}')

        result = await self._evaluate_js('SenderLayer.sendPixKey_.1', {"messageId": send_result.get("id"), }, page=self.page)

        return result

    async def sendMessageOptions_(self, chat, content, options=None):
        if not options:
            options = {}
        message_id = await self._evaluate_js('SenderLayer.sendMessageOptions_.0', {"chat": chat, "content": content, "options": options}, page=self.page)
        result = await self._evaluate_js('SenderLayer.sendMessageOptions_.1',
                                                            message_id, page=self.page)
        return result

    async def sendImage_(self, to, filePath, filename="", caption="", quotedMessageId=None, isViewOnce=None, options=None):
        to = self.valid_chatId(to)
        _base64 = await self._media_to_base64(filePath, 'image')
        filename = filename or (os.path.basename(filePath) if not filePath.startswith('data:') else '')
        return await self.sendImageFromBase64_(to, _base64, filename, caption, quotedMessageId, isViewOnce, options=options)

    async def sendImageFromBase64_(
        self,
        to,
        _base64,
        filename="",
        caption="",
        quotedMessageId=None,
        isViewOnce=None,
        mentionedList=None,
        options=None,
    ):
        to = self.valid_chatId(to)
        if options is None:
            options = {}
        if mentionedList is None and options:
            mentionedList = options.get("mentionedList")

        mime_type = self.base64MimeType(_base64)
        if not mime_type:
            raise Exception("Not valid mimeType")

        if 'image' not in mime_type:
            raise Exception('Not an image, allowed formats png, jpeg and webp')

        # filename = filenameFromMimeType(filename, mimeType)
        result = await self._evaluate_js('SenderLayer.sendImageFromBase64_.0', {
            "to": to,
            "base64": _base64,
            "filename": filename,
            "caption": caption,
            "quotedMessageId": quotedMessageId,
            "isViewOnce": isViewOnce,
            "mentionedList": mentionedList,
            "options":options
        }, page=self.page)
        return result

    async def reply_(self, to, content, quotedMsg):
        """
            @param to chat to: xxxxx@us.c
            @param content text message
            @param quotedMsg: @param quotedMsg Message id to reply to.
            @example
           // Simple message
           client.reply('<number>@c.us', 'A simple message', '<message-id>')
        """
        to = self.valid_chatId(to)
        result = await self._evaluate_js('SenderLayer.reply_.0', {"to": to, "content": content, "quotedMsg": quotedMsg}, page=self.page)
        # message = await self.ThreadsafeBrowser.page_evaluate()("(messageId) => WAPI.getMessageById(messageId)", result.get("id"), page=self.page)
        return result

    async def sendPttFromBase64(
            self,
            to: str,
            base64: str,
            filename: str,
            caption: str = None,
            quotedMessageId: str = None,
            messageId: str = None
    ):
        to = self.valid_chatId(to)
        result = await self._evaluate_js(
            'SenderLayer.sendPttFromBase64.0',
            {
                'to': to,
                'base64': base64,
                'filename': filename,
                'caption': caption,
                'quotedMessageId': quotedMessageId,
                'messageId': messageId
            }
            , page=self.page
        )
        return result

    async def sendPtt_(
            self,
            to: str,
            pathOrBase64: str,
            filename: str = None,
            caption: str = None,
            quotedMessageId: str = None,
            messageId: str = None
    ):

        base64 = ''
        if pathOrBase64.startswith('data:'):
            _base64 = pathOrBase64
        else:
            _base64 = await downloadFileToBase64(pathOrBase64)
            if not _base64:
                if pathOrBase64 and os.path.exists(pathOrBase64):
                    _base64 = self.fileToBase64(pathOrBase64)
            if not filename:
                filename = os.path.basename(pathOrBase64)

        if not _base64:
            raise Exception("Empty or invalid file or base64")

        return await self.sendPttFromBase64(
            self.valid_chatId(to),
            _base64,
            filename,
            caption,
            quotedMessageId,
            messageId
        )

    async def sendFile_(self, to, pathOrBase64, nameOrOptions=None, caption=""):
        to = self.valid_chatId(to)
        options = {"type": 'auto-detect'}
        if type(nameOrOptions) is str:
            options["filename"] = nameOrOptions
            options["caption"] = caption

        elif type(nameOrOptions) is dict:
            options = {**options, **nameOrOptions}

        _base64 = ''
        if pathOrBase64.startswith('data:'):
            _base64 = pathOrBase64
        else:
            _base64 = await downloadFileToBase64(pathOrBase64)
            if not _base64:
                if pathOrBase64 and os.path.exists(pathOrBase64):
                    _base64 = self.fileToBase64(pathOrBase64)

            if not options.get("filename"):
                options["filename"] = os.path.basename(pathOrBase64)
        if not _base64:
            raise Exception("Empty or invalid file or base64")

        return await self._evaluate_js('SenderLayer.sendFile_.0', {"to": to, "base64": _base64, "options": options}, page=self.page)

    async def sendVideoAsGif_(self, to: str, filePath: str, filename: str = "", caption: str = ""):
        """
          /**
           * Sends a video to given chat as a gif, with caption or not
           * @category Chat
           * @param to Chat id
           * @param filePath File path
           * @param filename
           * @param caption
           */
        """
        base64_ = await self._media_to_base64(filePath, 'video')

        if not base64_:
            raise Exception(f'No such file or directory, open "{filePath}"')

        if not filename:
            filename = os.path.basename(filePath)

        return await self.sendVideoAsGifFromBase64(to, base64_, filename, caption)

    async def sendVideoAsGifFromBase64(self, to, base64, filename, caption="", quotedMessageId=""):
        """
          /**
           * Sends a video to given chat as a gif, with caption or not, using base64
           * @category Chat
           * @param to chat id xxxxx@us.c
           * @param base64 base64 data:video/xxx;base64,xxx
           * @param filename string xxxxx
           * @param caption string xxxxx
           */
        """

        to = self.valid_chatId(to)
        result = await self._evaluate_js(
            'SenderLayer.sendVideoAsGifFromBase64.0',
            {"to": to, "base64": base64, "filename": filename, "caption": caption, "quotedMessageId": quotedMessageId}
            , page=self.page
        )
        return result

    async def sendGif_(self, to, filePath, filename="", caption=""):
        """
          /**
           * Sends a video to given chat as a gif, with caption or not, using base64
           * @category Chat
           * @param to Chat id
           * @param filePath File path
           * @param filename
           * @param caption
           */

        """
        base64_ = await self._media_to_base64(filePath, 'image')

        if not base64_:
            raise Exception(f'No such file or directory, open "{filePath}"')
        if not filename:
            filename = os.path.basename(filePath)

        return await self.sendGifFromBase64(to, base64_, filename, caption)

    async def sendGifFromBase64(self, to, base64_, filename, caption=""):
        """
          /**
           * Sends a video to given chat as a gif, with caption or not, using base64
           * @category Chat
           * @param to chat id xxxxx@us.c
           * @param base64 base64 data:video/xxx;base64,xxx
           * @param filename string xxxxx
           * @param caption string xxxxx
           */
        """
        base64_ = await asyncio.to_thread(convertToMP4GIF, base64_)

        return await self.sendVideoAsGifFromBase64(to, base64_, filename, caption)

    async def sendContactVcard_(self, to, contactsId, name=None):
        """
          /**
           * Sends contact card to iven chat id
           * @category Chat
           * @param to Chat id
           * @param contactsId Example: 0000@c.us | [000@c.us, 1111@c.us]
           */
        """
        to = self.valid_chatId(to)
        return await self._evaluate_js('SenderLayer.sendContactVcard_.0', {"to": to, "contactsId": contactsId, "name": name}, page=self.page)

    async def forwardMessages_(self, toChatId: str, msgId: str | list[str], options=None):
        if options is None:
            options = {}
        # {
        #     displayCaptionText?: boolean;
        # multicast?: boolean;
        # }
        toChatId = self.valid_chatId(toChatId)
        if isinstance(msgId, (list, tuple)):
            return await self.forwardMessagesV2_(toChatId, list(msgId), options)
        return await self._evaluate_js(
            'SenderLayer.forwardMessages_.0',
            {"toChatId": toChatId, "msgId": msgId,
             "options": options}, page=self.page)
        # return await self.ThreadsafeBrowser.page_evaluate("""({ to, messages, skipMyMessages }) =>
        # WAPI.forwardMessages(to, messages, skipMyMessages)""",
        #                                                   {"to": to, "messages": messages,
        #                                                    "skipMyMessages": skipMyMessages}, page=self.page)

    async def forwardMessagesV2_(self, toChatId: str, messages: str | list[str], options=None):
        if options is None:
            options = {}
        return await self._evaluate_js('SenderLayer.forwardMessagesV2_.0', { "toChatId":toChatId, "messages":messages, "options":options }, page=self.page)

    def sendImageAsStickerGif(self, to, pathOrBase64, options=None, timeout=120):
        return self.ThreadsafeBrowser.run_threadsafe(self.sendImageAsStickerGif_, to, pathOrBase64, options, timeout_=timeout)

    async def sendImageAsStickerGif_(self, to, pathOrBase64, options=None):
        import base64
        from io import BytesIO
        from PIL import Image

        content = await self._media_to_base64(pathOrBase64, 'image')
        raw = base64.b64decode(content.split(',', 1)[1], validate=True)
        with Image.open(BytesIO(raw)) as image:
            output = BytesIO()
            image.save(output, format='WEBP', save_all=True, loop=image.info.get('loop', 0))
        webp = 'data:image/webp;base64,' + base64.b64encode(output.getvalue()).decode('ascii')
        return await self.sendImageAsSticker_(to, webp, options)

    async def sendLocation_(self, to, options):
        to = self.valid_chatId(to)
        options = {
            **options,
            "lat": options.get("lat", options.get("latitude")),
            "lng": options.get("lng", options.get("longitude")),
            "title": options.get("title"),
        }
        return await self._evaluate_js('SenderLayer.sendLocation_.0', {"to": to, "options": options}, page=self.page)

    async def sendSeen_(self, chatId):
        chatId = self.valid_chatId(chatId)
        return await self._evaluate_js('SenderLayer.sendSeen_.0', chatId,
                                                          page=self.page)

    async def startTyping_(self, to, duration=None):
        to = self.valid_chatId(to)
        return await self._evaluate_js(
            'SenderLayer.startTyping_.0',
            {"to": to, "duration": duration}, page=self.page)

    async def stopTyping_(self, to):
        to = self.valid_chatId(to)
        return await self._evaluate_js('SenderLayer.stopTyping_.0', to, page=self.page)

    async def sendImageAsSticker_(self, to: str, pathOrBase64: str, options=None):
        if options is None:
            options = {}
        to = self.valid_chatId(to)
        _base64 = ''
        if pathOrBase64.startswith('data:'):
            _base64 = pathOrBase64
        else:
            _base64 = await downloadFileToBase64(pathOrBase64, [
                'image/gif',
                'image/png',
                'image/jpg',
                'image/jpeg',
                'image/webp',
            ])
            if not _base64:
                if pathOrBase64 and os.path.exists(pathOrBase64):
                    _base64 = self.fileToBase64(pathOrBase64)

        if not _base64:
            raise Exception("Empty or invalid file or base64")

        mime_type = self.base64MimeType(_base64)
        if not mime_type or 'image' not in mime_type:
            raise Exception('Not an image, allowed formats png, jpeg, webp and gif')

        return await self._evaluate_js('SenderLayer.sendImageAsSticker_.0', {"to": to, "base64": _base64, "options": options}, page=self.page)

    async def setOnlinePresence_(self, online=True):
        return await self._evaluate_js('SenderLayer.setOnlinePresence_.0', online,
                                                          page=self.page)

    async def sendMentioned_(self, to:str, message:str, mentioned:list[str], options=None):
        to = self.valid_chatId(to)

        return await self._evaluate_js(
            'SenderLayer.sendMentioned_.0',
            {"to": to, "message": message, "mentioned": mentioned, "options": options or {}}, page=self.page)

    async def sendListMessage_(self, to, options):
        to = self.valid_chatId(to)
        """
          /**
           * Sends a list message
           *
           * ```typescript
           *   // Example
           *   client.sendListMessage('<number>@c.us', {
           *     buttonText: 'Click here',
           *     description: 'Choose one option',
           *     sections: [
           *       {
           *         title: 'Section 1',
           *         rows: [
           *           {
           *             rowId: 'my_custom_id',
           *             title: 'Test 1',
           *             description: 'Description 1',
           *           },
           *           {
           *             rowId: '2',
           *             title: 'Test 2',
           *             description: 'Description 2',
           *           },
           *         ],
           *       },
           *     ],
           *   });
           * ```
           *
           * @category Chat
           */
        """
        sendResult = await self._evaluate_js(
            'SenderLayer.sendListMessage_.0',
            {"to": to, "options": options}, page=self.page)
        # result = await self.ThreadsafeBrowser.page_evaluate("""async ({ messageId }) => {
        #                 return JSON.parse(JSON.stringify(await WAPI.getMessageById(messageId)));
        #               }""", sendResult.get("id"))
        return sendResult

    async def setChatState_(self, chatId, chatState):
        """
          /**
           * Sets the chat state
           * Deprecated in favor of Use startTyping or startRecording functions
           * @category Chat
           * @param chatState   Typing = 0, Recording = 1, Paused = 2
           * @param chatId
           * @deprecated Deprecated in favor of Use startTyping or startRecording functions
           */
        """
        chatId = self.valid_chatId(chatId)
        return await self._evaluate_js('SenderLayer.setChatState_.0', {"chatState": chatState, "chatId": chatId}, page=self.page)

    def sendContactVcardList(self, to, contacts, timeout=60):
        """Send multiple contact cards."""
        return self.ThreadsafeBrowser.run_threadsafe(self.sendContactVcardList_, to, contacts, timeout_=timeout)

    async def sendContactVcardList_(self, to, contacts):
        to = self.valid_chatId(to)
        return await self._evaluate_js(
            'SenderLayer.sendContactVcardList_.0', {"to": to, "contacts": contacts}, page=self.page)

    def markPlayed(self, msgId, timeout=60):
        """Mark an audio message as played."""
        return self.ThreadsafeBrowser.run_threadsafe(self.markPlayed_, msgId, timeout_=timeout)

    async def markPlayed_(self, msgId):
        return await self._evaluate_js(
            'SenderLayer.markPlayed_.0', {"msgId": msgId}, page=self.page)

    def startRecording(self, to, duration=None, timeout=60):
        """Set recording presence for a chat."""
        return self.ThreadsafeBrowser.run_threadsafe(self.startRecording_, to, duration, timeout_=timeout)

    async def startRecording_(self, to, duration=None):
        to = self.valid_chatId(to)
        return await self._evaluate_js(
            'SenderLayer.startRecording_.0', {"to": to, "duration": duration}, page=self.page)

    def stopRecording(self, to, timeout=60):
        """Stop recording presence."""
        return self.ThreadsafeBrowser.run_threadsafe(self.stopRecording_, to, timeout_=timeout)

    async def stopRecording_(self, to):
        to = self.valid_chatId(to)
        return await self._evaluate_js(
            'SenderLayer.stopRecording_.0', {"to": to}, page=self.page)

    def sendReactionToMessage(self, msgId, reaction, timeout=60):
        """React to a message; false removes the reaction."""
        return self.ThreadsafeBrowser.run_threadsafe(self.sendReactionToMessage_, msgId, reaction, timeout_=timeout)

    async def sendReactionToMessage_(self, msgId, reaction):
        return await self._evaluate_js(
            'SenderLayer.sendReactionToMessage_.0', {"msgId": msgId, "reaction": reaction}, page=self.page)

    def sendMessageWithThumb(self, thumb, url, title, description, chatId, timeout=60):
        """Send a link with a custom preview."""
        return self.ThreadsafeBrowser.run_threadsafe(self.sendMessageWithThumb_, thumb, url, title, description, chatId, timeout_=timeout)

    async def sendMessageWithThumb_(self, thumb, url, title, description, chatId):
        chatId = self.valid_chatId(chatId)
        return await self._evaluate_js(
            'SenderLayer.sendMessageWithThumb_.0', {"thumb": thumb, "url": url, "title": title, "description": description, "chatId": chatId}, page=self.page)

    def sendImageFromBase64(self, to, base64, filename='', caption='', quotedMessageId=None,
                            isViewOnce=None, mentionedList=None, options=None, timeout=120):
        return self.ThreadsafeBrowser.run_threadsafe(self.sendImageFromBase64_, self.valid_chatId(to),
            base64, filename, caption, quotedMessageId, isViewOnce, mentionedList, options, timeout_=timeout)

    def sendFileFromBase64(self, to, base64, filename='', caption='', options=None, timeout=120):
        return self.ThreadsafeBrowser.run_threadsafe(self.sendFileFromBase64_, to, base64, filename, caption, options, timeout_=timeout)

    async def sendFileFromBase64_(self, to, base64, filename='', caption='', options=None):
        opts = {'filename': filename, 'caption': caption, **(options or {})}
        return await self.sendFile_(to, base64, opts, caption)

    def forwardMessage(self, toChatId, msgId, options=None, timeout=60):
        return self.ThreadsafeBrowser.run_threadsafe(self.forwardMessages_, toChatId, msgId, options, timeout_=timeout)

    async def forwardMessage_(self, toChatId, msgId, options=None):
        return await self.forwardMessages_(toChatId, msgId, options)

    def stopRecoring(self, to, timeout=60):
        """Compatibility spelling; use stopRecording."""
        return self.stopRecording(to, timeout=timeout)

    async def stopRecoring_(self, to):
        return await self.stopRecording_(to)

    async def sendPttFromBase64_(self, to, base64, filename='', caption=None, quotedMessageId=None, messageId=None):
        return await self.sendPttFromBase64(self.valid_chatId(to), base64, filename, caption, quotedMessageId, messageId)

    async def sendVideoAsGifFromBase64_(self, to, base64, filename='', caption='', quotedMessageId=''):
        return await self.sendVideoAsGifFromBase64(self.valid_chatId(to), base64, filename, caption, quotedMessageId)

    async def sendGifFromBase64_(self, to, base64, filename='', caption=''):
        return await self.sendGifFromBase64(self.valid_chatId(to), base64, filename, caption)
