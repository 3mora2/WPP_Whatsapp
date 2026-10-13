# Troubleshooting

## Interpreter or dependency errors

Use the same interpreter for installation and execution:

```bash
python --version
python -m pip show WPP_Whatsapp
python -m pip install --upgrade WPP_Whatsapp
```

The core requires Python 3.9+; FastMCP requires Python 3.10+ and the `mcp` extra.
An MCP import/start error can be resolved with
`python -m pip install --upgrade "WPP_Whatsapp[mcp]"` on a supported interpreter.
Use `python -m WPP_Whatsapp.mcp --help` if the console command is not on PATH.

## Factory versus client

`creator = Create("mybot")` is not the operation client. Use
`client = creator.start()` or `with Create("mybot") as client`. Register flat
callbacks through `client.onMessage` (also available as `client.on_message`). The native
equivalent is `client.events.on_message`. Use async methods inside async callbacks;
the error "Use the async API on the browser event loop" identifies a sync call
on the owner loop. Do not run that loop again with `run_forever()`.

## Browser or QR problems

Check Chrome installation and start with `headless=False`. For Playwright
Chromium, follow [installation](INSTALLATION.md#browser). Scan the QR in the
browser; terminal output is opt-in through `logQR=True` on `Create`.
Check access to WhatsApp Web, the phone's linked-device flow and writable profile
storage. Increasing a specific [timeout](CONFIGURATION.md#timeouts-and-readiness)
can help slow startup; it cannot repair a missing browser or unavailable network.

`wa_js_version="bundled"` isolates runtime discovery/download problems. It does
not make WhatsApp Web work offline. Explicit custom runtimes fail rather than
quietly selecting a different one. See [runtime provenance](../WPP_Whatsapp/js_lib/UPSTREAM.md).

## Profile ownership and login state

`ProfileInUseError` means another owner holds the profile. Close that owner or
choose a distinct session name; do not kill an unrelated browser to take it over.
`close_already_profile=True` is intentionally unsupported. Use an absolute
`folderNameToken`/`token_directory` when different working directories otherwise
create different profiles. Saved profiles are directories, not `.token` files.

An unpaired session needs the phone login flow again. Reconnect explicitly with
`await native.reconnect()` or the MCP reconnect tool; it never replays sends.
Do not delete a delivery ledger to resolve uncertain sends. For a suspected
damaged profile, first close its owner and back up the profile; use a new session
directory for diagnosis instead of deleting saved state.

## History and message IDs (#81 and #84)

Use `getMessages(chat_id, {"count": 50})` for a page.
`getAllMessagesInChat` only sees loaded history; `loadAndGetAllMessagesInChat`
requests what the linked device can retrieve. Preserve the complete string ID,
including group participant suffixes, for `getMessageById` and replies.
Use explicit `@lid` for LIDs; bare numbers remain phone numbers.

## Sending and media

Check the actual [signature](API_METHODS.md), account access and chat ID.
For `sendImage`, use the `caption=` keyword; its third positional argument is
filename. For `sendFile`, distinguish filename/options from caption. Media
availability and limits vary by WhatsApp/runtime, so avoid assuming universal
fixed size limits. Check input paths, MIME/data URI format and FFmpeg availability
when using conversion features.

`DeliveryUncertainError` means the send may have happened. Inspect its operation
ID/receipt or reconcile against a verified outgoing message; do not retry under
a new ID. An MCP send returns structured `state="unknown"` for uncertainty.
`confirmed` establishes a message ID, not recipient delivery/read.

## MCP connection problems

Stdio clients must launch the configured interpreter and module/command; a
bare running stdio process is not an HTTP endpoint. HTTP clients use
`http://127.0.0.1:8765/mcp` when started with `--transport http --port 8765`.
The CLI defaults to loopback; other hosts require verified JWT configuration
and an access policy. `whatsapp_status` starts at `new` until
`whatsapp_connect` opens the browser. Finish login and poll readiness.
`--read-only` deliberately omits sending and reconciliation tools.

For HTTP deployment, configure independent accounts and verified principal/scope
permissions as described in [FastMCP](FASTMCP.md). Each account is shared only
among its authorized principals. Unknown accounts and missing permissions
return the same error; verify both policy grants and token scopes.
The underlying browser profile must not be opened by multiple workers.

## Diagnostics for an issue

Use `client.diagnostics()` or the permitted `whatsapp_diagnostics` tool for a
sanitized support snapshot. See [report fields](TYPED_MEDIA.md#diagnostics).

```python
import platform
from importlib.metadata import version

print("Package:", version("WPP_Whatsapp"))
print("Python:", platform.python_version())
print("OS:", platform.system())
```

The package does not expose `__version__`; use distribution metadata above.
Configure logging in your application, preferably on stderr for MCP. Include
the selected runtime, session state, minimal code and sanitized exception type
when reporting an issue. Omit QR codes, credentials, profiles, message bodies and
private recipient IDs from public reports.
