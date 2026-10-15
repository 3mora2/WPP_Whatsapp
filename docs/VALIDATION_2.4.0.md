# 2.4.0 candidate validation

Local validation on Windows, 2026-10-14. This candidate includes the compatibility
checkpoint for 2.3.1 followed by the durable recovery/operations improvements.
No 2.3.1 or 2.4.0 release has been published by this task. Remote GitHub Actions
have not run for this branch; the workflows are prepared for PR/release review.

## Automated checks

| Check | Result |
| --- | --- |
| Python 3.12.13, FastMCP 4.1.0, optional native Chrome, full suite | 388 passed |
| Python 3.9.23, core without FastMCP | 337 passed, 10 skipped |
| Python 3.10.20, core fault/recovery and MCP checks | 71 passed |
| Python 3.14.3, installed final wheel outside the checkout, fault/MCP/stub checks | 30 passed, 1 skipped (optional Mypy not installed) |
| Isolated installed-wheel checks, minimum core dependencies | Passed on Python 3.9.23 |
| Isolated installed-wheel checks, minimum MCP dependencies | Passed on Python 3.10.20 and 3.12.13 |
| Isolated installed-wheel checks, current resolved dependencies | Passed on Python 3.13.1 and 3.14.3 |
| Real FastMCP stdio discovery from the installed wheel | 29 tools, 23 in read-only mode; 220 JS commands |
| Installed-wheel persistence smoke | Pre-dispatch metadata and acknowledged event cursors survive reopen |
| Ruff checks/formatting, all core/MCP and new Python files | Passed |
| Mypy, all 35 core modules and generated service declarations | Passed |
| Public native/sync type tests | Accept valid receipt/read types; reject invalid arguments and unknown operations |
| Documentation links, recipes and generated service inventory | 30 Markdown files passed |
| Development lock, wheel/sdist package payload and stub packaging | Passed |

The Python 3.9 skips are optional integrations and opt-in browser checks. The
Python 3.12 run includes native Chrome tests. HTTP readiness allows the full
30-second startup window already used by its polling loop; an earlier 15-second
outer test deadline expired under load and was corrected without changing
application startup behavior. Most
automated WhatsApp calls are synthetic. Authenticated HTTP uses real signed JWTs
and middleware; all six new tools are checked against missing grants/scopes and
cross-account access. Synthetic tests do not certify every live upstream API.

Fault coverage includes actual process termination after committing an expected
key, mismatched outgoing evidence, post-dispatch conversion errors, immutable
media ownership during a key-preparation timeout, pre-dispatch disk failure,
late completion, cancellation-safe journal writes, journal shutdown while a
callback worker remains alive, cross-connection consumer claims, stale leases,
retry/dead-letter persistence, retention gaps inside pages, namespace isolation,
and tombstones preventing a send after compaction. Text dispatch also verifies
that phone-number aliases use the same canonical LID chat as the reserved key.

## Synthetic endurance

The event/admission probe completed **50,000 operations** over five SQLite reopen
cycles: 467.06 seconds, last-sample p50 40.51 ms, p95 76.13 ms, Python traced peak
820,911 bytes and growth after warmup 93,581 bytes. Admission ended idle.
These are measurements from this machine, including SQLite/disk overhead, not
WhatsApp throughput guarantees or evidence of indefinite leak-free operation.

The paired delivery/consumer probe completed **50,000 workflows** over five
reopen cycles in 3,144.14 seconds: 520 uncertain operations recovered, 2,075 event
retries, seven explicit duplicate-send checks passed, and the dead-letter store
remained bounded at 256 entries. Last-cycle p50 was 45.75 ms and p95 64.11 ms;
Python traced peak was 786,785 bytes with 442 bytes growth after warmup. It also
checked the 1,000-entry receipt cache, persisted keys, acknowledged cursors and
compaction tombstones. These synthetic measurements do not measure network or
WhatsApp throughput.

## Real WhatsApp

The two-real-account read-only endurance probe completed its requested **7,200
seconds** with 235 samples and nine manual reconnects of the first account. Both
clients closed successfully. The accounts were verified to be different without
logging their identifiers; the second remained ready during first-account
reconnects. No additional readiness outage was recorded and no messages were sent.

Fresh group callbacks and exact-ID lookups matched **1/1 on the first account**
and **73/73 on the second**, with zero callback errors. The first-account message
arrived after reconnection, confirming its restored listener (#84). The initial
strict-readiness probe had stopped after roughly five minutes on a readiness
drop; that interrupted attempt is not counted as an endurance success.

The endurance scope covers account isolation, connection recovery, incoming
callbacks and process measurements. It began before the last outbound-only
fixes; the separate fresh-process follow-up below exercises final outbound code.
It does not establish indefinite uptime or complete upstream API coverage.

Observed sample ranges: Python RSS 61.42–68.98 MiB; owned Chrome RSS 2049.84–2678.13 MiB; Python handles 561–935; tasks 7–8 (last sample 7). Browser RSS sums the two owned process trees. Reconnect/handle growth requires longer production observation; this finite run is not a leak-free guarantee.

The authorized follow-up sent **one text and one small text document**, exactly
one attempt each. Both hit the injected receipt-commit failure after dispatch.
After closing and reopening the ledger, recovery matched the precommitted key;
repeated recovery reused the receipt without sending again. Text received server
ACK 1; recipient delivery was not yet observed for it. The document received ACK
2 (delivered), and its downloaded bytes/SHA-256 matched the original. These ACKs
are separate from recovery success and do not establish that a person read them.

An already-read group returned ten history messages, and lookup by a returned
full ID matched (#81). The follow-up measured its owned browser processes and
verified **zero remaining after close**. Reports omit account, recipient and
message IDs and bodies; private journals remain excluded from Git.

## Artifact and upstream boundary

Final local distribution SHA-256 values:

| Artifact | SHA-256 |
| --- | --- |
| `wpp_whatsapp-2.4.0-py3-none-any.whl` | `d4f6ce042319c6b6c800afa6059ab8bb17580e5ca0905fbe12c05c0796d7af87` |
| `wpp_whatsapp-2.4.0.tar.gz` | `f48c1f451b73a93357895c83fba4c871418f07b8ddc9335f42312eec2e5844cf` |

The packaged Python/JavaScript/stub payload matches the selected source. The
latest stable upstream releases checked on this date remain
[WPPConnect 2.3.4](https://github.com/wppconnect-team/wppconnect/releases/tag/v2.3.4)
and [WA-JS 4.6.1](https://github.com/wppconnect-team/wa-js/releases/tag/v4.6.1).
Those bundles were already present; this task did not replace them with unreleased
upstream main-branch code. See [operations](OPERATIONS.md), [changes](../CHANGELOG.md)
and [tests](../tests/README.md).
