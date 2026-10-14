# Configuration

The [2.3.0 reliability guide](RELIABILITY.md) documents incoming event persistence,
bounded recovery, operation admission and optional send pacing. All settings are
validated before browser startup; persistence and automatic recovery are opt-in.

## Factories and profile paths

```python
from WPP_Whatsapp import Create, AsyncClient

creator = Create("mybot", folderNameToken="tokens", autoClose=0)
native = AsyncClient("mybot", token_directory="tokens", autoClose=0)
```

`Create` uses `folderNameToken`; `AsyncClient` uses `token_directory`.
Both accept `user_data_dir` for an explicit profile directory. `Create` creates
its directory during construction; `AsyncClient` creates it when connecting.
Session names are single directory names, not paths. Profiles include login
state and must be kept private. One running owner can hold a profile at a time.

## Timeouts and readiness

| Option | Unit | Default/meaning |
| --- | --- | --- |
| `autoClose` | seconds | `Create`/MCP use 0; QR login auto-close disabled. Native default follows the underlying client (60 seconds); set 0 explicitly for manual login. |
| `deviceSyncTimeout` | milliseconds | 180000; 0 disables the sync deadline. |
| `navigationTimeout` | milliseconds | 60000; browser navigation. |
| `runtimeReadyTimeout` | milliseconds | 30000; runtime initialization. |
| `pageLoadTimeout` | seconds | 120; startup readiness. |
| `operationTimeout` | seconds | 60; tracked service sends, 0 disables it. |
| flat method `timeout` | seconds | Per-method sync wait, commonly 60 or 120; inspect its signature. |

Do not use browser flags such as `--timeout=...` to configure these values.
Native `wait_for_login=False` returns before login is ready; wait for `state`
to become `SessionState.READY` before invoking services. Legacy factory spelling
is `waitForLogin`. MCP manages this setting and exposes `whatsapp_status`.

## Browser and callbacks

`headless=False` is the default. `Create` defaults to installed Chrome. To use
Playwright Chromium, pass `browser="chromium", channel=None`; for `AsyncClient`,
pass `channel=None`. Browser launch options use their Playwright names, e.g.
`args=[...]`, `proxy={"server": "http://proxy:port"}` and `executable_path=...`.
Legacy names such as `browser_args`, `tokens_folder` and `whatsapp_web_version`
are not documented configuration keys.

`Create` accepts callable `catchQR`, `statusFind`, `onStateChange` and
`onLoadingScreen` hooks. `logQR=True` opts into terminal QR logging; the visible
browser is sufficient for ordinary login. Never publish QR data or login codes.

## Runtime and storage

| Setting | Meaning |
| --- | --- |
| `wa_js_version=None` | Latest stable discovery, verified cache and bundled fallback. |
| `wa_js_version="bundled"` | Skip WA-JS discovery/download, not WhatsApp network access. |
| `wa_js_version="nightly"` | Explicit mutable upstream runtime; not cached. |
| explicit constraint/URL/file | Strict selection; failure does not silently switch versions. |
| `runtimeCacheDir` | Optional verified runtime cache location. |
| `deliveryStore` | Optional SQLite metadata path; native/legacy service ledger otherwise in memory. |
| `eventQueueSize` | Positive integer, default 256; overflow is observable rather than silent overwrite. |

MCP-owned clients default to a SQLite ledger under
`<token-directory>/.deliveries/mcp.sqlite3`, partitioned by session. Injected
clients retain their own options. [FastMCP](FASTMCP.md) documents CLI flags,
HTTP authentication, account isolation and private media roots.

Known numeric/path options are validated before browser startup. Other
extension/Playwright options are preserved, but preserving a key does not mean
the browser supports it. `close_already_profile=True` is rejected.
