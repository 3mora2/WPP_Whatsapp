(function() {
    function getStore(modules) {
        let foundCount = 0;
        let neededObjects = [
            { id: "Store", conditions: (module) => (module.default && module.default.Chat && module.default.Msg) ? module.default : null },
            { id: "MediaCollection", conditions: (module) => (module.default && module.default.prototype && module.default.prototype.processAttachments) ? module.default : null },
            { id: "MediaProcess", conditions: (module) => (module.BLOB) ? module : null },
            { id: "ServiceWorker", conditions: (module) => (module.default && module.default.killServiceWorker) ? module : null },
            { id: "State", conditions: (module) => (module.STATE && module.STREAM) ? module : null },
            { id: "WapDelete", conditions: (module) => (module.sendConversationDelete && module.sendConversationDelete.length == 2) ? module : null },
            { id: "WapQuery", conditions: (module) => (module.default && module.instance && module.instance.queryExist) ? module.instance : null },
            { id: "CryptoLib", conditions: (module) => (module.decryptE2EMedia) ? module : null },
            { id: "OpenChat", conditions: (module) => (module.default && module.default.prototype && module.default.prototype.openChat) ? module.default : null },
            { id: "UserConstructor", conditions: (module) => (module.default && module.default.prototype && module.default.prototype.isServer && module.default.prototype.isUser) ? module.default : null },
            { id: "SendTextMsgToChat", conditions: (module) => (module.sendTextMsgToChat) ? module.sendTextMsgToChat : null },
            { id: "sendDelete", conditions: (module) => (module.sendDelete) ? module.sendDelete : null },
            { id: "FeatureChecker", conditions: (module) => (module && module.getProtobufFeatureName) ? module : null },
            { id: "GetMaybeMeUser", conditions: (module) => (module && module.getMaybeMeUser) ? module : null },
            { id: "FindChat", conditions: (module) => module.findChat ? module : module.default && module.default.findChat ? module.default : null },
            { id: "QueryExist2", conditions: (module) => (module.queryExist) ? module : null },
            { id: "AppState", conditions: (module) => (module && module.Socket) ? module.Socket : null },
            { id: "Conn", conditions: (module) => (module && module.Conn) ? module.Conn : null },
            { id: "BlockContact", conditions: (module) => (module && module.blockContact) ? module : null },
            { id: "Call", conditions: (module) => (module && module.CallCollection) ? module.CallCollection : null },
            { id: "Cmd", conditions: (module) => (module && module.Cmd) ? module.Cmd : null },
            { id: "DownloadManager", conditions: (module) => (module && module.downloadManager) ? module.downloadManager : null },
            { id: "MDBackend", conditions: (module) => (module && module.isMDBackend) ? module.isMDBackend() : null },
            { id: "Features", conditions: (module) => (module && module.FEATURE_CHANGE_EVENT) ? module.LegacyPhoneFeatures : null },
            { id: "GroupMetadata", conditions: (module) => (module.default && module.default.handlePendingInvite) ? module.default : null },
            { id: "Invite", conditions: (module) => (module && module.sendJoinGroupViaInvite) ? module : null },
            { id: "InviteInfo", conditions: (module) => (module && module.sendQueryGroupInvite) ? module : null },
            { id: "Label", conditions: (module) => (module && module.LabelCollection) ? module.LabelCollection : null },
            { id: "MediaPrep", conditions: (module) => (module && module.MediaPrep) ? module : null },
            { id: "MediaObject", conditions: (module) => (module && module.getOrCreateMediaObject) ? module : null },
            { id: "NumberInfo", conditions: (module) => (module && module.formattedPhoneNumber) ? module : null },
            { id: "MediaTypes", conditions: (module) => (module && module.msgToMediaType) ? module : null },
            { id: "MediaUpload", conditions: (module) => (module && module.uploadMedia) ? module : null },
            { id: "MsgKey", conditions: (module) => (module.default && module.default.fromString) ? module.default : null },
            { id: "MessageInfo", conditions: (module) => (module && module.sendQueryMsgInfo) ? module : null },
            { id: "OpaqueData", conditions: (module) => (module.default && module.default.createFromData) ? module.default : null },
            { id: "QueryExist", conditions: (module) => (module && module.queryExists) ? module.queryExists : null },
            { id: "QueryProduct", conditions: (module) => (module && module.queryProduct) ? module : null },
            { id: "QueryOrder", conditions: (module) => (module && module.queryOrder) ? module : null },
            { id: "SendClear", conditions: (module) => (module && module.sendClear) ? module : null },
            { id: "SendDelete", conditions: (module) => (module && module.sendDelete) ? module : null },
            { id: "SendMessage", conditions: (module) => (module && module.addAndSendMsgToChat) ? module : null },
            { id: "SendSeen", conditions: (module) => (module && module.sendSeen) ? module : null },
            { id: "User", conditions: (module) => (module && module.getMaybeMeUser) ? module : null },
            { id: "UploadUtils", conditions: (module) => (module.default && module.default.encryptAndUpload) ? module.default : null },
            { id: "Validators", conditions: (module) => (module && module.findLinks) ? module : null },
            { id: "VCard", conditions: (module) => (module && module.vcardFromContactModel) ? module : null },
            { id: "Wap", conditions: (module) => (module && module.queryLinkPreview) ? module.default : null },
            { id: "WidFactory", conditions: (module) => (module && module.createWid) ? module : null },
            { id: "ProfilePic", conditions: (module) => (module && module.profilePicResync) ? module : null },
            { id: "PresenceUtils", conditions: (module) => (module && module.sendPresenceAvailable) ? module : null },
            { id: "ChatState", conditions: (module) => (module && module.sendChatStateComposing) ? module : null },
            { id: "GroupParticipants", conditions: (module) => (module && module.sendPromoteParticipants) ? module : null },
            { id: "JoinInviteV4", conditions: (module) => (module && module.sendJoinGroupViaInviteV4) ? module : null },
            { id: "findCommonGroups", conditions: (module) => (module && module.findCommonGroups) ? module.findCommonGroups : null },
            { id: "StatusUtils", conditions: (module) => (module && module.setMyStatus) ? module : null },
            { id: "ConversationMsgs", conditions: (module) => (module && module.loadEarlierMsgs) ? module : null },
            { id: "sendReactionToMsg", conditions: (module) => (module && module.sendReactionToMsg) ? module.sendReactionToMsg : null },
            { id: "StickerTools", conditions: (module) => (module && module.toWebpSticker) ? module : null },
            { id: "addWebpMetadata", conditions: (module) => (module && module.addWebpMetadata) ? module : null },
            { id: "GroupUtils", conditions: (module) => (module && module.sendCreateGroup) ? module : null },
            { id: "sendSetGroupSubject", conditions: (module) => (module && module.sendSetGroupSubject) ? module : null },
            { id: "markExited", conditions: (module) => (module && module.markExited) ? module : null },

            { id: "addAndSendMsgToChat", conditions: (e) => (e.addAndSendMsgToChat ? e.addAndSendMsgToChat : null) },
            { id: "MaybeMeUser", conditions: (e) => (e.getMaybeMeUser ? e : null) },
            { id: "Archive", conditions: (module) => (module.setArchive) ? module : null },
            { id: "GroupInvite", conditions: (module) => (module.queryGroupInviteCode) ? module : null },
            { id: "Builders", conditions: (module) => (module.TemplateMessage && module.HydratedFourRowTemplate) ? module : null },
            { id: "createMessageKey", conditions: (module) => (module.createMessageKey && module.createDeviceSentMessage) ? module.createMessageKey : null },

        ];

        window.x = [];
        for (let idx in modules) {
            // const module = modules[idx];
            // if (module && (module.queryExist || (module.default && module.default.queryExist) || (module.instance && module.instance.queryExist))) {
            //   console.log(module);
            //   window.x.push(module);
            // }

            if ((typeof modules[idx] === "object") && (modules[idx] !== null)) {
                neededObjects.forEach((needObj) => {
                    if (!needObj.conditions || needObj.foundedModule)
                        return;
                    let neededModule = needObj.conditions(modules[idx]);
                    if (neededModule !== null) {
                        foundCount++;
                        needObj.foundedModule = neededModule;
                    }
                });
            }
        }

        let neededStore = neededObjects.find((needObj) => needObj.id === "Store");
        window.Store = neededStore.foundedModule ? neededStore.foundedModule : {};
        neededObjects.splice(neededObjects.indexOf(neededStore), 1);
        neededObjects.forEach((needObj) => {
            if (needObj.foundedModule) {
                window.Store[needObj.id] = needObj.foundedModule;
            }
        });

        window.Store.Chat._find = e => {
            const target = window.Store.Chat.get(e)
            return target ? Promise.resolve(target) : Promise.resolve({
                id: e
            })
        }

        window.Store.Chat.modelClass.prototype.sendMessage = function(e) {
            window.Store.SendTextMsgToChat(this, ...arguments);
        }

        return window.Store;
    }

    if (typeof webpackJsonp === 'function') {
        webpackJsonp([], { 'parasite': (x, y, z) => getStore(z) }, ['parasite']);
    } else {
        let tag = new Date().getTime();
        webpackChunkwhatsapp_web_client.push([
            ["parasite" + tag],
            {

            },
            function(o, e, t) {
                let modules = [];
                for (let idx in o.m) {
                    let module = o(idx);
                    modules.push(module);
                }
                getStore(modules);
            }
        ]);
    }

})();


