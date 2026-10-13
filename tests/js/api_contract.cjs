// Execute real Python bridge expressions against a strict recorded API surface.
const fs = require('node:fs');
const { exports: api, wapi } = require('../fixtures/upstream_contract.json');
const request = JSON.parse(fs.readFileSync(0, 'utf8'));
const calls = [];
const result = { id: 'message-id', ack: 1, body: 'edited', status: 200, sendMsgResult: true };
function callable(name) {
  return (...args) => {
    calls.push({ name, args });
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
(async () => {
  const expr = request.expr.replace(/;\s*$/, '');
  const fn = new Function('WPP', 'WAPI', 'window', `return (${expr});`)(WPP, WAPI, { WPP, WAPI });
  const value = await fn(request.arg);
  process.stdout.write(JSON.stringify({ value, calls }));
})().catch(error => { console.error(error.message); process.exitCode = 1; });
