# Maintaining and extending the library

Use Python 3.9+ and Node.js for executable JavaScript contract tests. Install
development tools with `uv sync --extra dev` and run `uv run pytest tests/ -q`.
Native Chrome tests are opt-in with `RUN_WHATSAPP_BROWSER_TESTS=1`; they own and
close their profiles. Real-account tests are described in
[tests/README.md](../tests/README.md).

## Responsibility boundaries

| Module | Responsibility |
| --- | --- |
| `core/commands.py` | JavaScript command strings in a typed Python dictionary. |
| `core/bridge.py` | Session page binding, safe browser errors and command timing. |
| `core/contracts.py` | Structural transport and operation-context interfaces. |
| `core/service_registry.py` | Service definitions and allowed operations. |
| `core/services.py` | Async dispatch, tracked sends and cached sync adapters. |
| `core/delivery.py` | Reservation, no-replay policy and uncertain results. |
| `core/delivery_store.py` | Atomic memory and SQLite metadata storage adapters. |
| `core/delivery_models.py` | Shared immutable delivery receipts and states. |
| `core/events.py` | Supported event names, ordered dispatch and callback isolation. |
| `core/options.py` | Known-option validation preserving extension/browser options. |
| `core/engine.py` | Browser ownership, loop dispatch and resource cleanup. |
| `mcp/runtime.py` | Serialize MCP operations with session lifecycle changes. |
| `mcp/models.py` | Typed structured MCP results and delivery lookup schema. |
| `mcp/server.py` | Explicit tool schemas, redacted errors and delivery receipts. |
| `mcp/cli.py` | Application startup, stdio logging and authenticated HTTP settings. |

Keep these responsibilities separate. Browser errors must not include message
bodies, tokens or recipient details. Storage adapters receive metadata only.
Imports must not configure the application's root logger or create folders.
Applications can configure the `WPP_Whatsapp` logger through standard logging.

The optional MCP integration requires Python 3.10+ and FastMCP 4. Install with
`uv sync --extra dev --extra mcp`. Exercise schemas, lifecycle, receipts and real
stdio/HTTP transports with:

```bash
uv run pytest tests/test_mcp.py tests/test_mcp_optional.py -q
```

These tests use synthetic WhatsApp operations and send
no real messages. Keep FastMCP imports inside the optional integration; base
imports and Python 3.9 must continue to work without the extra.

## Add or update an operation

1. Verify the current upstream WPPConnect/WA-JS contract. Record its source/version
   in the contract fixture when changing the supported surface.
2. Put its JavaScript expression in `core/commands.py`. Pass data as arguments;
   do not interpolate message content into script source.
3. Implement its async operation in the appropriate API layer using
   `_evaluate_js(command_name, arguments, page=self.page)`.
4. Preserve the legacy synchronous wrapper, arguments and raw return type when
   applicable. Internal helpers should have private names.
5. Add an executable contract case for the real argument/return shape, with
   validation and failure cases for mutations.

`ServiceDefinition` discovers public async operations declared by its listed
layers. Extra facade methods must be named explicitly in `extra_operations`;
session startup, cleanup and injection helpers are excluded from message services.
Names use snake_case, including acronyms: `getWAJSVersion_` becomes
`get_wajs_version`. Bound wrappers are cached and retain inspectable signatures
and docstrings.

## Add a service or event

Add a `ServiceDefinition` in `service_definitions()` for a new service. The native
client, service hub and synchronous adapter use it without another name whitelist.
Test that the operation uses the session's owner loop and rejects calls before
readiness.

For an event, add its public name to `EVENT_NAMES`, its registration method to
`ListenerLayer`, and its JavaScript subscription to the listener command.
Test serialization, disposal, ordering and error isolation. Internal handlers
must not be exposed through `events.on()`. Preserve native group-participant
suffixes through the shared message-ID compatibility bridge.

## Delivery storage and cancellation

A storage adapter implements `DeliveryStore`: `get`, atomic `claim`, `save`, and
`close`. `claim` returns an existing receipt when an ID is already reserved;
it must not check and insert through separate unprotected operations.
Set `blocking=True` for blocking I/O adapters. Claims and state writes then run
off the browser loop. A tracker owns and closes its adapter. Its optional `store=`
argument allows adapter testing without coupling tracking logic to SQLite.

Opening another tracker must not overwrite an active owner's pending state.
Recovered pending records are presented as unknown by the new tracker until a
confirmed result is observed. A cancelled reservation before dispatch is failed;
cancellation after dispatch is uncertain and must never resend. Failure to persist
a completed send is also uncertain. Closing prevents new sends and leaves
unresolved operations unknown. Async owners use `aclose()` and `reconcile_async()`;
`get()` remains a synchronous inspection method.

Use bounded condition waits for background work in tests. Fixed short sleeps
are unreliable across Windows timer scheduling and slower CI runners.

## Quality checks

```text
uv run ruff check WPP_Whatsapp/core WPP_Whatsapp/mcp tools/verify_docs.py
uv run ruff format --check WPP_Whatsapp/core WPP_Whatsapp/mcp tools/verify_docs.py
uv run python tools/verify_docs.py
uv run pytest tests/ -q
uv build
python tools/verify_release.py dist
```

Ruff is pinned in development dependencies. CI enforces core/MCP checks and
formatting alongside package-wide syntax/undefined-name checks and static guide
validation. `tools/verify_docs.py` checks local links/headings, compiles Python
recipes/examples, binds known API signatures and compares the generated service
inventory. It never executes snippets or opens WhatsApp. Regenerate the inventory
with `python tools/verify_docs.py --write-api` after service changes.
Legacy public method names remain unchanged. Enable Chrome tests for changes
to ownership, concurrency or callbacks. The
[architecture guide](ARCHITECTURE.md) describes runtime behavior and release recovery.

## Upstream review

Run `python tools/check_upstream.py --output archive/upstream-report.json` to
compare the recorded immutable WPPConnect/WA-JS sources against their current
default-branch commits. The audit pins commits, downloads bounded archives,
reads TypeScript without executing/extracting it, records SHA-256 provenance
and reports public export/method/parameter differences. Potential removals or
signature changes return exit code 2. Network/parser failures fail the run.

The [upstream workflow](../.github/workflows/upstream-review.yml) runs weekly
and manually, uploads its report and leaves bundled code/contracts unchanged.
Manual `propose_update=true` opens a draft PR containing the report for review;
GitHub must permit Actions to create PRs. Nothing is automatically merged or
released. Signature review, contract tests, browser capabilities and opt-in
authenticated tests are still required before adopting changes. Static names
alone do not establish compatibility. Public re-exports exclude internal helpers.

Common typed views live in `core/models.py`; keep unknown fields available as
copied raw data. Media transfers belong in `core/media.py`, with byte limits,
cleanup and explicit uncertainty. Use `sync_wrapper` only for unchanged argument
forwarding; keep custom normalization in its existing method. Every new MCP tool
must select its runtime through `mcp/accounts.py` with the appropriate scope
before accessing account data or dispatching work.
