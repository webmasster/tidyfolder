# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-11-13

### Added

- `tidyfolder organize` moves files into category folders, with an optional
  `YYYY-MM` grouping by modification time.
- `--dry-run` previews planned moves, grouped by category, without changing
  any files.
- JSON undo log with SHA-256 checksums, and `tidyfolder undo` to restore a
  previous layout (skipped when a file has changed, unless `--force` is used).
- Optional `tidyfolder.toml` configuration for default flags and category
  rules, plus `tidyfolder categories` to inspect the active map.
- `tidyfolder dupes` finds identical files by content hash and can move extra
  copies into a folder without deleting anything.
- Safety checks: no overwrites, skipped hidden files and symbolic links,
  refusal to organize the home directory or system paths without `--force`.
