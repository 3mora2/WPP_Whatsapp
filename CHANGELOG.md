# Changelog

All notable changes to WPP_Whatsapp will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
