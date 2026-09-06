# Calibre Book Selector: Copilot Guardrails & Rules

You are reviewing or writing code for **Calibre Book Selector**, an Interface Action plugin for Calibre 9.x that intelligently selects eligible books and series entries to append to a designated Reading List (default: `"Next"`) with sequential order incrementing.

## 🛑 CRITICAL CONSTRAINTS (DO NOT SUGGEST THESE)

1. **NO Reading Progress Violations:** Books with reading progress (`#kobo_percent_read > 0` or custom configured column) or already in the target list must NEVER be offered as selection candidates.
2. **NO Out-of-Order Series Additions:** Standalone books are eligible, but for any series represented, ONLY the book with the lowest available `series_index` is eligible. Higher-indexed books in that series must be filtered out.
3. **NO Author or Series Clumping:** Candidates must strictly respect `min_author_separation` (default: 6) and `min_series_separation` (default: 6) relative to the trailing entries of the target list.
4. **NO Manual DB Corruptions:** When running in the Calibre GUI, do not directly alter the Reading List database preference if the Reading List plugin interface action is available; delegate to `gui.iactions['Reading List'].add_books_to_list(...)` to trigger proper UI updates and custom column sync.
5. **NO Unversioned Changes:** Never update `__init__.py` without updating `about.txt` and `CHANGELOG.md`, or vice versa. Versions must match SemVer format exactly.

## 📐 ARCHITECTURE RULES (ENFORCE THESE)

1. **Sequential Order Increment:** Reading List content is an ordered list of book IDs in `content: [id1, id2, ...]`. Appending a book gives it order index `len(content) + 1`.
2. **PyQt6 / Qt Compatibility:** Calibre 9.x uses PyQt6. Use appropriate Qt widgets and dialog patterns (`QDialog`, `QTableWidget`, `QLineEdit`, `QVBoxLayout`). Ensure table selections are explicitly cleared or updated after mutations.
3. **Preference Persistence:** Plugin settings use Calibre's `JSONConfig('plugins/calibre_book_selector')`. Target list settings are read from Calibre's library database preferences under `namespaced:ReadingListPlugin:settings`.
4. **Clean Packaging:** All distributable files must be listed in `build_plugin.py`'s `FILES_TO_PACKAGE` and installable via `calibre-customize -a calibre-book-selector.zip`.
5. **Version Synchronization:** Ensure `version = (X, Y, Z)` in `__init__.py`, `Version: X.Y.Z` in `about.txt`, and `[X.Y.Z]` in `CHANGELOG.md` are always kept identical.