//  *************** whatsapp_web.js **************
function whatsapp_web_js_clint() {
    window.WWebJS = {};
    window.WWebJS.sendSeen = async(chatId) => {
        let chat = window.Store.Chat.get(chatId);
        if (chat !== undefined) {
            await window.Store.SendSeen.sendSeen(chat, false);
            return true;
        }
        return false;

    };
    window.WWebJS.sendMessage = async(chat, content, options = {}) => {
        let attOptions = {};
        if (options.attachment) {
            attOptions = options.sendMediaAsSticker ?
                await window.WWebJS.processStickerData(options.attachment) :
                await window.WWebJS.processMediaData(options.attachment, {
                    forceVoice: options.sendAudioAsVoice,
                    forceDocument: options.sendMediaAsDocument,
                    forceGif: options.sendVideoAsGif
                });

            content = options.sendMediaAsSticker ? undefined : attOptions.preview;

            delete options.attachment;
            delete options.sendMediaAsSticker;
        }
        let quotedMsgOptions = {};
        if (options.quotedMessageId) {
            let quotedMessage = window.Store.Msg.get(options.quotedMessageId);
            if (quotedMessage.canReply()) {
                quotedMsgOptions = quotedMessage.msgContextInfo(chat);
            }
            delete options.quotedMessageId;
        }

        if (options.mentionedJidList) {
            options.mentionedJidList = options.mentionedJidList.map(cId => window.Store.Contact.get(cId).id);
        }

        let locationOptions = {};
        if (options.location) {
            locationOptions = {
                type: 'location',
                loc: options.location.description,
                lat: options.location.latitude,
                lng: options.location.longitude
            };
            delete options.location;
        }

        let vcardOptions = {};
        if (options.contactCard) {
            let contact = window.Store.Contact.get(options.contactCard);
            vcardOptions = {
                body: window.Store.VCard.vcardFromContactModel(contact).vcard,
                type: 'vcard',
                vcardFormattedName: contact.formattedName
            };
            delete options.contactCard;
        } else if (options.contactCardList) {
            let contacts = options.contactCardList.map(c => window.Store.Contact.get(c));
            let vcards = contacts.map(c => window.Store.VCard.vcardFromContactModel(c));
            vcardOptions = {
                type: 'multi_vcard',
                vcardList: vcards,
                body: undefined
            };
            delete options.contactCardList;
        } else if (options.parseVCards && typeof(content) === 'string' && content.startsWith('BEGIN:VCARD')) {
            delete options.parseVCards;
            try {
                const parsed = window.Store.VCard.parseVcard(content);
                if (parsed) {
                    vcardOptions = {
                        type: 'vcard',
                        vcardFormattedName: window.Store.VCard.vcardGetNameFromParsed(parsed)
                    };
                }
            } catch (_) {
                // not a vcard
            }
        }

        if (options.linkPreview) {
            delete options.linkPreview;

            // Not supported yet by WhatsApp Web on MD
            if (!window.Store.MDBackend) {
                const link = window.Store.Validators.findLink(content);
                if (link) {
                    const preview = await window.Store.Wap.queryLinkPreview(link.url);
                    preview.preview = true;
                    preview.subtype = 'url';
                    options = {...options, ...preview };
                }
            }
        }

        let buttonOptions = {};
        if (options.buttons) {
            let caption;
            if (options.buttons.type === 'chat') {
                content = options.buttons.body;
                caption = content;
            } else {
                caption = options.caption ? options.caption : ' '; //Caption can't be empty
            }
            buttonOptions = {
                productHeaderImageRejected: false,
                isFromTemplate: false,
                isDynamicReplyButtonsMsg: true,
                title: options.buttons.title ? options.buttons.title : undefined,
                footer: options.buttons.footer ? options.buttons.footer : undefined,
                dynamicReplyButtons: options.buttons.buttons,
                replyButtons: options.buttons.buttons,
                caption: caption
            };
            delete options.buttons;
        }

        let listOptions = {};
        if (options.list) {
            if (window.Store.Conn.platform === 'smba' || window.Store.Conn.platform === 'smbi') {
                throw '[LT01] Whatsapp business can\'t send this yet';
            }
            listOptions = {
                type: 'list',
                footer: options.list.footer,
                list: {
                    ...options.list,
                    listType: 1
                },
                body: options.list.description
            };
            delete options.list;
            delete listOptions.list.footer;
        }

        const meUser = window.Store.User.getMaybeMeUser();
        const isMD = window.Store.MDBackend;

        const newMsgId = new window.Store.MsgKey({
            from: meUser,
            to: chat.id,
            id: window.Store.MsgKey.newId(),
            participant: isMD && chat.id.isGroup() ? meUser : undefined,
            selfDir: 'out',
        });

        const extraOptions = options.extraOptions || {};
        delete options.extraOptions;

        const ephemeralSettings = {
            ephemeralDuration: chat.isEphemeralSettingOn() ? chat.getEphemeralSetting() : undefined,
            ephemeralSettingTimestamp: chat.getEphemeralSettingTimestamp() || undefined,
            disappearingModeInitiator: chat.getDisappearingModeInitiator() || undefined,
        };

        const message = {
            ...options,
            id: newMsgId,
            ack: 0,
            body: content,
            from: meUser,
            to: chat.id,
            local: true,
            self: 'out',
            t: parseInt(new Date().getTime() / 1000),
            isNewMsg: true,
            type: 'chat',
            ...ephemeralSettings,
            ...locationOptions,
            ...attOptions,
            ...quotedMsgOptions,
            ...vcardOptions,
            ...buttonOptions,
            ...listOptions,
            ...extraOptions
        };

        await window.Store.SendMessage.addAndSendMsgToChat(chat, message);
        return window.Store.Msg.get(newMsgId._serialized);
    };
    window.WWebJS.toStickerData = async(mediaInfo) => {
        if (mediaInfo.mimetype == 'image/webp') return mediaInfo;

        const file = window.WWebJS.mediaInfoToFile(mediaInfo);
        const webpSticker = await window.Store.StickerTools.toWebpSticker(file);
        const webpBuffer = await webpSticker.arrayBuffer();
        const data = window.WWebJS.arrayBufferToBase64(webpBuffer);

        return {
            mimetype: 'image/webp',
            data
        };
    };
    window.WWebJS.processStickerData = async(mediaInfo) => {
        if (mediaInfo.mimetype !== 'image/webp') throw new Error('Invalid media type');

        const file = window.WWebJS.mediaInfoToFile(mediaInfo);
        let filehash = await window.WWebJS.getFileHash(file);
        let mediaKey = await window.WWebJS.generateHash(32);

        const controller = new AbortController();
        const uploadedInfo = await window.Store.UploadUtils.encryptAndUpload({
            blob: file,
            type: 'sticker',
            signal: controller.signal,
            mediaKey
        });

        const stickerInfo = {
            ...uploadedInfo,
            clientUrl: uploadedInfo.url,
            deprecatedMms3Url: uploadedInfo.url,
            uploadhash: uploadedInfo.encFilehash,
            size: file.size,
            type: 'sticker',
            filehash
        };

        return stickerInfo;
    };
    window.WWebJS.processMediaData = async(mediaInfo, { forceVoice, forceDocument, forceGif }) => {
        const file = window.WWebJS.mediaInfoToFile(mediaInfo);
        const mData = await window.Store.OpaqueData.createFromData(file, file.type);
        const mediaPrep = window.Store.MediaPrep.prepRawMedia(mData, { asDocument: forceDocument });
        const mediaData = await mediaPrep.waitForPrep();
        const mediaObject = window.Store.MediaObject.getOrCreateMediaObject(mediaData.filehash);

        const mediaType = window.Store.MediaTypes.msgToMediaType({
            type: mediaData.type,
            isGif: mediaData.isGif
        });

        if (forceVoice && mediaData.type === 'audio') {
            mediaData.type = 'ptt';
        }

        if (forceGif && mediaData.type === 'video') {
            mediaData.isGif = true;
        }

        if (forceDocument) {
            mediaData.type = 'document';
        }

        if (!(mediaData.mediaBlob instanceof window.Store.OpaqueData)) {
            mediaData.mediaBlob = await window.Store.OpaqueData.createFromData(mediaData.mediaBlob, mediaData.mediaBlob.type);
        }

        mediaData.renderableUrl = mediaData.mediaBlob.url();
        mediaObject.consolidate(mediaData.toJSON());
        mediaData.mediaBlob.autorelease();

        const uploadedMedia = await window.Store.MediaUpload.uploadMedia({
            mimetype: mediaData.mimetype,
            mediaObject,
            mediaType
        });

        const mediaEntry = uploadedMedia.mediaEntry;
        if (!mediaEntry) {
            throw new Error('upload failed: media entry was not created');
        }

        mediaData.set({
            clientUrl: mediaEntry.mmsUrl,
            deprecatedMms3Url: mediaEntry.deprecatedMms3Url,
            directPath: mediaEntry.directPath,
            mediaKey: mediaEntry.mediaKey,
            mediaKeyTimestamp: mediaEntry.mediaKeyTimestamp,
            filehash: mediaObject.filehash,
            encFilehash: mediaEntry.encFilehash,
            uploadhash: mediaEntry.uploadHash,
            size: mediaObject.size,
            streamingSidecar: mediaEntry.sidecar,
            firstFrameSidecar: mediaEntry.firstFrameSidecar
        });

        return mediaData;
    };
    window.WWebJS.getMessageModel = message => {
        const msg = message.serialize();

        msg.isEphemeral = message.isEphemeral;
        msg.isStatusV3 = message.isStatusV3;
        msg.links = (message.getLinks()).map(link => ({
            link: link.href,
            isSuspicious: Boolean(link.suspiciousCharacters && link.suspiciousCharacters.size)
        }));

        if (msg.buttons) {
            msg.buttons = msg.buttons.serialize();
        }
        if (msg.dynamicReplyButtons) {
            msg.dynamicReplyButtons = JSON.parse(JSON.stringify(msg.dynamicReplyButtons));
        }
        if (msg.replyButtons) {
            msg.replyButtons = JSON.parse(JSON.stringify(msg.replyButtons));
        }

        if (typeof msg.id.remote === 'object') {
            msg.id = Object.assign({}, msg.id, { remote: msg.id.remote._serialized });
        }

        delete msg.pendingAckUpdate;

        return msg;
    };
    window.WWebJS.getChatModel = async chat => {

        let res = chat.serialize();
        res.isGroup = chat.isGroup;
        res.formattedTitle = chat.formattedTitle;
        res.isMuted = chat.mute && chat.mute.isMuted;

        if (chat.groupMetadata) {
            const chatWid = window.Store.WidFactory.createWid((chat.id._serialized));
            await window.Store.GroupMetadata.update(chatWid);
            res.groupMetadata = chat.groupMetadata.serialize();
        }

        delete res.msgs;
        delete res.msgUnsyncedButtonReplyMsgs;
        delete res.unsyncedButtonReplies;

        return res;
    };
    window.WWebJS.getChat = async chatId => {
        const chatWid = window.Store.WidFactory.createWid(chatId);
        const chat = await window.Store.Chat.find(chatWid);
        return await window.WWebJS.getChatModel(chat);
    };
    window.WWebJS.getChats = async() => {
        const chats = window.Store.Chat.getModelsArray();

        const chatPromises = chats.map(chat => window.WWebJS.getChatModel(chat));
        return await Promise.all(chatPromises);
    };
    window.WWebJS.getContactModel = contact => {
        let res = contact.serialize();
        res.isBusiness = contact.isBusiness;

        if (contact.businessProfile) {
            res.businessProfile = contact.businessProfile.serialize();
        }

        res.isMe = contact.isMe;
        res.isUser = contact.isUser;
        res.isGroup = contact.isGroup;
        res.isWAContact = contact.isWAContact;
        res.isMyContact = contact.isMyContact;
        res.isBlocked = contact.isContactBlocked;
        res.userid = contact.userid;

        return res;
    };
    window.WWebJS.getContact = async contactId => {
        const wid = window.Store.WidFactory.createWid(contactId);
        const contact = await window.Store.Contact.find(wid);
        return window.WWebJS.getContactModel(contact);
    };
    window.WWebJS.getContacts = () => {
        const contacts = window.Store.Contact.getModelsArray();
        return contacts.map(contact => window.WWebJS.getContactModel(contact));
    };
    window.WWebJS.mediaInfoToFile = ({ data, mimetype, filename }) => {
        const binaryData = window.atob(data);

        const buffer = new ArrayBuffer(binaryData.length);
        const view = new Uint8Array(buffer);
        for (let i = 0; i < binaryData.length; i++) {
            view[i] = binaryData.charCodeAt(i);
        }

        const blob = new Blob([buffer], { type: mimetype });
        return new File([blob], filename, {
            type: mimetype,
            lastModified: Date.now()
        });
    };
    window.WWebJS.arrayBufferToBase64 = (arrayBuffer) => {
        let binary = '';
        const bytes = new Uint8Array(arrayBuffer);
        const len = bytes.byteLength;
        for (let i = 0; i < len; i++) {
            binary += String.fromCharCode(bytes[i]);
        }
        return window.btoa(binary);
    };
    window.WWebJS.getFileHash = async(data) => {
        let buffer = await data.arrayBuffer();
        const hashBuffer = await crypto.subtle.digest('SHA-256', buffer);
        return btoa(String.fromCharCode(...new Uint8Array(hashBuffer)));
    };
    window.WWebJS.generateHash = async(length) => {
        let result = '';
        let characters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
        let charactersLength = characters.length;
        for (let i = 0; i < length; i++) {
            result += characters.charAt(Math.floor(Math.random() * charactersLength));
        }
        return result;
    };
    window.WWebJS.sendClearChat = async(chatId) => {
        let chat = window.Store.Chat.get(chatId);
        if (chat !== undefined) {
            await window.Store.SendClear.sendClear(chat, false);
            return true;
        }
        return false;
    };
    window.WWebJS.sendDeleteChat = async(chatId) => {
        let chat = window.Store.Chat.get(chatId);
        if (chat !== undefined) {
            await window.Store.SendDelete.sendDelete(chat);
            return true;
        }
        return false;
    };
    window.WWebJS.sendChatstate = async(state, chatId) => {
        if (window.Store.MDBackend) {
            chatId = window.Store.WidFactory.createWid(chatId);
        }
        switch (state) {
            case 'typing':
                await window.Store.ChatState.sendChatStateComposing(chatId);
                break;
            case 'recording':
                await window.Store.ChatState.sendChatStateRecording(chatId);
                break;
            case 'stop':
                await window.Store.ChatState.sendChatStatePaused(chatId);
                break;
            default:
                throw 'Invalid chatstate';
        }

        return true;
    };
    window.WWebJS.getLabelModel = label => {
        let res = label.serialize();
        res.hexColor = label.hexColor;

        return res;
    };
    window.WWebJS.getLabels = () => {
        const labels = window.Store.Label.getModelsArray();
        return labels.map(label => window.WWebJS.getLabelModel(label));
    };
    window.WWebJS.getLabel = (labelId) => {
        const label = window.Store.Label.get(labelId);
        return window.WWebJS.getLabelModel(label);
    };
    window.WWebJS.getChatLabels = async(chatId) => {
        const chat = await window.WWebJS.getChat(chatId);
        return (chat.labels || []).map(id => window.WWebJS.getLabel(id));
    };
    window.WWebJS.getOrderDetail = async(orderId, token, chatId) => {
        const chatWid = window.Store.WidFactory.createWid(chatId);
        return window.Store.QueryOrder.queryOrder(chatWid, orderId, 80, 80, token);
    };
    window.WWebJS.getProductMetadata = async(productId) => {
        let sellerId = window.Store.Conn.wid;
        let product = await window.Store.QueryProduct.queryProduct(sellerId, productId);
        if (product && product.data) {
            return product.data;
        }

        return undefined;
    };
}

