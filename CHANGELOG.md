# Changelog

All notable changes to WPP_Whatsapp will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## 2.3.1 (candidate)

- Add isolated installed-wheel checks, minimum dependency constraints and modern
  Python compatibility jobs on Linux and Windows.
- Add an opt-in two-real-account endurance probe with owned-browser memory,
  handle/task measurements, recovery cycles and incoming callback ID lookup.

## [2.3.0] - 2026-10-14

- Bind tracked send IDs to canonical request digests; reject changed payloads,
  recipients and media bytes. Add a non-destructive SQLite schema migration.
- Add opt-in durable incoming MCP events with persistent cursors, retained-ID
  deduplication, count/age retention, explicit gaps and per-session namespaces.
- Add bounded opt-in native recovery and client-owned subscriptions that rebind
  after replacement contexts, without replaying sends.
- Observe delivery/read/play ACK evidence separately from queued send confirmation;
  add typed Python helpers and two read-only MCP tools (23 tools, 18 read-only).
- Bound composed operations and MCP admission, reuse the existing optional send
  rate limiter, and keep metadata responsive during slow work.
- Add type checks, Windows CI, process-crash/concurrency tests, synthetic endurance
  measurement, and authenticated FastAPI / durable FastMCP application templates.

See [migration, settings and limitations](docs/RELIABILITY.md). Publication remains
driven by a published GitHub release after the CI checks pass.
Local candidate results are recorded in the [validation report](docs/VALIDATION_2.3.0.md).

## [2.2.0] - 2026-10-13

### Added
- Optional immutable `Message`, `Chat`, `Group` and `GroupMember` views through
  native `client.typed` and composed sync/async services; legacy raw results remain.
- Sanitized diagnostics with lifecycle, startup categories and safe counters.
- Bounded media preparation and File/Blob transfers in 256 KiB chunks, progress,
  byte limits, cleanup, exclusive downloads and tracked sends with late confirmation.
- Nine additional MCP tools (21 total, 16 read-only): account discovery,
  diagnostics, bounded search, incoming events/cursors, media download,
  file/image sending and replies.
- Independent MCP profiles, locks, ledgers and buffers, verified JWT identity,
  scopes and account grants; authenticated HTTP and private media roots in the CLI.
- Weekly read-only upstream source audit with reports and optional manually
  requested draft review proposals. Bundles/contracts are never auto-replaced.

### Changed
- Centralized 157 reviewed legacy sync wrappers while preserving declarations,
  defaults, docs and original positional forwarding behavior.
- Expanded JWT/isolation, overflow, media cleanup/browser and upstream tests;
  refreshed guides, type metadata and generated API inventory.
- Legacy HTTP media conversion now uses bounded staging and safe logging while
  preserving its data-URI/False result contract.
- Serialize WA-JS media result message keys before crossing the browser bridge,
  preserving their full ID and avoiding false unknown receipts after a successful send.
- Confirm media using its preassigned full ID and verified outgoing local model
  when upstream registration/ack waiting stalls, without replaying the send.

## [2.1.0] - 2026-10-13

### Added
- Optional FastMCP 4 integration (`mcp` extra, Python 3.10+) with a reusable server
  factory, `wpp-whatsapp-mcp` command and `python -m WPP_Whatsapp.mcp` entry point.
- Twelve typed MCP tools for explicit session control, paginated chat/history
  reads, complete message-ID lookup, contacts, group members and tracked text sends.
  Required operation IDs prevent replay; uncertain receipts can be inspected and
  reconciled without resending. Delivery metadata uses SQLite by default.
- Lazy browser startup, caller/server ownership, serialized session operations,
  read-only tool selection, redacted errors, stdio and loopback HTTP transports,
  usage documentation and real MCP protocol/transport regression tests in CI.

### Documentation
- Refresh English/Spanish/package guides, API recipes, setup, configuration,
  troubleshooting, test guidance and example indexes against actual interfaces.
