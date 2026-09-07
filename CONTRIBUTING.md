# Contributing to Calibre Book Selector

Thank you for your interest in contributing to **Calibre Book Selector**!

Calibre Book Selector is a Calibre 9.x Interface Action plugin that intelligently queries the active Calibre library to find eligible candidate books and queues them into a designated Reading List (default `"Next"`, via the [Reading List plugin](https://github.com/kiwidude68/calibre_plugins/wiki/Reading-List)), strictly enforcing read status exclusions, series progression order, author/series separation spacing, and decimal series progression.

We welcome pull requests that align with the plugin's core philosophy, architecture, and reliability standards. Please take a moment to review these guidelines before submitting changes.

---

## 🎯 Core Project Philosophy & Business Rules

Before proposing features or submitting pull requests, please keep the following core constraints in mind:

1. **Queue & Read Status Exclusions**:
   - Books currently present in the target Reading List (`"Next"`) must NOT be offered as candidates.
   - Books with reading progress (e.g. `#kobo_percent_read > 0`) must NOT be offered as candidates, cleanly excluding currently-reading and completed books.
   - Target list membership is read from the Calibre library database preference key: `namespaced:ReadingListPlugin:settings`.

2. **Strict Series Progression Constraint**:
   - For every series represented in the candidate books, ONLY the book with the lowest `series_index` among available (unexcluded) books is marked eligible.
   - Higher-indexed books in that series are filtered out.
   - Standalone books (where `series` is `None` or empty) are always eligible if not excluded.

3. **Sequential Order Increment**:
   - Reading List lists maintain an ordered list of book IDs in `content: [id1, id2, ...]`.
   - Adding a new book appends it to the end of the list, assigning it Order index `len(content) + 1`.
   - When running within the Calibre GUI, the plugin delegates to `gui.iactions['Reading List'].add_books_to_list(...)` to trigger native custom column and UI tag synchronizations.

4. **Author & Series Separation Constraints**:
   - `min_author_separation` (default: 6): Authors present in the trailing $N$ entries of the target list cannot be selected.
   - `min_series_separation` (default: 6): Series present in the trailing $N$ entries of the target list cannot be selected.
   - Both constraints can be customized or disabled (set to `0`) in Plugin Settings.

5. **Decimal Series Progression (Auto-Add to Next Whole Integer)**:
   - When a book with a fractional `series_index` (e.g. 1.5, 4.2) is selected and `auto_add_series_decimals` is enabled (default: `True`), all subsequent unread, unqueued books in that series up to the next whole integer (e.g. 2.0, 5.0) are automatically queued in ascending sequential order.

---

## 🌿 Branching Strategy & Workflow

- **Development Branch (`develop`)**: All feature development, bug fixes, and documentation improvements target the `develop` branch.
- **Release Branch (`main`)**: Merging a Pull Request into `main` triggers the automated **Release Plugin Zip** GitHub Actions workflow, tagging a new release `vX.Y.Z` and attaching `calibre-book-selector.zip`.
- **User-Managed Commits**: AI agents and automated tools must NEVER run `git add`, `git commit`, or `git push` commands directly, and must not prompt or ask to run them. All staging, committing, and pushing is handled exclusively by maintainers.

### Versioning Protocol

When preparing a pull request for a new version release:

1. **Source Version**: Update `version = (X, Y, Z)` in `__init__.py`.
2. **About Metadata**: Update `Version: X.Y.Z` in `about.txt`.
3. **Changelog**: Move unreleased changes in `CHANGELOG.md` into a new release header `## [X.Y.Z] - YYYY-MM-DD` and retain an empty `## [Unreleased]` section.
4. **Consistency Rule**: `__init__.py`, `about.txt`, and `CHANGELOG.md` versions MUST remain identical at all times.
5. **SemVer Adherence**: Version numbers follow [Semantic Versioning 2.0.0](https://semver.org/spec/v2.0.0.html) (MAJOR.MINOR.PATCH).

### Post-Release Sync Protocol

Once your Pull Request is merged into `main` on GitHub, synchronize your local branches:

```bash
git fetch origin
git checkout main && git pull origin main
git checkout develop && git merge main
git push origin develop
```

---

## 🏗 Architectural & Coding Guidelines

### 1. Calibre 9.x & PyQt6 Compatibility

Calibre 9.x runs Python 3 and PyQt6.

- Use appropriate Qt widgets (`QDialog`, `QTableWidget`, `QLineEdit`, `QVBoxLayout`, `QHBoxLayout`, `QCheckBox`, `QSpinBox`).
- When updating table views or queue contents, explicitly clear selections (`table.clearSelection()`, `table.setCurrentItem(None)`) to prevent stale row selections.

### 2. Dual Database Interface Support

Code querying the Calibre library database must support both:

- `db.new_api` (modern fast Calibre cache API: `db.new_api.all_book_ids()`, `db.new_api.field_for`).
- Legacy / mock database interfaces (e.g. `DummyDatabase` using `all_ids()` and `get_field()`) used during automated testing without running Calibre.

### 3. Preference Persistence

- Plugin settings use Calibre's `JSONConfig('plugins/calibre_book_selector')` via `config.py`.
- Target list membership and order are read from the Calibre library database preferences under `namespaced:ReadingListPlugin:settings`.
- Support Calibre's plugin configuration lifecycle by implementing `config_widget()` and `save_settings()` on `CalibreBookSelectorPlugin` in `__init__.py` and `apply_settings()` on `BookSelectorAction` in `action.py`.

### 4. Clean Packaging

All files distributed in the plugin zip must be declared in `FILES_TO_PACKAGE` within `build_plugin.py`. Ensure the plugin installs cleanly via:

```powershell
& "E:\Calibre Portable\Calibre\calibre-customize.exe" -a calibre-book-selector.zip
```

---

## 🧪 Testing Standards

Calibre Book Selector enforces automated testing before any code is merged.

1. **Unit & Logic Tests**: Core selection rules, series lowest-index progression, author/series separation, decimal series auto-add, and order incrementing are covered by unit tests with mocked database fixtures (`DummyDatabase`).
2. **UI Tests**: Dialog lifecycle, table population, and row selection clearing are tested using headless or active `QApplication` instances (`TestBookSelectorDialog`).
3. **Active Library Integration Tests**: When run against a local Calibre installation, tests verify live database queries against the user's active library database (`TestRealCalibreLibrary`).

### Test Commands

Run the full automated test suite using Calibre's debug executable:

```powershell
& "E:\Calibre Portable\Calibre\calibre-debug.exe" test_selector.py
```

Build the distributable `.zip` archive:

```powershell
& "E:\Calibre Portable\Calibre\calibre-debug.exe" build_plugin.py
```

Build and install directly into your local Calibre Portable environment:

```powershell
& "E:\Calibre Portable\Calibre\calibre-debug.exe" -e build_plugin.py -- --install
```

---

## 📋 Pull Request Submission Checklist

Before opening a Pull Request:

- [ ] All unit and functional tests pass locally (`& "E:\Calibre Portable\Calibre\calibre-debug.exe" test_selector.py`).
- [ ] Plugin builds cleanly into `calibre-book-selector.zip` (`& "E:\Calibre Portable\Calibre\calibre-debug.exe" build_plugin.py`).
- [ ] Code follows Python conventions and PyQt6 compatibility guidelines.
- [ ] `CHANGELOG.md` is updated under `## [Unreleased]` describing the changes.
- [ ] If releasing a new version, version numbers are synchronized across `__init__.py`, `about.txt`, and `CHANGELOG.md`.
- [ ] Pull request description clearly explains the rationale, user impact, and verification steps.
