import asyncio

from WPP_Whatsapp.core.events import EVENT_NAMES, EventEmitter, EventDispatcher
from playwright.async_api import Error

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
onMessageEdit = 'onMessageEdit'


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
    __listenerEmitter: EventEmitter

    def __init__(self):
        self.__listenerEmitter = EventEmitter()
        self.__listenerEmitter.max_listener = 0
        self.__listenerEmitter.on(onInterfaceChange, self.onInterfaceChange_)
        # ToDo:
        # self.__listenerEmitter[captureRejectionSymbol]

    def onInterfaceChange_(self, state):
        self.logger.info(
            f'{self.session}: http => Current state: {state.get("mode")} ({state.get("displayInfo")}) ({state.get("info")}) ')

    async def _afterPageScriptInjectedListener(self):
        self.logger.debug(f'{self.session}: Start Exposing function')
        functions = EVENT_NAMES

        for func in functions:
            has = await self._evaluate_js('ListenerLayer._afterPageScriptInjectedListener.1', func,
                                                             page=self.page)
            if not has:
                self.logger.debug(f'{self.session}: Exposing {func} function')
                handel_func = HandelFunc(func, self.session, self.logger, self.__listenerEmitter).handel_func
                async def dispatch(*args, _handler=handel_func, **kwargs):
                    return await self._event_dispatcher().submit(_handler.__self__.func, *args, **kwargs)
                try:
                    await self.ThreadsafeBrowser.expose_function(func, dispatch, page=self.page)
                except Error as e:
                    if "has been already registered" not in e.message:
                        raise e

        await self._evaluate_js('ListenerLayer._afterPageScriptInjectedListener.0', page=self.page)

    def _event_dispatcher(self):
        dispatcher = getattr(self, '_dispatcher', None)
        if dispatcher is None:
            options = getattr(self, 'options', {})
            self._dispatcher = dispatcher = EventDispatcher(
                self.__listenerEmitter, maxsize=options.get('eventQueueSize', 256),
                on_error=lambda kind: self.logger.warning('Event callback failed (%s)', kind))
        return dispatcher

    async def close_listeners(self):
        dispatcher = getattr(self, '_dispatcher', None)
        if dispatcher is not None:
            await dispatcher.close()
        self.__listenerEmitter.remove_all_listeners()

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

    def onMessageEdit(self, callback):
        """ """
        return self.__registerEvent(onMessageEdit, callback)

    def _filtered_listener(self, event, ids, callback, field='id'):
        if callback is None and callable(ids):
            callback, ids = ids, None
        if not callable(callback):
            raise TypeError('A callable event callback is required')
        ids = [ids] if isinstance(ids, str) else list(ids or [])
        def listener(data):
            value = data.get(field)
            if isinstance(value, dict):
                value = value.get('_serialized')
            if not ids or value in ids:
                callback(data)
        return self.__registerEvent(event, listener)

    def onLiveLocation(self, id=None, callback=None):
        return self._filtered_listener(onLiveLocation, id, callback)

    def onParticipantsChanged(self, groupId=None, callback=None):
        if callback is None and callable(groupId):
            callback, groupId = groupId, None
        if not callable(callback):
            raise TypeError('A callable event callback is required')
        def listener(data):
            if groupId and data.get('groupId') != groupId:
                return
            callback({**data, 'by': data.get('author'), 'byPushName': data.get('authorPushName'),
                      'who': data.get('participants')})
        return self.__registerEvent(onParticipantsChanged, listener)

    def onAddedToGroup(self, callback):
        """ """
        return self.__registerEvent('onAddedToGroup', callback)

    def onIncomingCall(self, callback):
        """ """
        return self.__registerEvent("onIncomingCall", callback)

    def onPresenceChanged(self, id_=None, callback=None):
        if callback is None and callable(id_):
            callback, id_ = id_, None
        if id_:
            self.ThreadsafeBrowser.run_threadsafe(self.subscribePresence, id_)
        return self._filtered_listener(onPresenceChanged, id_, callback)

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
        return await self._evaluate_js('ListenerLayer.subscribePresence.0', id_, page=self.page)

    async def unsubscribePresence(self, id_):
        return await self._evaluate_js('ListenerLayer.unsubscribePresence.0', id_, page=self.page)

    def onRevokedMessage(self, callback):
        """ """
        return self.__registerEvent("onRevokedMessage", callback)

    def onReactionMessage(self, callback):
        """ """
        return self.__registerEvent("onReactionMessage", callback)

    def onPollResponse(self, callback):
        """ """
        return self.__registerEvent("onPollResponse", callback)

    def onStreamModeChanged(self, callback):
        return self.__registerEvent("onStreamModeChanged", callback)

    def onStreamInfoChanged(self, callback):
        return self.__registerEvent("onStreamInfoChanged", callback)

    def onBackendEvent(self, callback):
        return self.__registerEvent("onBackendEvent", callback)

    def onUpdateLabel(self, callback):
        return self.__registerEvent("onUpdateLabel", callback)

    def onOrderStatusUpdate(self, callback):
        return self.__registerEvent("onOrderStatusUpdate", callback)

    def onNewChat(self, callback):
        return self.__registerEvent("onNewChat", callback)

    on_message = onMessage

    on_any_message = onAnyMessage

    on_notification_message = onNotificationMessage

    on_state_change = onStateChange

    on_stream_change = onStreamChange

    on_incoming_call = onIncomingCall

    on_interface_change = onInterfaceChange

    on_ack = onAck

    on_message_edit = onMessageEdit

    on_live_location = onLiveLocation

    on_participants_changed = onParticipantsChanged

    on_added_to_group = onAddedToGroup

    on_presence_changed = onPresenceChanged

    on_revoked_message = onRevokedMessage

    on_reaction_message = onReactionMessage

    on_poll_response = onPollResponse

    on_stream_mode_changed = onStreamModeChanged

    on_stream_info_changed = onStreamInfoChanged

    on_backend_event = onBackendEvent

    on_update_label = onUpdateLabel

    on_order_status_update = onOrderStatusUpdate

    on_new_chat = onNewChat