//  *************** wapi.js **************

function wapi_js_client() {
    window.WAPI = {
        lastRead: {}
    };
    window.WAPI._serializeRawObj = (obj) => {
        if (obj) {
            return obj.toJSON();
        }
        return {}
    };
    window.WAPI._serializeChatObj = (obj) => {
        if (obj === undefined) {
            return null;
        }

        return Object.assign(window.WAPI._serializeRawObj(obj), {
            kind: obj.kind,
            isGroup: obj.isGroup,
            contact: obj['contact'] ? window.WAPI._serializeContactObj(obj['contact']) : null,
            groupMetadata: obj["groupMetadata"] ? window.WAPI._serializeRawObj(obj["groupMetadata"]) : null,
            presence: obj["presence"] ? window.WAPI._serializeRawObj(obj["presence"]) : null,
            msgs: null
        });
    };
    window.WAPI._serializeContactObj = (obj) => {
        if (obj === undefined) {
            return null;
        }

        return Object.assign(window.WAPI._serializeRawObj(obj), {
            formattedName: obj.formattedName,
            isHighLevelVerified: obj.isHighLevelVerified,
            isMe: obj.isMe,
            isMyContact: obj.isMyContact,
            isPSA: obj.isPSA,
            isUser: obj.isUser,
            isVerified: obj.isVerified,
            isWAContact: obj.isWAContact,
            profilePicThumbObj: obj.profilePicThumb ? WAPI._serializeProfilePicThumb(obj.profilePicThumb) : {},
            statusMute: obj.statusMute,
            msgs: null
        });
    };
    window.WAPI._serializeMessageObj = obj => {
        if (obj == undefined) {
            return null;
        }
        const _chat = obj["chat"] ? WAPI._serializeChatObj(obj["chat"]) : {};
        if (obj.quotedMsg) obj.quotedMsgObj();
        return Object.assign(window.WAPI._serializeRawObj(obj), {
            id: obj.id._serialized,
            //add 02/06/2020 mike -->
            quotedParticipant: obj.quotedParticipant ?
                obj.quotedParticipant._serialized ?
                obj.quotedParticipant._serialized :
                undefined : undefined,
            author: obj.author ?
                obj.author._serialized ?
                obj.author._serialized :
                undefined : undefined,
            chatId: obj.chatId ?
                obj.chatId._serialized ?
                obj.chatId._serialized :
                undefined : undefined,
            to: obj.to ?
                obj.to._serialized ?
                obj.to._serialized :
                undefined : undefined,
            fromMe: obj.id.fromMe,
            //add 02/06/2020 mike <--

            sender: obj["senderObj"] ?
                WAPI._serializeContactObj(obj["senderObj"]) : null,
            timestamp: obj["t"],
            content: obj["body"],
            isGroupMsg: obj.isGroupMsg,
            isLink: obj.isLink,
            isMMS: obj.isMMS,
            isMedia: obj.isMedia,
            isNotification: obj.isNotification,
            isPSA: obj.isPSA,
            type: obj.type,
            chat: _chat,
            isOnline: _chat.isOnline,
            lastSeen: _chat.lastSeen,
            chatId: obj.id.remote,
            quotedMsgObj: WAPI._serializeMessageObj(obj["_quotedMsgObj"]),
            mediaData: window.WAPI._serializeRawObj(obj["mediaData"]),
            reply: body => window.WAPI.reply(_chat.id._serialized, body, obj)
        });
    };
    window.WAPI._serializeNumberStatusObj = (obj) => {
        if (obj === undefined) {
            return null;
        }

        return Object.assign({}, {
            id: obj.jid,
            status: obj.status,
            isBusiness: (obj.biz === true),
            canReceiveMessage: (obj.status === 200)
        });
    };
    window.WAPI._serializeProfilePicThumb = (obj) => {
        if (obj === undefined) {
            return null;
        }

        return Object.assign({}, {
            eurl: obj.eurl,
            id: obj.id,
            img: obj.img,
            imgFull: obj.imgFull,
            raw: obj.raw,
            tag: obj.tag
        });
    }
    window.WAPI.isMultiDeviceVersion = function() {
        try {
            var resp = !!Store.GetMaybeMeUser.getMe().device;
            return resp;
        } catch (_) {
            return false;
        }
    }
    window.WAPI.getChat = function(id, done) {
        // New version WhatsApp Beta Multi Device
        if (WAPI.isMultiDeviceVersion()) {
            let chat = window.Store.Chat.get(id);
            if (chat) {
                if (chat.sendMessage) {
                    if (done) done(chat);
                    return chat;
                } else {
                    if (done) done(chat._value);
                    return chat._value;
                }
            } else {
                // Create user
                var idx = new window.Store.UserConstructor(id, { intentionallyUsePrivateConstructor: true });

                // Get chat
                // window.Store.Chat.find(idx, chat => {

                //   if (chat._value) {
                //     if (done) done(chat._value);
                //   } else {
                //     if (done) done(chat);
                //   }
                // });

                window.Store.FindChat.findChat(idx).then(chat => {
                    if (done) done(chat);
                }).catch(e => {
                    if (done) done(null);
                })

                return undefined;
            }
        } else
        // Old version
        {
            id = typeof id == "string" ? id : id._serialized;
            const found = window.Store.Chat.get(id);
            found.sendMessage = (found.sendMessage) ? found.sendMessage : function() { return window.Store.sendMessage.apply(this, arguments); };
            if (done !== undefined) done(found);
            return found;
        }
    }
    window.WAPI.base64ImageToFile = function(b64Data, filename) {
        var arr = b64Data.split(',');
        var mime = arr[0].match(/:(.*?);/)[1];
        var bstr = atob(arr[1]);
        var n = bstr.length;
        var u8arr = new Uint8Array(n);

        while (n--) {
            u8arr[n] = bstr.charCodeAt(n);
        }

        return new File([u8arr], filename, { type: mime });
    };
    window.WAPI.sendSeen = async(chatId) => {
        let chat = window.Store.Chat.get(chatId);
        if (chat !== undefined) {
            await window.Store.SendSeen.sendSeen(chat, false);
            return true;
        }
        return false;

    };
    window.WAPI.getFileHash = async(data) => {
        let buffer = await data.arrayBuffer();
        var sha = new jsSHA("SHA-256", "ARRAYBUFFER");
        sha.update(buffer);
        return sha.getHash("B64");
    };
    window.WAPI.generateMediaKey = async(length) => {
        var result = '';
        var characters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
        var charactersLength = characters.length;
        for (var i = 0; i < length; i++) {
            result += characters.charAt(Math.floor(Math.random() * charactersLength));
        }
        return result;
    };

    /** Joins a group via the invite link, code, or message
     * @param link This param is the string which includes the invite link or code. The following work:
     * - Follow this link to join my WA group: https://chat.whatsapp.com/DHTGJUfFJAV9MxOpZO1fBZ
     * - https://chat.whatsapp.com/DHTGJUfFJAV9MxOpZO1fBZ
     * - DHTGJUfFJAV9MxOpZO1fBZ
     * @returns Promise<string | boolean> Either false if it didn't work, or the group id.
     */
    window.WAPI.joinGroupViaLink = async function(link) {
            return await Store.WapQuery.acceptGroupInvite(link.split('\/').pop()).then(res => res.status === 200 ? res.gid._serialized : res.status);
            let code = link;
            //is it a link? if not, assume it's a code, otherwise, process the link to get the code.
            if (link.includes('chat.whatsapp.com')) {
                if (!link.match(/chat.whatsapp.com\/([\w\d]*)/g).length) return false;
                code = link.match(/chat.whatsapp.com\/([\w\d]*)/g)[0].replace('chat.whatsapp.com\/', '');
            }
            const group = await Store.GroupInvite.joinGroupViaInvite(code);
            if (!group.id) return false;
            return group.id._serialized
        }
        /**
         * @param id The id of the conversation
         * @param archive boolean true => archive, false => unarchive
         * @return boolean true: worked, false: didnt work (probably already in desired state)
         */
    window.WAPI.archiveChat = async function(id, archive) {
        return await Store.Archive.setArchive(Store.Chat.get(id), archive).then(_ => true).catch(_ => false)
    }

    /**
     * Create an chat ID based in a cloned one
     *
     * @param {string} chatId '000000000000@c.us'
     */
    window.WAPI.getNewMessageId = function(chatId) {
        var newMsgId = Store.Msg.models[0].__x_id.clone();

        newMsgId.fromMe = true;
        newMsgId.id = WAPI.getNewId().toUpperCase();
        newMsgId.remote = chatId;
        newMsgId._serialized = `${newMsgId.fromMe}_${newMsgId.remote}_${newMsgId.id}`

        return newMsgId;
    };

}



