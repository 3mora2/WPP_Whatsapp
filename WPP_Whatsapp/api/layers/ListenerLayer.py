from event_emitter import EventEmitter
from WPP_Whatsapp.api.layers.ProfileLayer import ProfileLayer

OnMessage = 'onMessage'
OnAnyMessage = 'onAnyMessage'
onAck = 'onAck'
onNotificationMessage = 'onNotificationMessage'
onParticipantsChanged = 'onParticipantsChanged'
onStateChange = 'onStateChange'
onStreamChange = 'onStreamChange'
onIncomingCall = 'onIncomingCall'
onInterfaceChange = 'onInterfaceChange'
onPresenceChanged = 'onPresenceChanged'
onLiveLocation = 'onLiveLocation'


class HandelFunc:
    func = None
    session = None
    __listenerEmitter: EventEmitter

    def __init__(self, func, session, logger, __listenerEmitter):
        self.func = func
        self.session = session
        self.__listenerEmitter = __listenerEmitter
        self.logger = logger

    def handel_func(self, *args, **kwargs):
        count = self.__listenerEmitter.listener_count(self.func)
        if count > 0:
            self.logger.debug(f'{self.session}: Emitting {self.func} event ({count} registered)')
        self.__listenerEmitter.emit(self.func, *args, **kwargs)


