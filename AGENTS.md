# Agent Operational Reference: Calibre Book Selector Plugin

This document provides architectural context, rules, and development guidelines for AI assistants working in this repository.

---

## 🎯 Project Overview & Purpose

The **Calibre Book Selector** is a Calibre 9.x Interface Action plugin. It queries the active Calibre library to find candidate books and queues them into a designated Reading List (default `"Next"`, via the [Reading List plugin](https://github.com/kiwidude68/calibre_plugins/wiki/Reading-List)), strictly enforcing exclusions, series order constraints, and author/series spacing.

---

## 📐 Core Business Rules

1. **Queue & Read Status Exclusions**:
   - Books currently present in the target Reading List (`"Next"`) must NOT be offered as candidates.
   - Books with reading progress (e.g. `#kobo_percent_read > 0`) must NOT be offered as candidates, cleanly excluding currently-reading and completed books.
   - List membership is stored in the Calibre library database preference key: `namespaced:ReadingListPlugin:settings`.

2. **Series Progression Constraint**:
   - For every series represented in the candidate books, ONLY the book with the lowest `series_index` among available (unexcluded) books is marked eligible.
   - Higher-indexed books in that series are filtered out.
   - Standalone books (where `series` is `None` or empty) are always eligible if not excluded.

3. **Sequential Order Increment**:
   - Reading List lists maintain an ordered list of book IDs in `content: [id1, id2, ...]`.
   - Adding a new book appends it to the end of the list, giving it Order index `len(content) + 1`.
   - When running within the Calibre GUI, the plugin delegates to `gui.iactions['Reading List'].add_books_to_list(...)` to trigger standard custom column and UI tag synchronizations.

4. **Author & Series Separation Constraints**:
   - `min_author_separation` (default: 6): Authors present in the trailing $N$ entries of the target list cannot be selected.
   - `min_series_separation` (default: 6): Series present in the trailing $N$ entries of the target list cannot be selected.

---

## 📁 Repository Structure

- `__init__.py`: Plugin entry point subclassing `calibre.customize.InterfaceActionBase`.
- `action.py`: `InterfaceAction` subclass handling toolbar button, menu entries, and UI events.
- `selector.py`: Selection engine (`get_eligible_books`, `pick_random_eligible_book`, `get_next_order_number`, `add_books_to_target_list`).
- `dialogs.py`: PyQt/Qt6 UI dialogs (`BookSelectorDialog`, `ConfigDialog`).
- `config.py`: Preferences schema and persistence wrapper (`JSONConfig`).
- `build_plugin.py`: Automation script to package into `calibre-book-selector.zip` and install into Calibre.
- `CHANGELOG.md`: Project changelog following Keep a Changelog and SemVer.
- `README.md`: End-user documentation.
- `about.txt`: Metadata description and version file per Calibre plugin specification.
- `plugin-import-name-calibre_book_selector.txt`: 0-byte file declaring the plugin import namespace.
- `LICENSE`: MIT License.
- `images/icon.png`: 128x128 high-DPI icon asset.

---

## 💻 Environment & Testing

- **Calibre Executables**:
  - Debug CLI: `E:\Calibre Portable\Calibre\calibre-debug.exe`
  - Customize CLI: `E:\Calibre Portable\Calibre\calibre-customize.exe`
  - Active Library DB: `M:\books\Libraries\Library\metadata.db` (fallback: `E:\Calibre Portable\Calibre Library\Library\metadata.db`)

### Build & Package

```powershell
& "E:\Calibre Portable\Calibre\calibre-debug.exe" build_plugin.py
```

### Install Plugin

```powershell
& "E:\Calibre Portable\Calibre\calibre-debug.exe" -e build_plugin.py -- --install
```

### Run Unit / Functional Tests

```powershell
& "E:\Calibre Portable\Calibre\calibre-debug.exe" test_selector.py
```

---

## 🏷️ Version Minting & Synchronization

When releasing or minting a new version:

1. **Source Version**: Update `version = (X, Y, Z)` in `__init__.py`.
2. **About Metadata**: Update `Version: X.Y.Z` in `about.txt`.
3. **Changelog**: Move unreleased changes in `CHANGELOG.md` into a new release header `## [X.Y.Z] - YYYY-MM-DD` and retain an empty `## [Unreleased]` section.
4. **Consistency Rule**: `__init__.py`, `about.txt`, and `CHANGELOG.md` versions MUST remain identical at all times.
5. **Automated Release**: When a pull request is merged into `main`, GitHub Actions creates a GitHub release tagged `vX.Y.Z` with the generated `calibre-book-selector.zip` asset.
