# Bundled JavaScript

Updated on 2026-10-13 from the official npm releases:

| File | Package | Version | License |
| --- | --- | --- | --- |
| `wapi.js` | `@wppconnect-team/wppconnect` | 2.3.4 | LGPL-3.0-or-later |
| `wppconnect-wa.js` | `@wppconnect/wa-js` | 4.6.1 | Apache-2.0 |

Sources: <https://github.com/wppconnect-team/wppconnect/tree/v2.3.4> and
<https://github.com/wppconnect-team/wa-js/tree/v4.6.1>.
License texts are included alongside these files.

The Python API audit also used these immutable upstream snapshots:

- WPPConnect: `05b24636fc5dd5cfc1246aff64ef7db94c3cf3a1` (2026-10-12).
- WA-JS: `7c0fbd759b6b6de995af515995ad84f66606fde9` (2026-10-13).

`tests/fixtures/upstream_contract.json` records their exported functions and
public WPPConnect method names. Tests validate Python API coverage, compile
all inline browser expressions, and execute argument/return contracts against
this recorded surface. An isolated Chrome check confirmed that all 130 WA-JS
functions referenced by the Python implementation are present in the bundled
4.6.1 runtime. These checks do not validate authenticated WhatsApp operations.

Both bundles are copied unchanged from their npm tarballs. Each tarball's
SHA-512 was checked against the registry `dist.integrity` before extraction:

- WPPConnect: `sha512-nG/g9APdqLT8PogvEuxfob3KVRPF3IFjHUl3QnXQ5UTmiNyRUkKuxqoKgjlY1KTsIUHMV/isFjy121Ud4z4p5w==`
- WA-JS: `sha512-vabRop+7EN2Ny0f6suB5jY9Gmrkclo2yvaaw4zinEH5UUNUiyb7cTnSuK0rknYUde4ElKSjpThJFV0J+220chA==`

`message_compat.js` is the local compatibility bridge for issues #81 and #84.
It preserves full native message keys (including group participant suffixes),
serializes existing message models without constructing replacements, and
routes legacy history methods through `WPP.chat.getMessages` rather than the
removed `chat.loadEarlierMsgs` method. `getAllMessagesInChat` still reads only
messages already loaded in memory. All-history retrieval uses `count: -1` and
returns the history available to the current linked device.

`api/helpers/wapi.py` loads the official WAPI bundle followed by this bridge.
By default, WA-JS first checks GitHub's latest stable release and downloads the
`wppconnect-wa.js` asset. If discovery or download fails (including a timeout,
rate limit, missing asset, or invalid response), it loads the bundled version.
The full attempt is limited to 30 seconds and requests have a 5-second connect
timeout. A warning identifies when the bundled fallback is used.

Stable release discovery happens before the verified asset cache is consulted.
Cached bytes are checked with SHA-256 metadata and refetched on corruption.
If an automatically selected latest runtime cannot initialize required
capabilities, startup reloads once and tries the bundled runtime. Mutable nightly
and custom URLs bypass the stable cache. See [architecture](../../docs/ARCHITECTURE.md).

Use `wa_js_version="bundled"` to skip WA-JS discovery/download; WhatsApp Web
still requires a network connection. Users can also
select `wa_js_version="nightly"`, a version constraint, a URL, or a local
JavaScript file. Explicit selections surface errors instead of silently
loading another runtime. Version constraints search up to ten pages of 100
releases to find a matching JavaScript asset, within the same total timeout.
