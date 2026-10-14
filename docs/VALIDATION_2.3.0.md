# 2.3.0 release candidate validation

Validated locally on Windows on 2026-10-14. Version 2.3.0 is prepared locally;
this report does not claim that it has been pushed, tagged or published to PyPI.

## Automated checks

| Environment / check | Result |
| --- | --- |
| Python 3.12.13, FastMCP 4.1.0, optional native Chrome, full suite | 357 passed |
| Python 3.9.23, core without FastMCP | 309 passed, 9 skipped |
| Python 3.10.20, MCP and reliability tests | 72 passed |
| HTTP template after final error-handler checks | Passed authentication, unconnected native client, duplicate and conflict checks |
| Ruff checks and formatting for core/MCP and all new Python files | Passed |
| Mypy on eight reliability/contract modules | Passed |
| Documentation links, runnable recipe signatures, generated API inventory | Passed |
| Development lock consistency | Passed; uv.lock tracks all extras |
| Wheel/sdist runtime payload comparison | Passed |
| Clean non-editable wheel installation and real MCP stdio | 23 tools, 18 read-only, 219 JS commands; lazy startup creates no profile |

The Python 3.9 skips comprise four optional integration modules and five opt-in
browser tests. Tests run against synthetic WhatsApp operations unless explicitly
described below. Existing legacy method/signature, JavaScript contract, package
and documentation tests remain part of the full suite.

Reliability coverage includes changed-recipient/body/media conflicts, equivalent
request spelling, non-destructive SQLite migration, concurrent reservations,
actual process termination after a durable claim, unknown recovery without replay,
persistent incoming cursors and retention gaps, per-session isolation, subscription
rebinding, recovery budget exhaustion, the legacy page-close ordering, admission
overflow/cancellation, media snapshot ownership, download cancellation and ACK
timeouts including a stalled lookup. See [core tests](../tests/test_reliability.py)
and [MCP tests](../tests/test_mcp_reliability.py).

## Synthetic endurance

`tools/soak_runtime.py --iterations 2000 --cycles 5` completed **10,000 operations**
and five SQLite close/reopen cycles with bounded 256-event retention, persistent
sequences and zero active/waiting operations at completion.

Recorded on this machine while other test suites ran: 106.62 seconds total;
last-sample p50 49.97 ms and p95 96.59 ms; Python traced peak allocation 741,422
bytes and allocation growth after warmup 121,192 bytes. Latency samples are bounded
to the last 1,024 operations. These figures include local disk/SQLite overhead and
are not a production throughput promise or proof of multi-hour browser stability.

## Real WhatsApp, no new outgoing messages

The [read-only live script](../tests/live_reliability_smoke.py) used the saved test
profile and WA-JS 4.6.1. It read six messages from an already-read group, verified
complete IDs and lookup, then closed its own page to exercise real recovery.
The session recovered on its first attempt, client-owned subscriptions rebound,
and history remained available afterward. Shutdown completed normally.

An existing, previously authorized document operation was inspected without
resending it. WhatsApp returned ACK=2: delivered=true, read=false. Waiting for
server ACK also succeeded without dispatch. This verifies receipt inspection and
observed delivery, not a new send or recipient reading.

No fresh incoming group message was arranged for this candidate. Full-ID callback
and journal behavior were tested synthetically; the earlier release's live #84
result is not represented as a new candidate callback test. A second authenticated
account remains unavailable, so multi-account/JWT tests use independent synthetic
clients and real authenticated HTTP middleware.

## Release boundary

The candidate wheel was installed outside the editable checkout, with isolated
Python imports. New Windows and synthetic endurance workflows were added and
their structure checked locally; remote GitHub Actions for this candidate have
not run yet. Publication still requires the normal PR/CI and published-release
workflow. See [changes](../CHANGELOG.md) and [migration](RELIABILITY.md).
