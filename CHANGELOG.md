# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Release policy:

- Keep in-progress changes under `## [Unreleased]` while work is still in progress on non-`main` branches.
- Mint the numbered release heading before opening a pull request to `main`.
- The first numbered release for this project will be `1.0.0`.
- Version numbers follow SemVer 2.0.0: MAJOR for incompatible changes, MINOR for backward-compatible functionality, and PATCH for backward-compatible bug fixes.

## [Unreleased]

### Added

- Packaged `about.txt` metadata description file and empty `plugin-import-name-calibre_book_selector.txt` per official Calibre plugin guidelines.
- `apply_settings()` lifecycle callback in `action.py` and `__init__.py` to reload preferences when modified via Calibre's Customize Plugin interface.
- Expanded version minting and synchronization rules across `__init__.py`, `about.txt`, and `CHANGELOG.md` in `AGENTS.md`, Copilot instructions, and PR template.
- Documentation links to the official [Reading List plugin wiki](https://github.com/kiwidude68/calibre_plugins/wiki/Reading-List) in `README.md` and `AGENTS.md`.
- Automatic decimal series progression: when a book with a fractional series index (e.g. 1.5, 4.5) is selected, automatically queue it and all unread books in that series up to the next whole integer (e.g. 2.0, 5.0).
- Checkbox configuration option in `ConfigWidget` and `ConfigDialog` to toggle the decimal series progression behavior (enabled by default).
- Core engine methods `get_series_books_up_to_next_integer()` and `pick_random_eligible_books()` in `selector.py`.
- Comprehensive unit test cases covering single-step and multi-step decimal series progression, exclusion filtering, missing library titles, and config toggle states.
- File-level `<!-- markdownlint-disable -->` directives on generated planning and walkthrough artifacts to suppress external markdownlint warnings in the editor.
- Expanded Git workflow and commit policy documentation in `AGENTS.md` and `.github/copilot-instructions.md`, explicitly prohibiting automated git operations.

## [1.0.1] - 2026-09-06

### Added

- Monokai Pro styled badges in `README.md` for release version, total downloads, build status, Calibre compatibility, Python version, PyQt6 GUI framework, and MIT license.
- Embedded UI screenshot in `README.md` showcasing the live Book Selector dialog and real-time filtering stats.
- Real-world statistics breakdown in `README.md` connecting live library metrics directly to the core business rules.
- Explicit Prerequisites section in `README.md` documenting the Calibre Reading List companion plugin requirement and recommended custom columns.
- `ConfigWidget` integration in `dialogs.py` and `__init__.py` enabling direct plugin customization via Calibre's **Preferences &rarr; Plugins &rarr; Customize plugin** interface.
- Markdownlint configuration (`.markdownlint.json` and `.markdownlintignore`) to support standard Keep a Changelog heading structures.

### Changed

- Formatted rule sections in `README.md` with clean markdown subheadings to satisfy strict markdownlint compliance (`MD033` and `MD051`).

## [1.0.0] - 2026-09-06

### Added

- Simplified book selection engine to manage a single Reading List named `Next`.
- Automatic read and in-progress book exclusion using `% Read > 0` (`#kobo_percent_read`).
- Series progression filter ensuring only the lowest numbered available book in any series is eligible for selection.
- Minimum author separation constraint (default 6 books) preventing recently queued authors from repeating in the selection queue.
- Minimum series separation constraint (default 6 books) preventing recently queued series from repeating in the selection queue.
- Automatic list order increment calculation when appending books to `Next`.
- Interactive Book Selector dialog with live search, table view, random picker, and selection actions.
- Quick action to randomly select and add an eligible book in a single click.
- Streamlined configuration dialog with author spacing, series spacing, and percent read column settings.
- Seamless integration with the Calibre Reading List plugin and library database.
- Build and packaging script `build_plugin.py` for Calibre Portable integration.
- Comprehensive user guide in `README.md` and agent reference in `AGENTS.md`.

### Fixed

- Clear table row selection after adding books to the reading list to prevent Qt from maintaining stale row selections on subsequent books.
