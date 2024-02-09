
import os
from WPP_Whatsapp.api.layers.ListenerLayer import ListenerLayer
from WPP_Whatsapp.api.helpers.download_file import downloadFileToBase64
from WPP_Whatsapp.utils.ffmpeg import convertToMP4GIF


class SenderLayer(ListenerLayer):

    def sendLinkPreview(self, chatId, url, text='', timeout=120):
        """
        * Automatically sends a link with the auto generated link preview. You can also add a custom message to be added.
        * Deprecated: please use {@link sendText}
        """
        return self.ThreadsafeBrowser.run_threadsafe(self.sendLinkPreview_, chatId, url, text, timeout_=timeout)

    def sendText(self, to, content, options=None, timeout=60):
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

    def sendMessageOptions(self, chat, content, options=None, timeout=60):
        return self.ThreadsafeBrowser.run_threadsafe(self.sendMessageOptions_, chat, content, options, timeout_=timeout)

    def sendImage(self, to, filePath, filename="", caption="", quotedMessageId=None, isViewOnce=None, timeout=120):
        return self.ThreadsafeBrowser.run_threadsafe(
            self.sendImage_, to, filePath, filename, caption,
            quotedMessageId, isViewOnce, timeout_=timeout)

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

    def sendFile(self, to, pathOrBase64, nameOrOptions, caption, timeout=60):
        return self.ThreadsafeBrowser.run_threadsafe(
            self.sendFile_, to, pathOrBase64, nameOrOptions, caption, timeout_=timeout)

    def sendVideoAsGif(self, to: str, filePath: str, filename: str = "", caption: str = "", timeout=60):
        return self.ThreadsafeBrowser.run_threadsafe(
            self.sendVideoAsGif_, to, filePath, filename, caption, timeout_=timeout)

    def sendGif(self, to, filePath, filename="", caption="", timeout=60):
        return self.ThreadsafeBrowser.run_threadsafe(
            self.sendGif_, to, filePath, filename, caption, timeout_=timeout)

    def sendContactVcard(self, to, contactsId, name, timeout=60):
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

    def forwardMessages(self, to, messages, skipMyMessages, timeout=60):
        return self.ThreadsafeBrowser.run_threadsafe(
            self.forwardMessages_, to, messages, skipMyMessages, timeout_=timeout)

    def sendLocation(self, to, options, timeout=60):
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

    def setOnlinePresence(self, online=True, timeout=60):
        return self.ThreadsafeBrowser.run_threadsafe(
            self.setOnlinePresence_, online, timeout_=timeout)

    def sendListMessage(self, to, options, timeout=60):
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
        return self.ThreadsafeBrowser.run_threadsafe(
            self.sendListMessage_, to, options, timeout_=timeout)

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

    ####################################################### async ######################################################

    async def sendLinkPreview_(self, chatId, url, text=''):
        message = text if url in text else f"{text}\n{url}"
        chatId = self.valid_chatId(chatId)
        result = await self.ThreadsafeBrowser.page_evaluate("""({ chatId, message }) => {
                    return WPP.chat.sendTextMessage(chatId, message, { linkPreview: true });
                    }""", {"chatId": chatId, "message": message})
        return result

    async def sendText_(self, to, content, options=None):
        if not options:
            options = {}
        to = self.valid_chatId(to)
        send_result = await self.ThreadsafeBrowser.page_evaluate("""({ to, content, options }) =>
                            WPP.chat.sendTextMessage(to, content, {
                              ...options,
                              waitForAck: true,
                            })""", {"to": to, "content": content, "options": options})
        self.logger.debug(f'{self.session}: Send Message {send_result=}')

        return send_result

    async def sendMessageOptions_(self, chat, content, options=None):
        if not options:
            options = {}
        message_id = await self.ThreadsafeBrowser.page_evaluate("""({ chat, content, options }) => {
        return WAPI.sendMessageOptions(chat, content, options);
      }""", {"chat": chat, "content": content, "options": options})
        result = await self.ThreadsafeBrowser.page_evaluate("""(messageId) => WAPI.getMessageById(messageId)""",
                                                            message_id)
        return result

    async def sendImage_(self, to, filePath, filename="", caption="", quotedMessageId=None, isViewOnce=None):
        to = self.valid_chatId(to)
        if filePath and os.path.exists(filePath):
            _base64 = self.convert_to_base64(filePath)
            filename = os.path.basename(filePath) if not filename else filename
            return await self.sendImageFromBase64_(to, _base64, filename, caption, quotedMessageId, isViewOnce)
        else:
            raise Exception("Path Not Found")

    async def sendImageFromBase64_(self, to, _base64, filename, caption, quotedMessageId, isViewOnce):
        mime_type = self.base64MimeType(_base64)
        if not mime_type:
            raise Exception("Not valid mimeType")

        if 'image' not in mime_type:
            raise Exception('Not an image, allowed formats png, jpeg and webp')

        # filename = filenameFromMimeType(filename, mimeType)
        result = await self.ThreadsafeBrowser.page_evaluate("""async ({
        to,
        base64,
        filename,
        caption,
        quotedMessageId,
        isViewOnce,
      }) => {
        const result = await WPP.chat.sendFileMessage(to, base64, {
          type: 'image',
          isViewOnce,
          filename,
          caption,
          quotedMsg: quotedMessageId,
          waitForAck: true,
        }).catch((e) => {return e});
        
        return {
          ack: result.ack,
          id: result.id,
          sendMsgResult: await result.sendMsgResult,
          error: result.message,
        };
      }""", {"to": to, "base64": _base64, "filename": filename, "caption": caption, "quotedMessageId": quotedMessageId,
             "isViewOnce": isViewOnce})
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
        result = await self.ThreadsafeBrowser.page_evaluate("""({ to, content, quotedMsg }) => {
                                    return WPP.chat.sendTextMessage(to, content, { quotedMsg });
                                  }""", {"to": to, "content": content, "quotedMsg": quotedMsg})
        # message = await self.ThreadsafeBrowser.page_evaluate()("(messageId) => WAPI.getMessageById(messageId)", result.get("id"))
        return result

    async def sendFile_(self, to, pathOrBase64, nameOrOptions, caption):
        to = self.valid_chatId(to)
        options = {"type": 'auto-detect'}
        if type(nameOrOptions) is str:
            options["filename"] = nameOrOptions
            options["caption"] = caption

        elif type(nameOrOptions) is dict:
            options = nameOrOptions

        _base64 = ''
        if pathOrBase64.startswith('data:'):
            _base64 = pathOrBase64
        else:
            if pathOrBase64 and os.path.exists(pathOrBase64):
                _base64 = self.convert_to_base64(pathOrBase64)

            if not options.get("filename"):
                options["filename"] = os.path.basename(pathOrBase64)
        if not _base64:
            raise Exception("Empty or invalid file or base64")

        return await self.ThreadsafeBrowser.page_evaluate("""async ({ to, base64, options }) => {
        const result = await WPP.chat.sendFileMessage(to, base64, options);
        return {
          ack: result.ack,
          id: result.id,
          sendMsgResult: await result.sendMsgResult,
        };
      }""", {"to": to, "base64": _base64, "options": options})

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
        base64_ = await downloadFileToBase64(filePath)

        if not base64_:
            base64_ = self.convert_to_base64(filePath)

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

        result = await self.ThreadsafeBrowser.page_evaluate(
            """
            async ({ to, base64, filename, caption, quotedMessageId }) => {
                const result = await WPP.chat.sendFileMessage(to, base64, {
                  type: 'video',
                  isGif: true,
                  filename,
                  caption,
                  quotedMsg: quotedMessageId,
                  waitForAck: true,
                });
        
                return {
                  ack: result.ack,
                  id: result.id,
                  sendMsgResult: await result.sendMsgResult,
                };
              }
      """,
            {"to": to, "base64": base64, "filename": filename, "caption": caption, "quotedMessageId": quotedMessageId}
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
        base64_ = await downloadFileToBase64(filePath)

        if not base64_:
            base64_ = self.convert_to_base64(filePath)

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
        base64_ = convertToMP4GIF(base64_)

        return await self.sendVideoAsGifFromBase64(to, base64_, filename, caption)

    async def sendContactVcard_(self, to, contactsId, name):
        """
          /**
           * Sends contact card to iven chat id
           * @category Chat
           * @param to Chat id
           * @param contactsId Example: 0000@c.us | [000@c.us, 1111@c.us]
           */
        """
        to = self.valid_chatId(to)
        return await self.ThreadsafeBrowser.page_evaluate("""({ to, contactsId, name }) => {
        return WPP.chat.sendVCardContactMessage(to, {
          id: contactsId,
          name: name,
        });
      }""", {"to": to, "contactsId": contactsId, "name": name})

    async def forwardMessages_(self, to, messages, skipMyMessages):
        to = self.valid_chatId(to)
        return await self.ThreadsafeBrowser.page_evaluate("""({ to, messages, skipMyMessages }) =>
        WAPI.forwardMessages(to, messages, skipMyMessages)""",
                                                          {"to": to, "messages": messages,
                                                           "skipMyMessages": skipMyMessages})

    async def sendLocation_(self, to, options):
        to = self.valid_chatId(to)
        options = {
            "lat": options.get("latitude"),
            "lng": options.get("longitude"),
            "title": options.get("title"),
        }
        return await self.ThreadsafeBrowser.page_evaluate("""async ({ to, options }) => {
        const result = await WPP.chat.sendLocationMessage(to, options);

        return {
          ack: result.ack,
          id: result.id,
          sendMsgResult: await result.sendMsgResult,
        };
      }""", {"to": to, "options": options})

    async def sendSeen_(self, chatId):
        chatId = self.valid_chatId(chatId)
        return await self.ThreadsafeBrowser.page_evaluate("(chatId) => WPP.chat.markIsRead(chatId)", chatId)

    async def startTyping_(self, to, duration=None):
        to = self.valid_chatId(to)
        return await self.ThreadsafeBrowser.page_evaluate(
            "({ to, duration }) => WPP.chat.markIsComposing(to, duration)",
            {"to": to, "duration": duration})

    async def stopTyping_(self, to):
        to = self.valid_chatId(to)
        return await self.ThreadsafeBrowser.page_evaluate("(to) => WPP.chat.markIsPaused(to)", to)

    async def setOnlinePresence_(self, online=True):
        return await self.ThreadsafeBrowser.page_evaluate("(online) => WPP.conn.markAvailable(online)", online)

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
        sendResult = await self.ThreadsafeBrowser.page_evaluate(
            "({ to, options }) => WPP.chat.sendListMessage(to, options)",
            {"to": to, "options": options})
        result = await self.ThreadsafeBrowser.page_evaluate("""async ({ messageId }) => {
                        return JSON.parse(JSON.stringify(await WAPI.getMessageById(messageId)));
                      }""", sendResult.get("id"))
        return result

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
        return await self.ThreadsafeBrowser.page_evaluate("""({ chatState, chatId }) => {
                WAPI.sendChatstate(chatState, chatId);
              }""", {"chatState": chatState, "chatId": chatId})

