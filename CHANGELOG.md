# Changelog

All notable changes to this project will be documented in this file.

The format is loosely based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and versions follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.1] - 2026-11-09

### Fixed
- Concurrent chats no longer crash the server with a segmentation fault:
  requests now queue and are processed one at a time (the llama.cpp
  instance is not thread-safe).
- Mobile layout: no more scrollable blank space under the composer caused
  by the 100vh vs 100dvh mismatch.
- UI is scaled down and better spaced on phones (root font 14px), with
  2 suggestion chips instead of 3.

## [1.1.0] - 2026-11-04

### Changed
- Replaced arbitrary Tailwind values (`border-[2px]`, `h-[5.5rem]`) with
  theme tokens (`border-2`, `h-22`).
- `playSegments` now calls the TTS endpoint with `lang="en"` explicitly.
- App version is displayed in the sidebar under Recientes, fetched from
  `/api/version`.

### Removed
- Dead per-segment language detection (`detectSegmentLanguage`) and the
  `language` field from speech segments.

### Fixed
- `hasEnglishSpeech` always returned `true` for any non-empty message because
  `buildSpeechSegments` forced `language: "en"`.
- TTS warmup failures are now logged to stderr instead of swallowed silently.
- Restarting speech now always stops any ongoing playback before starting from
  the beginning, without voice overlap.

## [1.0.0] - 2026-11-03

### Added
- Initial release.