class ListenerLayer(ProfileLayer):
    __listenerEmitter = EventEmitter()

    def __init__(self):
        self.__listenerEmitter.max_listener = 0
        self.__listenerEmitter.on(onInterfaceChange, self.onInterfaceChange_)
        # ToDo:
        # self.__listenerEmitter[captureRejectionSymbol]

    def onInterfaceChange_(self, state):
        self.logger.info(
            f'{self.session}: http => Current state: {state.get("mode")} ({state.get("displayInfo")}) ({state.get("info")}) ')

    async def _afterPageScriptInjectedListener(self):
        functions = [
            OnMessage,
            OnAnyMessage,
            onAck,
            onNotificationMessage,
            onParticipantsChanged,
            onStateChange,
            onStreamChange,
            onIncomingCall,
            onInterfaceChange,
            onPresenceChanged,
            onLiveLocation,
            'onAddedToGroup',
            'onIncomingCall',
            'onRevokedMessage',
            'onReactionMessage',
            'onPollResponse'
        ]

        for func in functions:
            has = await self.ThreadsafeBrowser.page_evaluate("(func) => typeof window[func] === 'function'", func, page=self.page)
            if not has:
                self.logger.debug(f'{self.session}: Exposing {func} function')
                handel_func = HandelFunc(func, self.session, self.logger, self.__listenerEmitter).handel_func
                await self.ThreadsafeBrowser.expose_function(func, handel_func, page=self.page)

        await self.ThreadsafeBrowser.page_evaluate("""() => {
        try {
          if (!window['onMessage'].exposed) {
            WPP.on('chat.new_message', (msg) => {
              if (msg.isSentByMe || msg.isStatusV3) {
                return;
              }
              const serialized = WAPI.processMessageObj(msg, false, false);
              if (serialized) {
                window['onMessage'](serialized);
              }
            });

            window['onMessage'].exposed = true;
          }
        } catch (error) {
          console.error(error);
        }
        try {
          if (!window['onAnyMessage'].exposed) {
            WPP.on('chat.new_message', (msg) => {
              const serialized = WAPI.processMessageObj(msg, true, false);
              if (serialized) {
                window['onAnyMessage'](serialized);
              }
            });
            window['onAnyMessage'].exposed = true;
          }
        } catch (error) {
          console.error(error);
        }
        try {
          if (!window['onStateChange'].exposed) {
            window.WAPI.onStateChange(window['onStateChange']);
            window['onStateChange'].exposed = true;
          }
        } catch (error) {
          console.error(error);
        }
        try {
          if (!window['onNotificationMessage'].exposed) {
            window.WAPI.onNotificationMessage(window['onNotificationMessage']);
            window['onNotificationMessage'].exposed = true;
          }
        } catch (error) {
          console.error(error);
        }
        /*
        try {
          if (!window['onAck'].exposed) {
            window.WAPI.waitNewAcknowledgements(window['onAck']);
            window['onAck'].exposed = true;
          }
        } catch (error) {
          console.error(error);
        }
        try {
          if (!window['onStreamChange'].exposed) {
            window.WAPI.onStreamChange(window['onStreamChange']);
            window['onStreamChange'].exposed = true;
          }
        } catch (error) {
          console.error(error);
        }
        try {
          if (!window['onAddedToGroup'].exposed) {
            window.WAPI.onAddedToGroup(window['onAddedToGroup']);
            window['onAddedToGroup'].exposed = true;
          }
        } catch (error) {
          console.error(error);
        }
        try {
          if (!window['onIncomingCall'].exposed) {
            window.WAPI.onIncomingCall(window['onIncomingCall']);
            window['onIncomingCall'].exposed = true;
          }
        } catch (error) {
          console.error(error);
        }
        try {
          if (!window['onInterfaceChange'].exposed) {
            window.WAPI.onInterfaceChange(window['onInterfaceChange']);
            window['onInterfaceChange'].exposed = true;
          }
        } catch (error) {
          console.error(error);
        }

        try {
          if (!window['onPresenceChanged'].exposed) {
            WPP.on('chat.presence_change', window['onPresenceChanged']);
            window['onPresenceChanged'].exposed = true;
          }
        } catch (error) {
          console.error(error);
        }
        try {
          if (!window['onLiveLocation'].exposed) {
            window.WAPI.onLiveLocation(window['onLiveLocation']);
            window['onLiveLocation'].exposed = true;
          }
        } catch (error) {
          console.error(error);
        }
        try {
          if (!window['onRevokedMessage'].exposed) {
            WPP.on('chat.msg_revoke', (data) => {
              const eventData = {
                author: data.author,
                from: data.from,
                to: data.to,
                id: data.id._serialized,
                refId: data.refId._serialized,
              };
              window['onRevokedMessage'](eventData);
            });
            window['onRevokedMessage'].exposed = true;
          }
        } catch (error) {
          console.error(error);
        }
        try {
          if (!window['onReactionMessage'].exposed) {
            WPP.on('chat.new_reaction', (data) => {
              const eventData = {
                id: data.id,
                msgId: data.msgId,
                reactionText: data.reactionText,
                read: data.read,
                orphan: data.orphan,
                orphanReason: data.orphanReason,
                timestamp: data.timestamp,
              };
              window['onReactionMessage'](eventData);
            });
            window['onReactionMessage'].exposed = true;
          }
        } catch (error) {
          console.error(error);
        }
        try {
          if (!window['onPollResponse'].exposed) {
            WPP.on('chat.poll_response', (data) => {
              const eventData = {
                msgId: data.msgId,
                chatId: data.chatId,
                selectedOptions: data.selectedOptions,
                timestamp: data.timestamp,
                sender: data.sender,
              };
              window['onPollResponse'](eventData);
            });
            window['onPollResponse'].exposed = true;
          }
        } catch (error) {
          console.error(error);
        }
        try {
          if (!window['onParticipantsChanged'].exposed) {
            WPP.on('group.participant_changed', (participantChangedEvent) => {
              window['onParticipantsChanged'](participantChangedEvent);
            });
            window['onParticipantsChanged'].exposed = true;
          }
        } catch (error) {
          console.error(error);
        }
        */
      }""", page=self.page)

    def __registerEvent(self, event, listener):
        """
        /**
        * Register the event and create a disposable object to stop the listening
        * @param event Name of event
        * @param listener The function to execute
        * @returns Disposable object to stop the listening
        */
        """
        self.logger.debug(f'{self.session}: Registering {str(event)} event')
        self.__listenerEmitter.on(event, listener)
        return lambda: self.off_listener(event, listener)

    def off_listener(self, event, listener):
        # print("off", event, listener)
        self.__listenerEmitter.remove_listener(event, listener)

    def onMessage(self, callback):
        """
          /**
           * @event Listens to all new messages received only.
           * @returns Disposable object to stop the listening
           */
        """
        return self.__registerEvent(OnMessage, callback)

    def onAnyMessage(self, callback):
        """
          /**
           * @event Listens to all new messages, sent and received.
           * @param to callback
           * @fires Message
           * @returns Disposable object to stop the listening
           */
        """
        return self.__registerEvent(OnAnyMessage, callback)

    def onNotificationMessage(self, callback):
        """ """
        return self.__registerEvent(onNotificationMessage, callback)

    def onStateChange(self, callback):
        """ """
        return self.__registerEvent(onStateChange, callback)

    def onStreamChange(self, callback):
        """ """
        return self.__registerEvent(onStreamChange, callback)

    def onInterfaceChange(self, callback):
        """ """
        return self.__registerEvent(onInterfaceChange, callback)

    def onAck(self, callback):
        """ """
        return self.__registerEvent(onAck, callback)

    def onLiveLocation(self, id, callback):
        """ ToDo: """
        # return self.__registerEvent(onLiveLocation, callback)

    def onParticipantsChanged(self, callback):
        """ ToDo: """
        # return self.__registerEvent(onNotificationMessage, callback)

    def onAddedToGroup(self, callback):
        """ """
        return self.__registerEvent('onAddedToGroup', callback)

    def onIncomingCall(self, callback):
        """ """
        return self.__registerEvent("onIncomingCall", callback)

    def onPresenceChanged(self, id_, callback):
        """ TODO:"""
        # return self.__registerEvent(onPresenceChanged, callback)

    async def subscribePresence(self, id_):
        """
          /**
           * Subscribe presence of a contact or group to use in onPresenceChanged (see {@link onPresenceChanged})
           *
           * ```typescript
           * // subcribe all contacts
           * const contacts = client.getAllContacts();
           * client.subscribePresence(contacts.map((c) => c.id._serialized));
           *
           * // subcribe all groups participants
           * const chats = client.getAllGroups(false);
           * for (const c of chats) {
           *   const ids = c.groupMetadata.participants.map((p) => p.id._serialized);
           *   client.subscribePresence(ids);
           * }
           * ```
           *
           * @param id contact id (xxxxx@c.us) or group id: xxxxx-yyyy@g.us
           * @returns number of subscribed
           */
        """
        await self.ThreadsafeBrowser.page_evaluate("(id) => WAPI.subscribePresence(id)", id_, page=self.page)

    async def unsubscribePresence(self, id_):
        await self.ThreadsafeBrowser.page_evaluate("(id) => WAPI.unsubscribePresence(id)", id_, page=self.page)

    def onRevokedMessage(self, callback):
        """ """
        return self.__registerEvent("onRevokedMessage", callback)

    def onReactionMessage(self, callback):
        """ """
        return self.__registerEvent("onReactionMessage", callback)

    def onPollResponse(self, callback):
        """ """
        return self.__registerEvent("onPollResponse", callback)
