# Tests and validation boundaries

Run from the repository root. The core supports Python 3.9+; optional MCP tests
need Python 3.10+ and the `mcp` extra. Node.js 18+ is required for executable
JavaScript contract tests. Native Chrome tests are opt-in and need installed Chrome.

## Commands

```bash
uv sync --extra dev --extra mcp --python 3.12
uv run pytest tests/ -q
uv run pytest tests/test_mcp.py tests/test_mcp_development.py tests/test_mcp_optional.py -q
uv run pytest tests/ --cov=WPP_Whatsapp --cov-report=term-missing
uv run python tools/verify_docs.py
```

On Python 3.9, omit `--extra mcp`; the MCP protocol module is skipped and base
compatibility tests still run. In PowerShell, enable native browser checks with
`$env:RUN_WHATSAPP_BROWSER_TESTS='1'`; in POSIX shells use
`RUN_WHATSAPP_BROWSER_TESTS=1 uv run pytest tests/ -q`. CI intentionally skips
these real-browser checks and runs synthetic tests on Python 3.9–3.12 plus
separate MCP jobs on Python 3.10 and 3.12.

## Coverage areas

| Area | Main files |
| --- | --- |
| Wrappers and JavaScript arguments | [test_api_contracts.py](test_api_contracts.py), [test_all_features.py](test_all_features.py) |
| History/full IDs and runtime fallback | [test_message_regressions.py](test_message_regressions.py), [test_wajs_updates.py](test_wajs_updates.py) |
| Lifecycle/events/delivery/ownership | [test_core.py](test_core.py), [test_core_faults.py](test_core_faults.py), [test_maintenance.py](test_maintenance.py) |
| Runtime/concurrency/media | [test_runtime_regressions.py](test_runtime_regressions.py) |
| Optional MCP tools and real transports | [test_mcp.py](test_mcp.py), [test_mcp_optional.py](test_mcp_optional.py) |
| Typed models and chunked browser media | [test_development.py](test_development.py) |
| JWT account isolation, scopes and buffers | [test_mcp_development.py](test_mcp_development.py) |
| Offline upstream audit contracts | [test_upstream_review.py](test_upstream_review.py) |
| Release provenance/payload verification | [test_release.py](test_release.py) |

Most WhatsApp operations are synthetic. MCP tests use real in-process, stdio
subprocess and HTTP subprocess transports with synthetic WhatsApp operations.
They verify schema validation, ownership, pagination/full IDs, SQLite restart,
duplicate suppression, uncertain sends, reconciliation and late confirmation.
They do not establish live-account outbound behavior or every upstream API.

The development suite passed 322 tests on Windows/Python 3.12.13 with FastMCP
4.1.0 and opt-in Chrome checks on 2026-10-13. Browser File/Blob tests verified
exact bytes over multiple chunks and cleanup. HTTP JWT tests reject invalid
signatures, cross-account access and missing scopes. They verify independent
locks, ledgers and buffers with synthetic WhatsApp operations.
The final base-only Python 3.9.23 run passed 286 tests with two optional MCP
modules skipped; the Python 3.10.20 MCP suite passed 38 tests.

For an identified previous result, [PR #87 run #88](https://github.com/3mora2/WPP_Whatsapp/actions/runs/38390409311)
passed base tests on Python 3.9–3.12, MCP tests on 3.10/3.12, lint and package
builds. Local validation on 2026-10-13 passed 280 tests on Windows/Python 3.12.13
with FastMCP 4.1.0 and Chrome enabled; the MCP subset passed 23 tests on Python
3.10.20, and the base-only Python 3.9.23 run passed 259 tests with one module skip.
Those are dated snapshots, not a promise of a permanent test count or coverage percentage.

## Real-account reads and callbacks

Run `python tests/live_whatsapp_smoke.py` and log in in its separate browser.
It checks issue #81 history retrieval and waits for a fresh incoming group
message to check #84 callback-ID lookup. `--chat GROUP_ID` selects a group.
It sends no messages. Its ignored report stores counts/checks and hashed IDs
without message bodies; the browser remains open until you close it.

`python tests/live_async_smoke.py` separately exercises native async history,
ID lookup, reconnect/profile reuse and repeated close. These are opt-in scripts,
not automated CI tests. They do not authorize sending messages.

`python tests/live_mcp_smoke.py` checks MCP against the saved test profile
without sending by default. `--recipient` requires an explicitly authorized
destination and sends one fixed text with a durable operation ID; reruns with
the same ID reuse the saved result. `--wait-events SECONDS` waits for a fresh
group message. Its ignored report contains counts/booleans, not IDs or bodies.

On 2026-10-13, the MCP check discovered 21 tools, read 25 messages from an
already-read group, matched full-ID and typed lookup, scanned 25 messages and
produced a sanitized diagnostic on WA-JS 4.6.1. One authorized text send returned
a confirmed ID; lookup verified the outgoing message. A duplicate call with the
same operation ID returned the identical saved receipt. This confirms the
sender's result, not recipient delivery/read. Two distinct authenticated
WhatsApp accounts were not exercised because a second account was unavailable.
The fresh group message check also passed: the new MCP event buffer received
an incoming group message and lookup by its complete callback ID matched.
This rechecks #84 alongside the already-read group history flow for #81.

`python tests/live_mcp_media.py --recipient AUTHORIZED_ID` performs explicit
opt-in sends of one synthetic image and one small document with stable operation
IDs, then verifies outgoing lookup, downloads and deduplication. It requires
separate authorization for those sends. `--document-only` limits the test to
the document. On 2026-10-13 both original sends were verified in WhatsApp,
downloaded, and reconciled after upstream waiting did not return their result.
The image decoded correctly; the document matched the original bytes exactly.
No original media operation was replayed. A regression test now covers a stalled
upstream promise, exact-key/type/outgoing verification and rejected false confirmation.

On 2026-10-13, read/callback checks on WhatsApp Web 2.3000.1050169898 / WA-JS 4.6.1
returned 50, 51, 53 and 234 messages through the four legacy history getters;
all IDs were complete. A newly received group message reached the Python
callback and lookup by that ID matched. Native async checks read 25 messages,
matched lookup, reconnected and read five more, with zero sends. These results
cover those flows on that account/build, not all methods or future web builds.

## Release verification

The workflow validates an immutable tagged source, tests, builds wheel/sdist,
uploads only for a published release/recovery event and verifies PyPI afterward.
For local read-only checks use `python tools/verify_release.py dist` or `pypi`.
Compare against the exact selected source: Windows CRLF checkout bytes can differ
from Linux CI LF bytes. The release's CI artifacts and PyPI SHA-256 digests are
the authority for matching uploaded files. Never replace payload checks with a
version-only check. See [release recovery](../docs/ARCHITECTURE.md#releases-and-recovery).
