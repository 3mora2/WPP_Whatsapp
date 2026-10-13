# Changelog

All notable changes to WPP_Whatsapp will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

- **0.5.8** - Build system migration to uv
- **0.5.7** - Latest stable release
- **0.5.x** - Various improvements and bug fixes

---

For more details, see the [GitHub Releases](https://github.com/3mora2/WPP_Whatsapp/releases).
