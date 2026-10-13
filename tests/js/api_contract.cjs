// Execute real Python bridge expressions against a strict recorded API surface.
const fs = require('node:fs');
const { exports: api, wapi } = require('../fixtures/upstream_contract.json');
const request = JSON.parse(fs.readFileSync(0, 'utf8'));
const calls = [];
const result = { id: 'message-id', ack: 1, body: 'edited', status: 200, sendMsgResult: true };
if (request.media) {
  // WA-JS can return a MsgKey whose serialized getter lives on its prototype.
  // Playwright only copies own enumerable properties across the boundary.
  result.id = Object.create({ get _serialized() { return request.message_id; } });
  global.File = require('node:buffer').File;
}
function callable(name) {
  return (...args) => {
    calls.push({ name, args });
    if (request.media && name === 'chat.find') return {id: request.arg.chatId};
    if (request.media && name === 'chat.generateMessageID') return {_serialized: request.message_id, fromMe: true};
    if (request.media && name === 'chat.sendFileMessage') {
      if (request.media_mode === 'hang') return new Promise(() => {});
      if (request.media_mode === 'unverified') return Promise.reject(new Error('Send failed'));
      return Promise.resolve(result);
    }
    return result;
  };
}
const WPP = {};
for (const [ns, names] of Object.entries(api)) {
  WPP[ns] = new Proxy({}, { get: (_, name) => {
    if (!names.includes(name)) throw new Error(`Unknown WA-JS API: ${ns}.${String(name)}`);
    return callable(`${ns}.${String(name)}`);
  }});
}
const WAPI = new Proxy({}, { get: (_, name) => {
  if (!wapi.includes(name)) throw new Error(`Unknown WAPI function: ${String(name)}`);
  return callable(`WAPI.${String(name)}`);
}});
if (request.media) WPP.whatsapp = {MsgStore: {get: () => request.media_mode === 'normal' ? undefined : ({
  id: {_serialized: request.message_id, fromMe: request.media_mode !== 'unverified'},
  type: request.arg.type, ack: 1,
})}};
(async () => {
  const expr = request.expr.replace(/;\s*$/, '');
  const window = { WPP, WAPI, __wppMedia: new Map([['media-test', []]]) };
  const fn = new Function('WPP', 'WAPI', 'window', `return (${expr});`)(WPP, WAPI, window);
  const value = await fn(request.arg);
  process.stdout.write(JSON.stringify({ value, calls }));
})().catch(error => { console.error(error.message); process.exitCode = 1; });
