# 📝 Description

Please include a summary of the change, rationale, motivation, and any context.

Fixes / Closes #(issue number)

## 📐 Scope & Architecture Checklist

Please confirm that your Pull Request adheres to the core rules of Calibre Book Selector:

- [ ] **Queue & Read Status Exclusions**: Books with reading progress (`#kobo_percent_read > 0`) or already queued in `"Next"` are never returned as eligible candidates.
- [ ] **Series Progression**: Only the lowest available `series_index` for any series is marked eligible; higher series numbers are filtered out.
- [ ] **Author & Series Separation**: Configured separation minimums (default 6) from the trailing entries of the target list are strictly respected.
- [ ] **Order Increment**: Book additions append to the list with sequential order index incrementing (`len(content) + 1`).
- [ ] **Calibre & Qt6 Integrity**: UI components and database interactions cleanly support Calibre 9.x / PyQt6 without freezing the UI thread.

## 🧪 Testing Checklist

- [ ] I have executed unit/functional tests locally (`& "E:\Calibre Portable\Calibre\calibre-debug.exe" test_selector.py`) and all tests pass.
- [ ] Plugin builds cleanly into zip (`& "E:\Calibre Portable\Calibre\calibre-debug.exe" build_plugin.py`).
- [ ] Version numbers are synchronized across `__init__.py`, `about.txt`, and `CHANGELOG.md` (or release heading minted if releasing).