function custom_clint() {
    window.WAPI.checkNumberStatus_V2 = async function(chatId, done) {
        let data
        try {
            if (chatId && (!chatId.endsWith('@c.us') && !chatId.endsWith('@g.us'))) {
                chatId += chatId.length > 15 ? '@g.us' : '@c.us'
            }
            const wid = window.Store.WidFactory.createWid(chatId);
            const result = await window.Store.QueryExist(wid);
            // console.log(result);
            if (!result || result.wid === undefined) data = { result: null, error: 'not found' };
            data = { result: result.wid, error: null };
        } catch (e) {
            // console.log(e.message)
            data = { result: null, error: e.message }
        }
        if (done) done(data);
        return data
    };

    window.WAPI.checkNumberStatus_V3 = async function(chatId, done) {
        let data
        try {
            if (chatId && (!chatId.endsWith('@c.us') && !chatId.endsWith('@g.us'))) {
                chatId += '@c.us'
            }

            const result = await WPP.contact.queryExists(chatId)

            if (!result || result.wid === undefined) data = { result: null, error: 'not found' };
            data = { result: result.wid, error: null };
        } catch (e) {
            // console.log(e.message)
            data = { result: null, error: e.message }
        }
        if (done) done(data);
        return data
    };

    window.WAPI.getLoadMessagesChat_V2 = async function(id, more = false, includeMe = true, done) {
        let data
        let msgs;
        let output = [];
        let isNext = false;
        try {
            if (id && (!id.endsWith('@c.us') || !id.endsWith('@g.us'))) {
                id += id.length > 15 ? '@g.us' : '@c.us'
            }
            const chat = window.WAPI.getChat(id);
            isNext = !chat.msgs.msgLoadState.noEarlierMsgs
            if (more) {
                msgs = await window.Store.ConversationMsgs.loadEarlierMsgs(chat);
            } else {
                msgs = chat.msgs.getModelsArray()
            }
            if (msgs) {
                for (const m of msgs) {
                    output.push(window.WAPI._serializeMessageObj(m))
                }
            }

            data = { result: output, isNext: isNext, error: null };
        } catch (e) {
            data = { result: output, error: e.message, isNext: isNext }
        }
        if (done) done(data);
        return data
    };
    window.WAPI.stopAutoReplay_V2 = function(done) {
        window.Store.Msg._events.add = []
        if (done) done();
    }
    window.WAPI.startAutoReplay_V2 = function(done) {
        window.Store.Msg.on('add', async(msg) => {
            if (msg && msg.isNewMsg && !msg.isSentByMe) {
                //for read state
                if (msg.ack && msg.ack > 2) {} else if (msg.isGroupMsg) {}
                // else if (msg.isMedia) {}
                // else if (msg.type && msg.type !== "chat") {} else if (!msg.body) {}
                else {
                    let messages = []
                    let replays = JSON.parse(localStorage.getItem("replays"));
                    Object.keys(replays).map(function(key, index) {
                        key.split(',').map((k) => {
                            if (msg.body.includes(k.replace(/\s/g, ''))) {
                                messages.push(replays[key])
                            }
                        })
                    });
                    try {
                        await window.WAPI.sendSeen(msg.sender._serialized);
                    } catch (e) {
                        console.log(e.message)
                    }
                    messages = [...new Set(messages)];
                    for (const message of messages) {
                        if ("text" === message.message_type || ("button" === message.message_type && !message.media)) {
                            console.log(await window.WAPI.sendButtonsWithText_V2(msg.sender._serialized, message))
                        } else if (("button" === message.message_type && message.media) || "file" === message.message_type) {
                            console.log(await window.WAPI.sendButtonsWithFile_V2(msg.sender._serialized, message))
                        } else if ("list" === message.message_type) {
                            console.log(await window.WAPI.sendList_V2(msg.sender._serialized, message))
                        }
                    }
                }
            }
        })
        if (done) done();
    }
    window.WAPI.updateReplay_V2 = function(replays = {}, done) {
        localStorage.setItem("replays", JSON.stringify(replays));
        if (done) done();
    }
    window.WAPI.sendMessage_V4 = async function sendFileInput(chatId, caption, options = {}, done) {
        let data;
        let media;
        if (chatId && (!chatId.endsWith('@c.us') && !chatId.endsWith('@g.us'))) {
            chatId += chatId.length > 15 ? '@g.us' : '@c.us'
        }
        try {
            try{
                await WPP.chat.openChatBottom(chatId);
            }catch(e){
            }

            const chat = window.WAPI.getChat(chatId);
            if (chat) {
                if (options.media && options.filename) {
                    const forceDocument = options.sendMediaAsDocument || false
                    const mediaBlob = window.WAPI.base64ImageToFile(options.media, options.filename);
                    const mData = await window.Store.OpaqueData.createFromData(mediaBlob, mediaBlob.type);
                    const media = window.Store.MediaPrep.prepRawMedia(mData, { asDocument: forceDocument });
                    const result = await media.sendToChat(chat, { caption: caption })

                    data = { 'result': result !== 'ERROR_UNKNOWN' ? result : null, error: result === 'ERROR_UNKNOWN' ? result : null };
                } else {
                    const result = await window.Store.SendTextMsgToChat(chat, caption)
                    data = { 'result': result };
                }
            } else {
                data = { 'error': "Chat NOT FOUND" };
            }

        } catch (e) {
            data = { 'error': e.message };
        }

        if (done) done(data);
        return data

    }
    window.WAPI.openChat_V2 = async function(chatId, done) {
        let data;
        if (chatId && (!chatId.endsWith('@c.us') && !chatId.endsWith('@g.us'))) {
            chatId += chatId.length > 15 ? '@g.us' : '@c.us'
        }

        const chat = window.WAPI.getChat(chatId)
        if (chat) {
            try {
                const res = await window.Store.Cmd.openChatAt(chat)
                data = { result: res }
            } catch (e) {
                data = { error: e.message }
            }
        } else {
            data = { error: "Chat NOT FOUND" }
        }

        if (done) done(data);
        return data

    }
    window.WAPI.closeChat_v2 = function(done) {
        window.Store.Cmd.closeChat(window.Store.Chat.getActive())
        if (done) done();
    }
    window.WAPI.chatInfoDrawer_v2 = function(done) {
            window.Store.Cmd.chatInfoDrawer(window.Store.Chat.getActive())
            if (done) done();
        }
        /**
         * buttons max 3 text and 2 link or phoneNumber
         * @param chatId
         * @param option
         * @param done
         * @returns {Promise<{error: string}|{result: boolean}>}
         */
    window.WAPI.sendTest_V2 = async function(chatId, option, done) {
        let data;
        try {
            if (chatId && (!chatId.endsWith('@c.us') && !chatId.endsWith('@g.us'))) {
                chatId += chatId.length > 15 ? '@g.us' : '@c.us'
            }

            let text = "text?text:''"
            const chat = window.WAPI.getChat(chatId);
            if (chat && 404 != chat.status && chat.id) {
                const meUser = window.Store.User.getMaybeMeUser();
                const isMD = window.Store.MDBackend;

                const newMsgId = new window.Store.MsgKey({
                    from: meUser,
                    to: chat.id,
                    id: window.Store.MsgKey.newId(),
                    participant: isMD && chat.id.isGroup() ? meUser : undefined,
                    selfDir: 'out',
                });

                let s = {
                    id: newMsgId,
                    ack: 1,
                    from: meUser,
                    to: chat.id,
                    local: true,
                    self: "out",
                    t: parseInt((new Date).getTime() / 1e3),
                    isNewMsg: true,
                    type: "chat",
                    body: text,
                    caption: text,
                    content: text,
                    isForwarded: false,
                    broadcast: false,
                };
                let r = (await Promise.all(window.Store.addAndSendMsgToChat(chat, s)));
                data = { result: "success" === r[1] || "OK" === r[1] }

            } else {
                data = { error: "Chat NOT FOUND" }
            }
        } catch (e) {
            data = { error: e.message }
        }

        if (done) done(data);
        return data
    }

    window.WAPI.sendButtons_V2 = async function(chatId, option, done) {
        let data;
        try {
            if (chatId && (!chatId.endsWith('@c.us') && !chatId.endsWith('@g.us'))) {
                chatId += chatId.length > 15 ? '@g.us' : '@c.us'
            }

            const buttons = option.buttons
            const title = option.title
            const footer = option.footer
            let text = option.message
            text = text ? text : ''
            const chat = window.WAPI.getChat(chatId);
            if (chat && 404 != chat.status && chat.id) {
                const meUser = window.Store.User.getMaybeMeUser();
                const isMD = window.Store.MDBackend;

                const newMsgId = new window.Store.MsgKey({
                    from: meUser,
                    to: chat.id,
                    id: window.Store.MsgKey.newId(),
                    participant: isMD && chat.id.isGroup() ? meUser : undefined,
                    selfDir: 'out',
                });

                // const e = await window.WAPI.getNewMessageId(chat.id._serialized),
                let s = {
                    id: newMsgId,
                    ack: 1,
                    from: meUser,
                    to: chat.id,
                    local: true,
                    self: "out",
                    t: parseInt((new Date).getTime() / 1e3),
                    isNewMsg: true,
                    type: "chat",
                    body: text,
                    caption: text,
                    content: text,
                    isForwarded: false,
                    broadcast: false,
                    isQuotedMsgAvailable: false,
                    shouldEnableHsm: true,
                    __x_hasTemplateButtons: true,
                    invis: true,
                };
                let a = await WPP.chat.prepareMessageButtons({
                    "phone": new Store.WidFactory.createWid(chat.id),
                    "message": text,
                    "options": {
                        "useTemplateButtons": true,
                        "buttons": buttons,
                    }
                }, {
                    "useTemplateButtons": true,
                    "buttons": buttons,
                    "title": title,
                    "footer": footer,
                });
                Object.assign(s, a);
                let r = (await Promise.all(window.Store.addAndSendMsgToChat(chat, s)));
                data = { result: "success" === r[1] || "OK" === r[1] }

            } else {
                data = { error: "Chat NOT FOUND" }
            }
        } catch (e) {
            data = { error: e.message }
        }

        if (done) done(data);
        return data
    }
    window.WAPI.sendButtonsWithFile_V2 = async function(chatId, options, done) {
        let data;
        try {
            if (chatId && (!chatId.endsWith('@c.us') && !chatId.endsWith('@g.us'))) {
                chatId += chatId.length > 15 ? '@g.us' : '@c.us'
            }
            let isButton = Array.isArray(options.buttons) && 5 >= options.buttons.length >= 1
            let useTemplateButton = Array.isArray(options.buttons) && 5 >= options.buttons.length >= 1
            if (options.useTemplateButton == "false") {
                useTemplateButton = false
            }
            console.log(useTemplateButton)
            let s = {
                createChat: true,
                useTemplateButtons: useTemplateButton,
                type: options.type,
                footer: options.footer,
                caption: options.message || '',
            }
            if (isButton) {
                s['buttons'] = options.buttons
            }
            try{
                await WPP.chat.openChatBottom(chatId);
            }catch(e){
            }
            const a = await WPP.chat.sendFileMessage(
                chatId,
                options.media, s
            );
            data = { result: "success" === a.sendMsgResult._value || "OK" === a.sendMsgResult._value }

        } catch (e) {
            data = { error: e.message }
        }

        if (done) done(data);
        return data
    }
    window.WAPI.sendButtonsWithText_V2 = async function(chatId, options, done) {
        let data = {};
        try {
            if (chatId && (!chatId.endsWith('@c.us') && !chatId.endsWith('@g.us'))) {
                chatId += chatId.length > 15 ? '@g.us' : '@c.us'
            }
            let isButton = Array.isArray(options.buttons) && 5 >= options.buttons.length >= 1
            let useTemplateButton = Array.isArray(options.buttons) && 5 >= options.buttons.length >= 1
            if (options.useTemplateButton == "false") {
                useTemplateButton = false
            }
            console.log(useTemplateButton)
            let s = {
                createChat: true,
                useTemplateButtons: useTemplateButton,
                footer: options.footer,
                title: options.title,
            }

            if (isButton) {
                s['buttons'] = options.buttons
            }
            try{
                await WPP.chat.openChatBottom(chatId);
            }catch(e){
            }
            const a = await WPP.chat.sendTextMessage(
                chatId,
                options.message, s
            );
            data = { result: "success" === a.sendMsgResult._value || "OK" === a.sendMsgResult._value }
        } catch (e) {
            console.log(e)
            data = { error: e.message }
        }

        if (done) done(data);
        return data
    }

    /**
     * @param chatId
     * @param option
     * Sections options must have between 1 and 10 options
     * @param done
     * @returns {Promise<{error: string}|{result: boolean}>}
     */
    window.WAPI.sendList_V2 = async function(chatId, option, done) {
        let data
        try {
            if (chatId && (!chatId.endsWith('@c.us') && !chatId.endsWith('@g.us'))) {
                chatId += chatId.length > 15 ? '@g.us' : '@c.us'
            }
            const buttonText = option.buttonText || "ارسل"
            const description = option.description || option.message
            const section = option.sections
            const title = option.title
            const footer = option.footer
            try{
                await WPP.chat.openChatBottom(chatId);
            }catch(e){
            }
            const chat = window.WAPI.getChat(chatId);
            if (chat && 404 != chat.status && chat.id) {
                let n = {
                    "buttonText": buttonText,
                    "description": description,
                    "sections": section,
                    "title": title,
                    "footer": footer,
                }
                const a = await WPP.chat.sendListMessage(chat.id, n);

                data = { result: "success" === a.sendMsgResult._value || "OK" === a.sendMsgResult._value }
            } else {
                data = { error: "Chat NOT FOUND" }
            }
        } catch (e) {
            console.log(e)
            data = { error: e.message }
        }

        if (done) done(data);
        return data
    }

    window.WAPI.getChats_V2 = async function(options = {}, done) {
        let data;
        let option = {};
        if (options instanceof Object) {
            option.onlyUsers = options.onlyUsers
            option.onlyGroups = options.onlyGroups
            option.withLabels = options.withLabels
        }
        data = await WPP.chat.list(option)
        data = data.map((e) => {
            return {
                id: e.id.user,
                // name:e.__x_formattedTitle,
                isGroup: e.isGroup,
                isMyContact: e.__x_contact.isMyContact,
                __x_displayName: e.__x_contact.__x_displayName
            }
        });
        if (done) done(data);
        return data
    }

    window.WAPI.getGroupParticipants_V2 = function(id, done) {
        let data;
        if (id && (!id.endsWith('@g.us'))) {
            id += '@g.us'
        }
        let metadata = window.Store.GroupMetadata.get(id);
        if (metadata) {
            data = metadata.participants.map((e) => {
                return {
                    id: e.id.user,
                    // name:e.__x_formattedTitle,
                    isGroup: e.isGroup,
                    isMyContact: e.__x_contact.isMyContact,
                    __x_displayName: e.__x_contact.__x_displayName
                }
            });
        }
        if (done) done(data);
        return data
    };

    window.WAPI.getGroupInfoFromInviteCode_V2 = async function(inviteCode, done) {
        let data = {}
        if (inviteCode && inviteCode !== "") {
            try {
                data = await WPP.group.getGroupInfoFromInviteCode(inviteCode);
            } catch (e) {
                data = { "error": e.message }
            }
        } else {
            data = { "error": "Invalid Invite Code" }
        }
        if (done) done(data);
        return data
    }

    window.WAPI.joinGroupFromInviteCode_V2 = async function(inviteCode, done) {
        let data = {}
        if (inviteCode && inviteCode !== "") {
            try {
                data = await WPP.group.join(inviteCode);
            } catch (e) {
                data = { "error": e.message }
            }
        } else {
            data = { "error": "Invalid Invite Code" }
        }
        if (done) done(data);
        return data
    }

    window.WAPI.canAddToGroup_V2 = async function(id, done) {
        let data = {}
        if (id && (!id.endsWith('@g.us'))) {
            id += '@g.us'
        }

        try {
            let r = await WPP.group.canAdd(id);
            data = { "result": r }
        } catch (e) {
            data = { "error": e.message }
        }

        if (done) done(data);
        return data
    }
    window.WAPI.addToGroup_V2 = async function(idGroup, ids, done) {
        let data = {}
        if (idGroup && (!idGroup.endsWith('@g.us'))) {
            idGroup += '@g.us'
        }

        try {
            let r = await WPP.group.addParticipants(idGroup, ids);
            data = { "result": r }
        } catch (e) {
            data = { "error": e.message }
        }

        if (done) done(data);
        return data
    }
    window.WAPI.createGroup_V2 = async function(name, done) {
        let data = {}
        try {
            let r = await WPP.group.create(name, []);
            data = { "result": r }
        } catch (e) {
            data = { "error": e.message }
        }

        if (done) done(data);
        return data
    }

    window.WAPI.getAllContacts_V2 = async function(option, done) {
        let data;
        option = option instanceof Object ? option : {}
        data = await WPP.contact.list(option)
        data = data.map((e) => {

            return {
                id: e.id.user,
                name: e.__x_formattedTitle,
                isGroup: e.isGroup,
                isMyContact: e.isMyContact,
                __x_displayName: e.__x_displayName,
                __x_contact: e.__x_contact.__x_displayName,
                __x_notifyName: e.__x_contact.__x_notifyName,
            }
        });
        if (done) done(data);
        return data
    }
    window.WAPI.getLabels_V2 = (done) => {
        const labels = window.Store.Label.getModelsArray();
        let data = labels.map(label => label.serialize());
        if (done) done(data);
        return data
    };


}

wapi_js_client()
custom_clint()