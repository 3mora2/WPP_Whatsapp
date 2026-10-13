// WPP_Whatsapp compatibility for current WhatsApp message keys and history APIs.
// Kept separate so the official WPPConnect bundle can be updated unchanged.
(() => {
  const ready = WPP.isReady
    ? Promise.resolve()
    : new Promise((resolve) => WPP.loader.onReady(resolve));

  window.__wppWhatsappReady = ready.then(() => {
    function serializeId(value) {
      if (value == null) return undefined;
      if (typeof value === 'string') return value;
      if (value._serialized) return value._serialized;
      // Recent MsgKey implementations cache the full key in a minified field.
      // The native toString() still returns the complete key, including the
      // participant suffix for group messages.
      const text = value.toString?.();
      if (text && text !== '[object Object]') return text;
      if (value.id && value.remote && typeof value.fromMe === 'boolean') {
        const parts = [value.fromMe, serializeId(value.remote), value.id];
        if (value.participant) parts.push(serializeId(value.participant));
        return parts.join('_');
      }
      return undefined;
    }

    const originalSerialize = WAPI._serializeMessageObj;
    WAPI._serializeMessageObj = (msg) => {
      if (msg == null) return null;
      let result;
      try {
        result = originalSerialize(msg);
      } catch (error) {
        // Preserve the message when optional sender/media serialization fails.
        try {
          result = WAPI._serializeRawObj(msg);
        } catch (_) {
          result = {};
        }
      }
      return Object.assign({}, result, {
        id: serializeId(msg.id),
        from: serializeId(msg.from),
        to: serializeId(msg.to),
        author: serializeId(msg.author),
        chatId: serializeId(msg.id?.remote || msg.chatId || msg.from),
        quotedParticipant: serializeId(msg.quotedParticipant),
        quotedMsgId: serializeId(msg._quotedMsgObj?.id) || result?.quotedMsgId,
        fromMe: msg.id?.fromMe ?? msg.fromMe ?? msg.isSentByMe,
        body: msg.body ?? result?.body ?? '',
        content: msg.body ?? result?.content ?? '',
        timestamp: msg.t ?? result?.timestamp,
        t: msg.t ?? result?.t,
        type: msg.type ?? result?.type,
        isGroupMsg: msg.isGroupMsg ?? serializeId(msg.id?.remote || msg.from)?.endsWith('@g.us'),
        isNotification: msg.isNotification,
      });
    };

    WAPI.processMessageObj = (msg, includeMe, includeNotifications) => {
      if (msg.isNotification) {
        return includeNotifications ? WAPI._serializeMessageObj(msg) : undefined;
      }
      const fromMe = msg.id?.fromMe ?? msg.fromMe ?? msg.isSentByMe;
      if (fromMe !== true || includeMe) return WAPI._serializeMessageObj(msg);
    };

    WAPI.getMessages = async (chatId, params = {}) => {
      const messages = await WPP.chat.getMessages(chatId, params);
      if (!Array.isArray(messages)) {
        throw Object.assign(new Error(`Failed to fetch messages for ${chatId}`), messages);
      }
      // WA-JS already returns MsgModel instances. Reconstructing them can
      // discard prototype getters, including the message key.
      return messages.map((msg) => WAPI.processMessageObj(msg, true, true));
    };

    WAPI.getAllMessagesInChat = async (chatId, includeMe, includeNotifications) => {
      const chat = await WPP.chat.get(chatId);
      return chat.msgs.getModelsArray()
        .map((msg) => WAPI.processMessageObj(msg, includeMe, includeNotifications))
        .filter(Boolean);
    };

    WAPI.loadAndGetAllMessagesInChat = async (chatId, includeMe, includeNotifications) => {
      const messages = await WAPI.getMessages(chatId, { count: -1 });
      return messages.filter((msg) => msg.isNotification
        ? includeNotifications
        : includeMe || !msg.fromMe);
    };

    WAPI.loadEarlierMessages = async (chatId) => {
      const chat = await WPP.chat.get(chatId);
      const first = chat.msgs.getModelsArray()[0];
      const params = { count: 50, direction: 'before' };
      if (first) params.id = serializeId(first.id);
      return WAPI.getMessages(chatId, params);
    };
    WAPI._wppWhatsappReady = true;
  });
})();