- Add installation, configuration, usage-practice, performance and FAQ guides;
  repair relative links and remove stale coverage/production-validation claims.
- Generate the complete composed-service signature inventory and validate local
  links/headings, Python recipes and known API call signatures in CI.
- Correct example lifecycle/callback usage and explicit media inputs; remove
  automatic sample sends from basic examples. Bulk sending now requires explicit
  arguments and durable operation IDs and stops on uncertain delivery.

## [2.0.0] - 2026-10-13

### Maintainability
- Separate explicit service definitions, structural interfaces, delivery models
  and memory/SQLite adapters. Cache bound operations and sync adapters while
  preserving inspectable signatures and excluding internal session helpers.
- Validate known session options before browser startup, preserving extension
  settings. Centralize supported event names and reject internal event handlers.
- Preserve the active owner's pending delivery state when opening another
  tracker. Offload blocking claims/state writes, handle persistence failure as
  uncertain, and prohibit sends after tracker shutdown.
- Share concurrent startup of the same multi-session profile. Support partial
  and callable callbacks, including async callable interval handlers.
- Remove dead interval code and redundant directory handling. Library imports
  no longer configure root logging or create the temporary token directory.
- Add pinned Ruff checks/formatting for the core in CI and a development guide
  for future services, commands, events and persistence adapters.

### Added
- Native `AsyncClient` on the caller's event loop, with composed message, chat,
  group, catalog, community, newsletter, profile, label, list, status and event services.
- Central JavaScript command registry in a typed Python module and page-bound bridge with safe errors,
  capability checks and aggregate timing/failure metrics.
- Explicit session lifecycle, monotonic deadlines, exclusive profile leases,
  idempotent owned-resource cleanup and native reconnect without operation replay.
- Bounded, ordered event dispatch supporting sync/async callbacks, failure
  isolation, recent message-ID deduplication and explicit overflow statistics.
- Delivery receipts and optional per-session SQLite metadata storage for service
  sends. Reserved operation IDs cannot be replayed; uncertain sends can be
  confirmed later or reconciled against a verified outgoing message.
- Verified WA-JS asset caching after live latest-release discovery, and one
  initialization fallback for incompatible latest runtimes. Mutable nightly
  and custom URLs bypass the cache; explicit runtime selections remain strict.
- Manual published-tag release recovery, immutable source selection, complete
  wheel/sdist payload checks and post-upload PyPI verification.
- Fault-path regressions, native Chrome checks, migration documentation and a
  read-only real-account smoke test for the native async client.

### Fixed
- Interpret `deviceSyncTimeout` in milliseconds and measure auto-close using
  actual elapsed time. Return sessions to ready after successful login/sync.
- Construct clients and bind browser callbacks on the owning browser loop.
  Closing one multi-session client no longer closes other session contexts.
- Shut down listeners, timers, storage, contexts, profile leases and the owned
  driver on startup failure and repeated close calls.
- Preserve the browser's `wait_for_first_selectors` helper with concurrent waits,
  bounded timeout accounting and cleanup of outstanding selector tasks.
- Preserve legacy method signatures and raw return values through a flat
  compatibility facade. Remove the PlaywrightSafeThread dependency; stealth
  support is available through the optional `stealth` extra.

### Compatibility
- Automatic profile takeover (`close_already_profile=True`) is rejected; close
  that profile's owner explicitly. Service sends return `DeliveryReceipt` while
  existing flat send methods keep their return types. See the migration guide.

## [1.1.0] - 2026-10-13

### Upstream API audit (2026-10-13)
- Compared all API layers with WPPConnect `05b24636fc5dd5cfc1246aff64ef7db94c3cf3a1`
  and WA-JS `7c0fbd759b6b6de995af515995ad84f66606fde9`. The latest npm releases
  remain WPPConnect 2.3.4 and WA-JS 4.6.1.
- Added ListsLayer, IndexedDB row-ID retrieval, auto-download settings, missing
  catalog controls, participant promotion/demotion, recording/played/reaction
  methods, base64 sending helpers, business-profile retrieval, link-code
  refresh and upstream compatibility aliases.
