const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

async function main() {
  const events = {};
  const messages = [];
  const calls = [];
  const chat = { msgs: { getModelsArray: () => messages } };
  const sandbox = {
    console,
    Promise,
    Store: {}, // Legacy loader modules are unrelated to these regression tests.
    setTimeout: () => 0,
    setInterval: () => 0,
    clearInterval: () => {},
    sessionStorage: { getItem: () => null, setItem: () => {} },
    addEventListener: () => {},
    WPP: {
      isReady: true,
      on: (name, cb) => (events[name] ||= []).push(cb),
      whatsapp: {
        MsgStore: { on: () => {} },
        Socket: { on: () => {}, state: 'CONNECTED' },
      },
      chat: {
        get: async () => chat,
        getMessages: async (id, params) => {
          calls.push({ id, params });
          return messages;
        },
      },
    },
  };
  sandbox.window = sandbox;
  vm.createContext(sandbox);
  const root = path.resolve(__dirname, '../..');
  vm.runInContext(fs.readFileSync(path.join(root, 'WPP_Whatsapp/js_lib/wapi.js'), 'utf8'), sandbox);
  await Promise.resolve();
  const WAPI = sandbox.WAPI;

  const groupId = '120000000000000000@g.us';
  const participant = '123456789@lid';
  class CurrentMsgKey {
    constructor(fromMe = false) {
      this.fromMe = fromMe;
      this.remote = { _serialized: groupId };
      this.id = 'ABCDEF';
      this.participant = { _serialized: participant };
      this.$1 = `${fromMe}_${groupId}_ABCDEF_${participant}`;
    }
    toString() { return this.$1; }
  }
  function message(id) {
    return {
      id, from: { _serialized: groupId }, to: { _serialized: '999@c.us' },
      author: { _serialized: participant }, body: 'hello', t: 123,
      type: 'chat', isGroupMsg: true, isNotification: false,
      caption: 'keep media metadata',
      toJSON() { return { ...this }; },
    };
  }
  const incoming = message(new CurrentMsgKey());
  // Reproduce #84 against the actual, unmodified upstream serializer.
  assert.equal(WAPI._serializeMessageObj(incoming).id, undefined);
  vm.runInContext(fs.readFileSync(path.join(root, 'WPP_Whatsapp/js_lib/message_compat.js'), 'utf8'), sandbox);
  await sandbox.__wppWhatsappReady;
  const expectedId = incoming.id.toString();
  assert.equal(WAPI.processMessageObj(incoming, false, false).id, expectedId);
  assert.equal(WAPI.processMessageObj(incoming, false, false).chatId, groupId);
  assert.equal(WAPI.processMessageObj(incoming, false, false).author, participant);
  assert.equal(WAPI.processMessageObj(incoming, false, false).caption, incoming.caption);

  const serialized = JSON.parse(JSON.stringify(WAPI.processMessageObj(incoming, false, false)));
  assert.equal(serialized.id, expectedId);
  const legacy = message({ _serialized: 'false_123@c.us_OLD', fromMe: false });
  assert.equal(WAPI._serializeMessageObj(legacy).id, 'false_123@c.us_OLD');
  const stringKey = message('false_123@c.us_STRING');
  assert.equal(WAPI._serializeMessageObj(stringKey).id, stringKey.id);
  const plainKey = message({ fromMe: false, remote: { _serialized: groupId }, id: 'PLAIN', participant: { _serialized: participant } });
  assert.equal(WAPI._serializeMessageObj(plainKey).id, `false_${groupId}_PLAIN_${participant}`);
  const brokenOptionalData = message(new CurrentMsgKey());
  brokenOptionalData.senderObj = { toJSON() { throw new Error('optional sender data unavailable'); } };
  assert.equal(WAPI._serializeMessageObj(brokenOptionalData).id, expectedId);
  assert.equal(WAPI._serializeMessageObj(brokenOptionalData).body, 'hello');
  const nativeWids = message(new CurrentMsgKey());
  nativeWids.from = { toString: () => groupId };
  nativeWids.author = { toString: () => participant };
  assert.equal(WAPI._serializeMessageObj(nativeWids).from, groupId);
  assert.equal(WAPI._serializeMessageObj(nativeWids).author, participant);
  const outgoing = message(new CurrentMsgKey(true));
  const notification = { ...incoming, isNotification: true };
  assert.equal(WAPI.processMessageObj(outgoing, false, false), undefined);
  assert.equal(WAPI.processMessageObj(notification, true, false), undefined);
  assert.equal(WAPI.processMessageObj(notification, false, true).id, expectedId);

  // No chat.loadEarlierMsgs exists: this is the exact failing #81 contract.
  messages.push(incoming, outgoing, notification);
  assert.equal((await WAPI.loadAndGetAllMessagesInChat(groupId, false, false)).length, 1);
  assert.equal(calls.at(-1).params.count, -1);
  assert.equal((await WAPI.loadAndGetAllMessagesInChat(groupId, true, false)).length, 2);
  assert.equal((await WAPI.loadAndGetAllMessagesInChat(groupId, false, true)).length, 2);
  assert.equal((await WAPI.loadAndGetAllMessagesInChat(groupId, true, true)).length, 3);
  const beforeLoaded = calls.length;
  assert.equal((await WAPI.getAllMessagesInChat(groupId, false, false)).length, 1);
  assert.equal(calls.length, beforeLoaded); // Loaded-only method stays loaded-only.
  await WAPI.loadEarlierMessages(groupId);
  assert.equal(calls.at(-1).params.id, expectedId);
  assert.equal(calls.at(-1).params.direction, 'before');
  await WAPI.getMessages(groupId, { count: 10, direction: 'after', id: expectedId });
  assert.equal(calls.at(-1).params.direction, 'after');

  // Run the actual listener registration supplied by Python.
  const listenerScript = JSON.parse(fs.readFileSync(0, 'utf8'));
  const received = [], any = [];
  sandbox.onMessage = msg => received.push(JSON.parse(JSON.stringify(msg)));
  sandbox.onAnyMessage = msg => any.push(JSON.parse(JSON.stringify(msg)));
  sandbox.onStateChange = () => {};
  sandbox.onNotificationMessage = () => {};
  const delivered = {};
  for (const name of ['onAck', 'onMessageEdit', 'onRevokedMessage', 'onReactionMessage',
      'onPollResponse', 'onUpdateLabel', 'onOrderStatusUpdate', 'onParticipantsChanged',
      'onNewChat', 'onBackendEvent']) {
    delivered[name] = [];
    sandbox[name] = (...args) => delivered[name].push(JSON.parse(JSON.stringify(args)));
  }
  vm.runInContext(`(${listenerScript})()`, sandbox);
  vm.runInContext(`(${listenerScript})()`, sandbox); // Reinjection must not duplicate callbacks.
  for (const msg of messages) {
    for (const cb of events['chat.new_message']) cb(msg);
  }
  assert.equal(received.length, 1);
  assert.equal(received[0].id, expectedId);
  assert.equal(any.length, 2);
  const emit = (name, ...args) => { for (const cb of events[name] || []) cb(...args); };
  emit('chat.msg_ack_change', { id: incoming.id, chat: { _serialized: groupId }, ack: 2 });
  emit('chat.msg_edited', { id: incoming.id, chat: { _serialized: groupId }, msg: incoming });
  emit('chat.msg_revoke', { id: incoming.id, refId: incoming.id, from: { _serialized: groupId } });
  emit('chat.new_reaction', { id: incoming.id, msgId: incoming.id, reactionText: 'x' });
  emit('chat.poll_response', { msgId: incoming.id, selectedOptions: [0] });
  emit('order.payment_status', { msgId: incoming.id, method: 'test' });
  emit('group.participant_changed', { groupId, author: participant, participants: [participant] });
  const newChat = { id: { _serialized: groupId }, isGroup: true, toJSON() { return { id: this.id }; } };
  emit('chat.new_chat', newChat);
  emit('chat.update_label', { chat: newChat, ids: ['1'], type: 'add' });
  emit('conn.backend_event', 'test_event', { value: 1 });
  for (const name of Object.keys(delivered)) assert.equal(delivered[name].length, 1, name);
  assert.equal(delivered.onAck[0][0].id, expectedId);
  assert.equal(delivered.onMessageEdit[0][0].msg.id, expectedId);
  assert.equal(delivered.onRevokedMessage[0][0].refId, expectedId);
  assert.equal(delivered.onReactionMessage[0][0].msgId, expectedId);
  assert.equal(delivered.onNewChat[0][0].id._serialized, groupId);
  assert.equal(delivered.onUpdateLabel[0][0].chat.id._serialized, groupId);
  assert.deepEqual(delivered.onBackendEvent[0], ['test_event', { value: 1 }]);
  messages.length = 0;
  assert.equal((await WAPI.loadAndGetAllMessagesInChat(groupId)).length, 0);
  sandbox.WPP.chat.getMessages = async () => ({ code: 'chat_not_found' });
  await assert.rejects(WAPI.getMessages(groupId), /Failed to fetch messages/);
  sandbox.WPP.chat.getMessages = async () => { throw new Error('network failure'); };
  await assert.rejects(WAPI.getMessages(groupId), /network failure/);
  console.log('Message IDs, listener delivery, history APIs, filters and error propagation passed.');
}
main().catch(error => { console.error(error.message, error.stack?.split('\n').slice(1, 4).join('\n')); process.exitCode = 1; });
