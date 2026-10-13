"""Central JavaScript commands executed by the session bridge."""

from __future__ import annotations

COMMANDS: dict[str, str] = {
    "BusinessLayer.getBusinessProfile_.0": "({id}) => WPP.contact.getBusinessProfile(id)",
    "BusinessLayer.sendImageWithProduct_.0": "({to, base64, caption, businessId, productId}) => WAPI.sendImageWithProduct(base64, to, caption, businessId, productId)",
    "CatalogLayer.createProduct_.0": """({ name, image, description, price, isHidden, url, retailerId, currency }) => {
                return WPP.catalog.createProduct({
                    name, image, description, price, isHidden, url, retailerId, currency
                });
            }""",
    "CatalogLayer.delProducts_.0": """({ productsId }) => {
                return WPP.catalog.delProducts(productsId);
            }""",
    "CatalogLayer.getProducts_.0": """({ id, qnt }) => {
                return WPP.catalog.getProducts(id, qnt);
            }""",
    "CatalogLayer.getProductById_.0": """({ id, productId }) => {
                return WPP.catalog.getProductById(id, productId);
            }""",
    "CatalogLayer.getCollections_.0": """({ id, qnt, maxProducts }) => {
                return WPP.catalog.getCollections(id, qnt, maxProducts);
            }""",
    "CatalogLayer.createCollection_.0": """({ collectionName, productsId }) => {
                return WPP.catalog.createCollection(collectionName, productsId);
            }""",
    "CatalogLayer.deleteCollection_.0": """({ collectionId }) => {
                return WPP.catalog.deleteCollection(collectionId);
            }""",
    "CatalogLayer.editCollection_.0": """({ collectionId, options }) => {
                return WPP.catalog.editCollection(collectionId, options);
            }""",
    "CatalogLayer.editProduct_.0": """({ productId, options }) => {
                return WPP.catalog.editProduct(productId, options);
            }""",
    "CatalogLayer.addProductImage_.0": """({ productId, image }) => {
                return WPP.catalog.addProductImage(productId, image);
            }""",
    "CatalogLayer.changeProductImage_.0": """({ productId, image }) => {
                return WPP.catalog.changeProductImage(productId, image);
            }""",
    "CatalogLayer.getBusinessProfilesProducts_.0": """({ id }) => {
                return WAPI.getBusinessProfilesProducts(id);
            }""",
    "CatalogLayer.getOrderbyMsg_.0": """({ messageId }) => {
                return WPP.order.get(messageId);
            }""",
    "CatalogLayer.removeProductImage_.0": "({productId, index}) => WPP.catalog.removeProductImage(productId, index)",
    "CatalogLayer.setProductVisibility_.0": "({productId, value}) => WPP.catalog.setProductVisibility(productId, value)",
    "CatalogLayer.updateCartEnabled_.0": "({value}) => WPP.catalog.updateCartEnabled(value)",
    "CommunityLayer.createCommunity_.0": """({ name, description, groupIds, options }) => {
                return WPP.community.create(options.name ?? name,
                    options.description ?? description, options.groupIds ?? groupIds);
            }""",
    "CommunityLayer.deactivateCommunity_.0": """({ communityId }) => {
                return WPP.community.deactivate(communityId);
            }""",
    "CommunityLayer.addSubgroupsCommunity_.0": """({ communityId, groupsIds }) => {
                return WPP.community.addSubgroups(communityId, groupsIds);
            }""",
    "CommunityLayer.removeSubgroupsCommunity_.0": """({ communityId, groupsIds }) => {
                return WPP.community.removeSubgroups(communityId, groupsIds);
            }""",
    "CommunityLayer.promoteCommunityParticipant_.0": """({ communityId, participantIds }) => {
                return WPP.community.promoteParticipants(communityId, participantIds);
            }""",
    "CommunityLayer.demoteCommunityParticipant_.0": """({ communityId, participantIds }) => {
                return WPP.community.demoteParticipants(communityId, participantIds);
            }""",
    "CommunityLayer.getCommunityParticipants_.0": """({ communityId }) => {
                return WPP.community.getParticipants(communityId);
            }""",
    "ControlsLayer.unblockContact_.0": "(contactId) => WPP.blocklist.unblockContact(contactId)",
    "ControlsLayer.blockContact_.0": "(contactId) => WPP.blocklist.blockContact(contactId)",
    "ControlsLayer.markUnseenMessage_.0": "(contactId) => WPP.chat.markIsUnread(contactId)",
    "ControlsLayer.deleteChat_.0": "(chatId) => WPP.chat.delete(chatId)",
    "ControlsLayer.archiveChat_.0": "({ chatId, option }) => WPP.chat.archive(chatId, option)",
    "ControlsLayer.pinChat_.0": "({ chatId, option }) => WPP.chat.pin(chatId, option)",
    "ControlsLayer.pinChat_.1": "(chatId) => WPP.chat.find(chatId)",
    "ControlsLayer.clearChat_.0": "({ chatId, keepStarred }) => WPP.chat.clear(chatId, keepStarred)",
    "ControlsLayer.deleteMessage_.0": """({ chatId, messageId, onlyLocal, deleteMediaInDevice }) => WPP.chat.deleteMessage(
            chatId,messageId,deleteMediaInDevice,!onlyLocal
            )""",
    "ControlsLayer.editMessage_.0": "({ msgId, newText, options }) =>  WPP.chat.editMessage(msgId, newText, options)",
    "ControlsLayer.editMessage_.1": "async ({ messageId }) => { return JSON.parse(JSON.stringify(await WAPI.getMessageById(messageId)));}",
    "ControlsLayer.starMessage_.0": "({ messagesId, star }) => WAPI.starMessages(messagesId, star)",
    "ControlsLayer.setLimit_.0": "({ key, value }) => WPP.conn.setLimit(key, value)",
    "ControlsLayer.setTemporaryMessages_.0": "({chatId, value}) => WAPI.setTemporaryMessages(chatId, value)",
    "GroupLayer.leaveGroup_.0": "(groupId) => WPP.group.leave(groupId)",
    "GroupLayer.getGroupMembersIds_.0": """(groupId) => Promise.resolve(WPP.group.getParticipants(groupId)).then(
          (participants) => participants.map((p) => p.id))""",
    "GroupLayer.getGroupInviteLink_.0": "(chatId) => WPP.group.getInviteCode(chatId)",
    "GroupLayer.revokeGroupInviteLink_.0": "(chatId) => WPP.group.revokeInviteCode(chatId)",
    "GroupLayer.getGroupInfoFromInviteLink_.0": "(inviteCode) => WPP.group.getGroupInfoFromInviteCode(inviteCode)",
    "GroupLayer.createGroup_.0": "({ groupName, contacts }) => WPP.group.create(groupName, contacts)",
    "GroupLayer.removeParticipant_.0": """({ groupId, participantId }) =>
        WPP.group.removeParticipants(groupId, participantId)""",
    "GroupLayer.addParticipant_.0": """({ groupId, participantId }) =>
        WPP.group.addParticipants(groupId, participantId)""",
    "GroupLayer.getGroupAdmins_.0": """(chatId) =>
        Promise.resolve(WPP.group.getParticipants(chatId)).then(
          (participants) => participants.map((p) => p.toJSON())
        )""",
    "GroupLayer.joinGroup_.0": "(inviteCode) => WPP.group.join(inviteCode)",
    "GroupLayer.setGroupDescription_.0": """({ groupId, description }) => {
                return WPP.group.setDescription(groupId, description);
            }""",
    "GroupLayer.setGroupSubject_.0": """({ groupId, subject }) => {
                return WPP.group.setSubject(groupId, subject);
            }""",
    "GroupLayer.setGroupIcon_.0": """({ groupId, pathOrBase64 }) => {
                return WPP.group.setIcon(groupId, pathOrBase64);
            }""",
    "GroupLayer.removeGroupIcon_.0": """({ groupId }) => {
                return WPP.group.removeIcon(groupId);
            }""",
    "GroupLayer.setGroupProperty_.0": """({ groupId, property, value }) => {
                return WPP.group.setProperty(groupId, property, value);
            }""",
    "GroupLayer.setMessagesAdminsOnly_.0": """({ groupId, value }) => {
                return WPP.group.setProperty(groupId, "announcement", value);
            }""",
    "GroupLayer.getGroupMembershipRequests_.0": """({ groupId }) => {
                return WPP.group.getMembershipRequests(groupId);
            }""",
    "GroupLayer.approveGroupMembershipRequest_.0": """({ groupId, membershipIds }) => {
                return WPP.group.approve(groupId, membershipIds);
            }""",
    "GroupLayer.rejectGroupMembershipRequest_.0": """({ groupId, membershipIds }) => {
                return WPP.group.reject(groupId, membershipIds);
            }""",
    "GroupLayer.promoteParticipant_.0": "({groupId, participantId}) => WPP.group.promoteParticipants(groupId, participantId)",
    "GroupLayer.demoteParticipant_.0": "({groupId, participantId}) => WPP.group.demoteParticipants(groupId, participantId)",
    "HostLayer._afterPageLoad.0": "(options) => {window.WPPConfig = options;}",
    "HostLayer._afterPageScriptInjectedHost.0": "() => {WPP.on('conn.auth_code_change', window.checkQrCode);}",
    "HostLayer._afterPageScriptInjectedHost.1": "() => {WPP.on('conn.main_ready', window.checkInChat);}",
    "HostLayer.unregisterServiceWorker.0": """() => {
                    setInterval(() => {
                      window.onerror = console.error;
                      window.onunhandledrejection = console.error;
                    }, 500);

                    // Remove existent service worker
                    navigator.serviceWorker
                      .getRegistrations()
                      .then((registrations) => {
                        for (let registration of registrations) {
                          registration.unregister();
                        }
                      })
                      .catch((err) => null);

                    // Disable service worker registration
                    // @ts-ignore
                    navigator.serviceWorker.register = new Promise(() => {});
                  }""",
    "HostLayer.__loginByCode.0": """async ({ phone }) => {
        return JSON.parse(
          JSON.stringify(await WPP.conn.genLinkDeviceCodeForPhoneNumber(phone))
        );
          }""",
    "HostLayer.getHostDevice.0": "() => WAPI.getHost()",
    "HostLayer.getWid.0": "() => WAPI.getWid()",
    "HostLayer.getWAVersion.0": "() => WAPI.getWAVersion()",
    "HostLayer.getWAJSVersion.0": "() => window.WPP.version",
    "HostLayer.getConnectionState.0": "() => {return window.WPP.whatsapp.Socket.state;}",
    "HostLayer.isConnected.0": "() => WAPI.isConnected()",
    "HostLayer.isOnline.0": "() => WPP.conn.isOnline()",
    "HostLayer.isLoggedIn.0": "() => WAPI.isLoggedIn()",
    "HostLayer.getBatteryLevel.0": "() => WAPI.getBatteryLevel()",
    "HostLayer.startPhoneWatchdog.0": "(interval) => WAPI.startPhoneWatchdog(interval)",
    "HostLayer.stopPhoneWatchdog.0": "() => WAPI.stopPhoneWatchdog()",
    "HostLayer.isMultiDevice.0": "() => window.WPP.conn.isMultiDevice()",
    "HostLayer.isMainLoaded.0": "() => window.WPP.conn.isMainLoaded()",
    "HostLayer.isMainInit.0": "() => window.WPP.conn.isMainInit()",
    "HostLayer.joinWebBeta.0": "(value) => WPP.conn.joinWebBeta(value)",
    "HostLayer.getBuildConstants.0": "() => WPP.conn.getBuildConstants()",
    "HostLayer.isLidMigrated.0": "() => WPP.whatsapp.functions.isLidMigrated()",
    "HostLayer.isAuthenticated.0": "() => typeof window.WPP !== 'undefined' && window.WPP.conn.isRegistered()",
    "HostLayer.sync_isAuthenticated.0": "() => typeof window.WPP !== 'undefined' && window.WPP.conn.isRegistered()",
    "HostLayer.scrapeImg.0": """() => {
              const selectorImg = document.querySelector('canvas');
              const selectorUrl = selectorImg.closest('[data-ref]');
              //const buttonReload = selectorUrl.querySelector('[role="button"]') as HTMLButtonElement;
              const buttonReload = selectorUrl.querySelector('button');
              if (buttonReload != null) {
                buttonReload.click();
                return true;
              }
              return false;
            }""",
    "HostLayer.scrapeImg.1": """() => {
              const selectorImg = document.querySelector('canvas');
              const selectorUrl = selectorImg.closest('[data-ref]');

              if (selectorImg != null && selectorUrl != null) {
                let data = {
                  base64Image: selectorImg.toDataURL(),
                  urlCode: selectorUrl.getAttribute('data-ref'),
                };
                return data;
              } else {
                return undefined;
              }
            }""",
    "HostLayer.isInsideChat.0": "() => typeof window.WPP !== 'undefined' && window.WPP.conn.isMainReady()",
    "HostLayer.sync_isInsideChat.0": "() => typeof window.WPP !== 'undefined' && window.WPP.conn.isMainReady()",
    "HostLayer.getWWebVersion.0": """() => {
            return window.Debug.VERSION;
        }""",
    "HostLayer.inject_api.0": """() => {
                        return window.WAPI?._wppWhatsappReady === true;}""",
    "HostLayer.inject_api.1": """() => {
                                  window.WPP.chat.defaultSendMessageOptions.createChat = true;
                                  window.WPP.conn.setKeepAlive(true);
                                }""",
    "HostLayer._onLoadingScreen.0": """function getElementByXpath(path) {
        return document.evaluate(path, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
            }""",
    "HostLayer._onLoadingScreen.1": """
     function load_ (selectors) {
      let observer = new MutationObserver(function () {
        let window2 = window;

        let progressBar = window2.getElementByXpath(selectors.PROGRESS);
        let progressBarNewTheme = window2.getElementByXpath(
          selectors.PROGRESS_NEW_THEME
        );
        let progressMessage = window2.getElementByXpath(
          selectors.PROGRESS_MESSAGE
        );
        let progressMessageNewTheme = window2.getElementByXpath(
          selectors.PROGRESS_MESSAGE_NEW_THEME
        );

        if (progressBar) {
          if (
            this.lastPercent !== progressBar.value ||
            this.lastPercentMessage !== progressMessage.innerText
          ) {
            window2.loadingScreen(progressBar.value, progressMessage.innerText);
            this.lastPercent = progressBar.value;
            this.lastPercentMessage = progressMessage.innerText;
          }
        } else if (progressBarNewTheme) {
          if (
            this.lastPercent !== progressBarNewTheme.value ||
            this.lastPercentMessage !== progressMessageNewTheme.innerText
          ) {
            const progressMsg =
              progressMessageNewTheme.innerText != 'WhatsApp'
                ? progressMessageNewTheme.innerText
                : '';
            window2.loadingScreen(progressBarNewTheme.value, progressMsg);
            this.lastPercent = progressBarNewTheme.value;
            this.lastPercentMessage = progressMsg;
          }
        }
      });

      observer.observe(document, {
        attributes: true,
        childList: true,
        characterData: true,
        subtree: true,
      });
    }""",
    "HostLayer.refreshLinkCode_.0": "() => WPP.conn.refreshLinkDeviceCode()",
    "HostLayer.isMainReady.0": "() => WPP.conn.isMainReady()",
    "HostLayer.isMainReady_.0": "() => WPP.conn.isMainReady()",
    "LabelsLayer.addNewLabel_.0": """({ name, options }) => {
        return WPP.labels.addNewLabel(name, options);
      }""",
    "LabelsLayer.addOrRemoveLabels_.0": """({ chatIds, options }) => {
        return WPP.labels.addOrRemoveLabels(chatIds, options);
      }""",
    "LabelsLayer.getAllLabels_.0": "() => WPP.labels.getAllLabels()",
    "LabelsLayer.getLabelById_.0": "({ id }) => {return WPP.labels.getLabelById(id); }",
    "LabelsLayer.deleteAllLabels_.0": "() => {return WPP.labels.deleteAllLabels();}",
    "LabelsLayer.deleteLabel_.0": "({ id }) => {return WPP.labels.deleteLabel(id); }",
    "ListenerLayer._afterPageScriptInjectedListener.0": """() => {
          function register(name, subscribe) {
            const callback = window[name];
            if (typeof callback !== 'function' || callback.exposed) return;
            try {
              subscribe(callback);
              callback.exposed = true;
            } catch (error) { console.error('[WPP] ' + name, error); }
          }
          const id = (value) => {
            if (value == null || typeof value === 'string') return value;
            const text = value._serialized || value.toString?.();
            return text && text !== '[object Object]' ? text : undefined;
          };
          register('onMessage', (cb) => WPP.on('chat.new_message', (msg) => {
            if (msg.isSentByMe || msg.id?.fromMe || msg.isStatusV3 || msg.isNotification) return;
            const value = WAPI.processMessageObj(msg, false, false);
            if (value) cb(value);
          }));
          register('onAnyMessage', (cb) => WPP.on('chat.new_message', (msg) => {
            const value = WAPI.processMessageObj(msg, true, false);
            if (value) cb(value);
          }));
          register('onAck', (cb) => WPP.on('chat.msg_ack_change', (data) => cb({
            ...data, id: id(data.id), chat: id(data.chat)
          })));
          register('onMessageEdit', (cb) => WPP.on('chat.msg_edited', (data) => cb({
            ...data, id: id(data.id), chat: id(data.chat),
            msg: WAPI.processMessageObj(data.msg, true, false)
          })));
          for (const name of ['onStateChange', 'onStreamChange', 'onStreamModeChanged',
              'onStreamInfoChanged', 'onAddedToGroup', 'onIncomingCall',
              'onInterfaceChange', 'onNotificationMessage', 'onLiveLocation']) {
            register(name, (cb) => WAPI[name](cb));
          }
          for (const [name, event] of Object.entries({
            onPresenceChanged: 'chat.presence_change',
            onReactionMessage: 'chat.new_reaction',
            onPollResponse: 'chat.poll_response',
            onOrderStatusUpdate: 'order.payment_status',
            onParticipantsChanged: 'group.participant_changed'
          })) {
            register(name, (cb) => WPP.on(event, (data) => {
              // Normalize public key objects without dropping other event fields.
              const value = {...data};
              for (const key of ['id', 'msgId', 'chatId', 'refId']) {
                if (data[key] != null) value[key] = id(data[key]) || data[key];
              }
              cb(value);
            }));
          }
          register('onNewChat', (cb) => WPP.on('chat.new_chat', (chat) => cb(WAPI._serializeChatObj(chat))));
          register('onUpdateLabel', (cb) => WPP.on('chat.update_label', (data) => cb({
            ...data, chat: WAPI._serializeChatObj(data.chat)
          })));
          register('onRevokedMessage', (cb) => WPP.on('chat.msg_revoke', (data) => cb({
            ...data, id: id(data.id), refId: id(data.refId),
            from: id(data.from), to: id(data.to), author: id(data.author)
          })));
          register('onBackendEvent', (cb) => WPP.on('conn.backend_event', (name, ...args) => cb(name, ...args)));
        }""",
    "ListenerLayer._afterPageScriptInjectedListener.1": "(func) => typeof window[func] === 'function'",
    "ListenerLayer.subscribePresence.0": "(id) => WAPI.subscribePresence(id)",
    "ListenerLayer.unsubscribePresence.0": "(id) => WAPI.unsubscribePresence(id)",
    "ListsLayer.createList_.0": "({name, chatIds, colorIndex}) => WPP.lists.create(name, chatIds, colorIndex ?? undefined)",
    "ListsLayer.getAllLists_.0": "() => WPP.lists.list()",
    "ListsLayer.addChatsToList_.0": "({listId, chatIds}) => WPP.lists.addChats(listId, chatIds)",
    "ListsLayer.removeChatsFromList_.0": "({listId, chatIds}) => WPP.lists.removeChats(listId, chatIds)",
    "ListsLayer.renameList_.0": "({listId, newName}) => WPP.lists.rename(listId, newName)",
    "ListsLayer.deleteList_.0": "({listId}) => WPP.lists.remove(listId)",
    "NewsletterLayer.createNewsletter_.0": """({ name, options }) => {
                return WPP.newsletter.create(name, options);
            }""",
    "NewsletterLayer.editNewsletter_.0": """({ id, options }) => {
                return WPP.newsletter.edit(id, options);
            }""",
    "NewsletterLayer.destroyNewsletter_.0": """({ id }) => {
                return WPP.newsletter.destroy(id);
            }""",
    "NewsletterLayer.muteNewsletter_.0": """({ id }) => {
                return WPP.newsletter.mute(id);
            }""",
    "ProfileLayer.sendMute_.0": "({id, time, type}) => WAPI.sendMute(id, time, type)",
    "ProfileLayer.setTheme_.0": "(type_) => WAPI.setTheme(type_)",
    "ProfileLayer.setProfileStatus_.0": "(status) => WPP.profile.setMyStatus(status)",
    "ProfileLayer.getProfileStatus_.0": "() => WPP.profile.getMyStatus()",
    "ProfileLayer.getProfileName_.0": "() => WPP.profile.getMyProfileName()",
    "ProfileLayer.editBusinessProfile_.0": """({ options }) => {
                return WPP.profile.editBusinessProfile(options);
            }""",
    "ProfileLayer.setProfilePic_.0": "(base64) => WPP.profile.setMyProfilePicture(base64)",
    "ProfileLayer.setProfilePic_.1": "({to, base64}) => WPP.group.setIcon(to, base64)",
    "ProfileLayer.setProfileName_.0": "(name) => WPP.profile.setMyProfileName(name)",
    "ProfileLayer.removeMyProfilePicture_.0": "() => WPP.profile.removeMyProfilePicture()",
    "RetrieverLayer.getListMutes_.0": "(type) => WAPI.getListMute(type)",
    "RetrieverLayer.getSessionTokenBrowser_.0": "() => WPP.conn.isMultiDevice()",
    "RetrieverLayer.getSessionTokenBrowser_.1": """() => {
        if (window.localStorage) {
          return {
            WABrowserId: window.localStorage.getItem('WABrowserId'),
            WASecretBundle: window.localStorage.getItem('WASecretBundle'),
            WAToken1: window.localStorage.getItem('WAToken1'),
            WAToken2: window.localStorage.getItem('WAToken2'),
          };
        }
        return null;
      }""",
    "RetrieverLayer.getSessionTokenBrowser_.2": "() => {window['pathSession'] = true;}",
    "RetrieverLayer.getSessionTokenBrowser_.3": """() => {
          if (window.localStorage) {
            return {
              WABrowserId:
                window.localStorage.getItem('WABrowserId') || 'MultiDevice',
              WASecretBundle: 'MultiDevice',
              WAToken1: 'MultiDevice',
              WAToken2: 'MultiDevice',
            };
          }
          return null;
        }""",
    "RetrieverLayer.getTheme_.0": "() => WAPI.getTheme()",
    "RetrieverLayer.getBlockList_.0": " () => WPP.blocklist.all().map((b) => b.toString())",
    "RetrieverLayer.getAllChats_.0": "() => WAPI.getAllChats()",
    "RetrieverLayer.getAllChats_.1": "() => WAPI.getAllChatsWithNewMsg()",
    "RetrieverLayer.listChats_.0": """
        async ({ options }) => {
        const chats = await WPP.chat.list(options);

        const serialized = chats.map((c) => WAPI._serializeChatObj(c));
        return serialized;
      }
        """,
    "RetrieverLayer.checkNumberStatus_.0": "(contactId) => WAPI.checkNumberStatus(contactId)",
    "RetrieverLayer.getAllChatsWithMessages_.0": """(withNewMessageOnly) =>
        WAPI.getAllChatsWithMessages(withNewMessageOnly)""",
    "RetrieverLayer.getAllGroups_.0": """async ({ withNewMessagesOnly }) => {
        const chats = await WPP.chat.list({
          onlyGroups: true,
          onlyWithUnreadMessage: withNewMessagesOnly,
        });

        const groups = await Promise.all(
          chats.map((c) => WPP.group.ensureGroup(c.id))
        );

        return groups.map((g) => WAPI._serializeChatObj(g));
      }""",
    "RetrieverLayer.getAllBroadcastList_.0": "() => WAPI.getAllChats()",
    "RetrieverLayer.getContact_.0": "(contactId) => WAPI.getContact(contactId)",
    "RetrieverLayer.getAllContacts_.0": "() => WAPI.getAllContacts()",
    "RetrieverLayer.getChatById_.0": "(contactId) => WAPI.getChatById(contactId)",
    "RetrieverLayer.getProfilePicFromServer_.0": "(chatId) => WAPI._profilePicfunc(chatId)",
    "RetrieverLayer.loadEarlierMessages_.0": "(contactId) => WAPI.loadEarlierMessages(contactId)",
    "RetrieverLayer.getStatus_.0": """async (contactId) => {
                                        const status = await WPP.contact.getStatus(contactId);

                                        return {
                                          id: contactId,
                                          status: status?.status || status,
                                        };
                                      }""",
    "RetrieverLayer.getNumberProfile_.0": "(contactId) => WAPI.getNumberProfile(contactId)",
    "RetrieverLayer.getUnreadMessages_.0": """({ includeMe, includeNotifications, useUnreadCount }) =>
        WAPI.getUnreadMessages(includeMe, includeNotifications, useUnreadCount)""",
    "RetrieverLayer.getAllUnreadMessages_.0": "() => WAPI.getAllUnreadMessages()",
    "RetrieverLayer.getAllNewMessages_.0": "() => WAPI.getAllNewMessages()",
    "RetrieverLayer.getAllMessagesInChat_.0": """({ chatId, includeMe, includeNotifications }) =>
        WAPI.getAllMessagesInChat(chatId, includeMe, includeNotifications)""",
    "RetrieverLayer.loadAndGetAllMessagesInChat_.0": """({ chatId, includeMe, includeNotifications }) =>
        WAPI.loadAndGetAllMessagesInChat(chatId, includeMe, includeNotifications)""",
    "RetrieverLayer.getChatIsOnline_.0": "(chatId) => WAPI.getChatIsOnline(chatId)",
    "RetrieverLayer.getLastSeen_.0": "(chatId) => WAPI.getLastSeen(chatId)",
    "RetrieverLayer.getPlatformFromMessage_.0": "(msgId) => WPP.chat.getPlatformFromMessage(msgId)",
    "RetrieverLayer.getReactions_.0": "(msgId) => WPP.chat.getReactions(msgId)",
    "RetrieverLayer.getVotes_.0": "(msgId) => WPP.chat.getVotes(msgId)",
    "RetrieverLayer.getGroupSizeLimit_.0": "() => WPP.group.getGroupSizeLimit()",
    "RetrieverLayer.getOrder_.0": "(msgId) => WPP.order.get(msgId)",
    "RetrieverLayer.getCommonGroups_.0": "({ wid }) => WPP.contact.getCommonGroups(wid)",
    "RetrieverLayer.getPnLidEntry_.0": "(phoneOrLid) => WPP.contact.getPnLidEntry(phoneOrLid)",
    "RetrieverLayer.getMessagesFromRowId_.0": "({options}) => WPP.indexdb.getMessagesFromRowId(options)",
    "SenderLayer.sendPollMessage_.0": """({ chatId, name, choices, options }) => {
                return WPP.chat.sendCreatePollMessage(chatId, name, choices, options);
            }""",
    "SenderLayer.sendOrderMessage_.0": """({ to, items, options }) => {
                return WPP.chat.sendChargeMessage(to, items, options);
            }""",
    "SenderLayer.sendWatermarkMessage_.0": """({ to, content, options }) => {
                return WPP.chat.sendTextMessage(to, content, {
                    ...options,
                    waitForAck: true
                });
            }""",
    "SenderLayer.sendLinkPreview_.0": """({ chatId, message }) => {
                    return WPP.chat.sendTextMessage(chatId, message, { linkPreview: true });
                    }""",
    "SenderLayer.sendText_.0": """({ to, content, options }) =>
                            WPP.chat.sendTextMessage(to, content, {
                              ...options,
                              waitForAck: true,
                            })""",
    "SenderLayer.sendPixKey_.0": """({ to, params, options }) =>
        WPP.chat.sendPixKeyMessage(to, params, {
          ...options,
          waitForAck: true,
        })""",
    "SenderLayer.sendPixKey_.1": """async ({ messageId }) => {
        return JSON.parse(JSON.stringify(await WAPI.getMessageById(messageId)));
      }""",
    "SenderLayer.sendMessageOptions_.0": """({ chat, content, options }) => {
        return WAPI.sendMessageOptions(chat, content, options);
      }""",
    "SenderLayer.sendMessageOptions_.1": "(messageId) => WAPI.getMessageById(messageId)",
    "SenderLayer.sendImageFromBase64_.0": """async ({
        to,
        base64,
        filename,
        caption,
        quotedMessageId,
        isViewOnce,
        mentionedList,
        options
      }) => {
        const result = await WPP.chat.sendFileMessage(to, base64, {
          ...options,
          type: 'image',
          isViewOnce: isViewOnce ?? options.isViewOnce,
          messageId: options.msgId ?? options.messageId,
          filename: filename || options.filename,
          caption: caption || options.caption,
          quotedMsg: quotedMessageId ?? options.quotedMsg,
          waitForAck: true,
          detectMentioned: options.detectMentioned ?? true,
          mentionedList: mentionedList ?? options.mentionedList,
        });

        return {
          ack: result.ack,
          id: result.id,
          sendMsgResult: await result.sendMsgResult,
          error: result.message,
        };
      }""",
    "SenderLayer.reply_.0": """({ to, content, quotedMsg }) => {
                                    return WPP.chat.sendTextMessage(to, content, { quotedMsg });
                                  }""",
    "SenderLayer.sendPttFromBase64.0": """
            async ({ to, base64, filename, caption, quotedMessageId, messageId }) => {
        const result = await WPP.chat.sendFileMessage(to, base64, {
          type: 'audio',
          isPtt: true,
          filename,
          caption,
          quotedMsg: quotedMessageId,
          waitForAck: true,
          messageId: messageId,
        });

        return {
          ack: result.ack,
          id: result.id,
          sendMsgResult: await result.sendMsgResult,
        };
      }
      """,
    "SenderLayer.sendFile_.0": """async ({ to, base64, options }) => {
        const result = await WPP.chat.sendFileMessage(to, base64, options);
        return {
          ack: result.ack,
          id: result.id,
          sendMsgResult: await result.sendMsgResult,
        };
      }""",
    "SenderLayer.sendVideoAsGifFromBase64.0": """
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
    "SenderLayer.sendContactVcard_.0": """({ to, contactsId, name }) => {
        return WPP.chat.sendVCardContactMessage(to, {
          id: contactsId,
          name: name,
        });
      }""",
    "SenderLayer.forwardMessages_.0": "({ toChatId, msgId, options }) =>WPP.chat.forwardMessage(toChatId, msgId, options)",
    "SenderLayer.forwardMessagesV2_.0": """({ toChatId, messages, options }) =>
        WPP.chat.forwardMessages(toChatId, messages, options)""",
    "SenderLayer.sendLocation_.0": """async ({ to, options }) => {
        const result = await WPP.chat.sendLocationMessage(to, options);

        return {
          ack: result.ack,
          id: result.id,
          sendMsgResult: await result.sendMsgResult,
        };
      }""",
    "SenderLayer.sendSeen_.0": "(chatId) => WPP.chat.markIsRead(chatId)",
    "SenderLayer.startTyping_.0": "({ to, duration }) => WPP.chat.markIsComposing(to, duration ?? undefined)",
    "SenderLayer.stopTyping_.0": "(to) => WPP.chat.markIsPaused(to)",
    "SenderLayer.sendImageAsSticker_.0": """async ({ to, base64, options }) => {
            const result = await WPP.chat.sendFileMessage(to, base64, {
              type: 'sticker',
              ...options,
              waitForAck: true,
            });

            return {
              ack: result.ack,
              id: result.id,
              sendMsgResult: await result.sendMsgResult,
            };
          }""",
    "SenderLayer.setOnlinePresence_.0": "(online) => WPP.conn.markAvailable(online)",
    "SenderLayer.sendMentioned_.0": """({ to, message, mentioned, options }) => WPP.chat.sendTextMessage(to, message, {
          ...options,
          detectMentioned: true,
          mentionedList: mentioned,
        })""",
    "SenderLayer.sendListMessage_.0": "({ to, options }) => WPP.chat.sendListMessage(to, options)",
    "SenderLayer.setChatState_.0": """({ chatState, chatId }) => {
                return WAPI.sendChatstate(chatState, chatId);
              }""",
    "SenderLayer.sendContactVcardList_.0": "({to, contacts}) => WPP.chat.sendVCardContactMessage(to, contacts)",
    "SenderLayer.markPlayed_.0": "({msgId}) => WPP.chat.markPlayed(msgId)",
    "SenderLayer.startRecording_.0": "({to, duration}) => WPP.chat.markIsRecording(to, duration ?? undefined)",
    "SenderLayer.stopRecording_.0": "({to}) => WPP.chat.markIsPaused(to)",
    "SenderLayer.sendReactionToMessage_.0": "({msgId, reaction}) => WPP.chat.sendReactionToMessage(msgId, reaction)",
    "SenderLayer.sendMessageWithThumb_.0": "({thumb, url, title, description, chatId}) => WPP.chat.sendTextMessage(chatId, url, {linkPreview: {thumbnail: thumb, canonicalUrl: url, title, description, matchedText: url}})",
    "StatusLayer.sendImageStatus_.0": "({base64, options}) => WPP.status.sendImageStatus(base64, options);",
    "StatusLayer.sendVideoStatus_.0": "({base64, options}) => WPP.status.sendVideoStatus(base64, options);",
    "StatusLayer.sendTextStatus_.0": "({text, options}) => WPP.status.sendTextStatus(text, options);",
    "StatusLayer.sendReadStatus_.0": "({ chatId, statusId }) => WPP.status.sendReadStatus(chatId, statusId);",
    "UILayer.openChat_.0": "(chatId) => WPP.chat.openChatBottom(chatId, undefined)",
    "UILayer.openChatAt_.0": "({chatId, messageId}) => WPP.chat.openChatAt(chatId, messageId, undefined)",
    "UILayer.closeChat_.0": "() => WPP.chat.closeChat()",
    "UILayer.getActiveChat_.0": "() => WPP.chat.getActiveChat()",
    "UILayer.getAutoDownloadSettings_.0": "() => WPP.conn.getAutoDownloadSettings()",
    "UILayer.setAutoDownloadSettings_.0": "({settings}) => WPP.conn.setAutoDownloadSettings(settings)",
    "Whatsapp.__intervalHandel.0": "() => typeof window.WPP !== 'undefined' && window.WPP.conn.isRegistered()",
    "Whatsapp.afterPageScriptInjected.0": "() => typeof window.WPP !== 'undefined' &&  WPP.conn.isRegistered()",
    "Whatsapp.downloadFile_.0": "(data) => WAPI.downloadFile(data)",
    "Whatsapp.downloadMedia_.0": "async (messageId) => WPP.util.blobToBase64(await WPP.chat.downloadMedia(messageId))",
    "Whatsapp.useHere_.0": "() => WAPI.takeOver()",
    "Whatsapp.logout_.0": "() => WPP.conn.logout()",
    "Whatsapp.getMessageById_.0": "(messageId) => WAPI.getMessageById(messageId)",
    "Whatsapp.getMessages_.0": "({ chatId, params }) => WAPI.getMessages(chatId, params)",
    "Whatsapp.rejectCall_.0": "(callId) => WPP.call.rejectCall(callId)",
}