- Fixed invalid JavaScript/TypeScript fragments, argument shapes and discarded
  results in retrieval, profile, labels, community, newsletter and sender APIs.
- Migrated catalog calls to `WPP.catalog`, community participant methods to
  their plural names, newsletter editing to `edit`, and poll/order sending to
  the current chat APIs. Preserved legacy order, mention and profile option
  names through normalization without mutating caller dictionaries.
- Restored all listener registrations, added missing upstream events, isolated
  event emitters per session, and implemented optional event ID filters.
- Dispatch synchronous user callbacks off the browser loop so they can safely
  call client methods. Serialize chat models for new-chat and label events.
- Fixed cross-loop browser awaits, interval cancellation, disabled auto-close,
  factory context managers, reconnection callbacks and multi-session startup
  and cleanup without requiring an initial browser page.
- Fixed PTT content/reply IDs, data-URI image inputs, animated sticker conversion,
  MIME parameters, FFmpeg executable discovery and blocking GIF conversion.
- Fixed batch operations to use async client methods, validate input before
  sending, preserve input order and honor an explicitly empty group selection.
- Initialize rate-limiter locks on their owning running loop, validate limits,
  and use a monotonic clock. Clean up FFmpeg temporary files deterministically.
- Added recorded upstream API contracts, executable JavaScript argument tests
  and regressions for lifecycle, session isolation, concurrency and media.
- Fixed package classifiers placement in project metadata.

### Fixed
- Preserve complete message IDs, including group participants, when WhatsApp
  exposes the key through `toString()` instead of `_serialized` (#84).
- Use the current WA-JS history API for `loadAndGetAllMessagesInChat` and
  `loadEarlierMessages`, preserving sender and notification filters (#81).
- Keep valid phone IDs when no LID mapping exists; resolve LIDs before opening
  chats and retrieving messages, with matching sync and async behavior (#81).
- Treat bare 14-digit numbers as phone numbers; explicit LIDs use `@lid`.

### Updated
- Bundle WPPConnect 2.3.4 and WA-JS 4.6.1 from verified official npm releases.
  Startup tries the latest stable WA-JS release first, then uses the bundled
  runtime if discovery or download fails within a 30-second total timeout.
  `wa_js_version="bundled"` skips the network entirely. Explicit versions,
  local files, URLs, and `wa_js_version="nightly"` remain supported and report
  failures rather than silently switching versions.
- Search additional release pages for older explicit WA-JS versions, ignore
  releases without JavaScript assets, and reject empty or HTML/JSON downloads.
- Load WAPI from one packaged JavaScript source and wait for initialization
  before registering listeners.

### Changed
- Migration to `uv` build system
- Updated GitHub Actions workflow to use `uv`
- Removed `setup.py` in favor of `pyproject.toml`
- Removed `requirements.txt` (dependencies managed in `pyproject.toml`)

### Added
- Build test script (`test/test_build.py`)
- Enhanced package metadata (author, license, URLs, classifiers)

## [0.5.8] - 2026-03-27

### Changed
- Updated build configuration to use `pyproject.toml`
- Improved package structure for PyPI distribution

## [0.5.7] - 2024

### Added
- WhatsApp Web API integration
- Multi-session support
- Message sending (text, image, video, audio, documents)
- Message receiving and listening
- Group management
- Contact management
- Sticker support (static and GIF)
- QR Code authentication
- Auto QR refresh
- Call events handling
- Business features (catalog, orders)

### Features
- Send text, image, video, audio and docs
- Get contacts, chats, groups, group members, Block List
- Send contacts
- Send stickers
- Send stickers GIF
- Multiple Sessions
- Forward Messages
- Receive message
- Send location
- Auto QR refresh

---

## Version History

Use the release sections above and GitHub Releases for current versions.
The 0.5.x sections describe historical changes.

---

For more details, see the [GitHub Releases](https://github.com/3mora2/WPP_Whatsapp/releases).
