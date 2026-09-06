import os
import sys
import unittest
import sqlite3
import json

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from selector import (
    get_reading_list_settings,
    get_list_book_ids,
    get_eligible_books,
    pick_random_eligible_book,
    get_next_order_number,
    READING_LIST_PREF_KEY,
)
from config import (
    DEFAULT_TARGET_LIST,
    DEFAULT_PERCENT_READ_COLUMN,
    DEFAULT_EXCLUDE_PERCENT_READ,
    DEFAULT_MIN_AUTHOR_SEPARATION,
    DEFAULT_MIN_SERIES_SEPARATION,
)


class DummyDatabase:
    """Mock DB mimicking Calibre DB interface for unit tests."""
    def __init__(self, prefs_dict=None, books_data=None):
        self._prefs = prefs_dict or {}
        self._books = books_data or {}

    def pref(self, key):
        return self._prefs.get(key)

    def set_pref(self, key, value):
        self._prefs[key] = value

    def all_ids(self):
        return list(self._books.keys())

    def get_field(self, bid, field, default_value=None):
        book = self._books.get(bid, {})
        return book.get(field, default_value)


class TestCalibreBookSelector(unittest.TestCase):

    def setUp(self):
        # Sample dataset
        # Series A (Author 1): Book 1 (100% read), Book 2 (unread), Book 3 (unread)
        # Series B (Author 2): Book 4 (in Next), Book 5 (unread)
        # Series C (Author 5): Book 6 (unread), Book 7 (unread)
        # Standalones: Book 10 (Author 3, 56% read), Book 11 (Author 4, unread), Book 12 (Author 1, unread)
        self.books = {
            1: {'title': 'A1', 'authors': ['Author 1'], 'series': 'Series A', 'series_index': 1.0, '#kobo_percent_read': 100},
            2: {'title': 'A2', 'authors': ['Author 1'], 'series': 'Series A', 'series_index': 2.0, '#kobo_percent_read': 0},
            3: {'title': 'A3', 'authors': ['Author 1'], 'series': 'Series A', 'series_index': 3.0, '#kobo_percent_read': None},
            4: {'title': 'B1', 'authors': ['Author 2'], 'series': 'Series B', 'series_index': 1.0, '#kobo_percent_read': 0},
            5: {'title': 'B2', 'authors': ['Author 2'], 'series': 'Series B', 'series_index': 2.0, '#kobo_percent_read': 0},
            6: {'title': 'C1', 'authors': ['Author 5'], 'series': 'Series C', 'series_index': 1.0, '#kobo_percent_read': 0},
            7: {'title': 'C2', 'authors': ['Author 5'], 'series': 'Series C', 'series_index': 2.0, '#kobo_percent_read': 0},
            10: {'title': 'Standalone 1', 'authors': ['Author 3'], 'series': None, 'series_index': None, '#kobo_percent_read': 56},
            11: {'title': 'Standalone 2', 'authors': ['Author 4'], 'series': None, 'series_index': None, '#kobo_percent_read': 0},
            12: {'title': 'Standalone 3', 'authors': ['Author 1'], 'series': None, 'series_index': None, '#kobo_percent_read': None},
        }

        # Reading list setup:
        # Only ONE list: "Next", containing Book 4
        self.rl_settings = {
            'lists': {
                'Next': {'content': [4]},
            }
        }

        self.db = DummyDatabase(
            prefs_dict={READING_LIST_PREF_KEY: json.dumps(self.rl_settings)},
            books_data=self.books
        )

    def test_reading_list_settings_parsing(self):
        settings = get_reading_list_settings(self.db)
        self.assertIn('lists', settings)
        self.assertEqual(get_list_book_ids(self.db, 'Next'), [4])

    def test_next_and_percent_read_exclusions(self):
        # Book 1 has 100% read -> excluded
        # Book 10 has 56% read -> excluded
        # Book 4 is in Next -> excluded
        eligible, total, excluded_count, series_filtered, spacing_filtered = get_eligible_books(
            self.db,
            target_list='Next',
            exclude_percent_read=True,
            percent_read_column='#kobo_percent_read',
            enforce_series=False,
            min_author_separation=0,
            min_series_separation=0,
        )

        eligible_ids = {b['id'] for b in eligible}
        self.assertNotIn(1, eligible_ids) # 100% read
        self.assertNotIn(10, eligible_ids) # 56% read
        self.assertNotIn(4, eligible_ids) # in Next list
        self.assertEqual(total, 10)
        self.assertEqual(excluded_count, 3)

    def test_series_lowest_index_progression(self):
        # Spacing disabled (0, 0) to test pure series logic with % read exclusions
        eligible, total, excluded_count, series_filtered, spacing_filtered = get_eligible_books(
            self.db,
            target_list='Next',
            exclude_percent_read=True,
            percent_read_column='#kobo_percent_read',
            enforce_series=True,
            min_author_separation=0,
            min_series_separation=0,
        )

        eligible_ids = {b['id'] for b in eligible}

        # Expected:
        # - Book 1 (A1) is 100% read -> excluded.
        # - Book 2 (A2) is lowest unread in Series A -> ELIGIBLE.
        # - Book 3 (A3) is unread but index 3.0 > 2.0 -> FILTERED OUT.
        # - Book 4 (B1) is in Next -> excluded.
        # - Book 5 (B2) is unread lowest in Series B -> ELIGIBLE.
        # - Book 6 (C1) is unread lowest in Series C -> ELIGIBLE.
        # - Book 7 (C2) is index 2.0 > 1.0 -> FILTERED OUT.
        # - Book 10 is 56% read -> excluded.
        # - Book 11 is unread standalone -> ELIGIBLE.
        # - Book 12 is unread standalone -> ELIGIBLE.

        self.assertIn(2, eligible_ids)
        self.assertNotIn(3, eligible_ids)
        self.assertIn(5, eligible_ids)
        self.assertNotIn(1, eligible_ids)
        self.assertNotIn(4, eligible_ids)
        self.assertIn(6, eligible_ids)
        self.assertNotIn(7, eligible_ids)
        self.assertNotIn(10, eligible_ids)
        self.assertIn(11, eligible_ids)
        self.assertIn(12, eligible_ids)

        self.assertEqual(len(eligible), 5)  # Books 2, 5, 6, 11, 12
        self.assertEqual(series_filtered, 2)  # Books 3 and 7

    def test_author_and_series_separation(self):
        # Next list: [Book 1 (Author 1, Series A), Book 4 (Author 2, Series B)]
        self.rl_settings['lists']['Next']['content'] = [1, 4]
        self.db.set_pref(READING_LIST_PREF_KEY, json.dumps(self.rl_settings))

        # min_author_separation=1, min_series_separation=1:
        # Trailing 1 book is Book 4 (Author 2, Series B).
        # Book 5 (Author 2, Series B) must be filtered.
        eligible, _, _, _, spacing_filtered = get_eligible_books(
            self.db,
            target_list='Next',
            exclude_percent_read=True,
            percent_read_column='#kobo_percent_read',
            enforce_series=True,
            min_author_separation=1,
            min_series_separation=1,
        )

        eligible_ids = {b['id'] for b in eligible}
        self.assertNotIn(5, eligible_ids)
        self.assertIn(2, eligible_ids)
        self.assertIn(6, eligible_ids)
        self.assertIn(11, eligible_ids)
        self.assertIn(12, eligible_ids)
        self.assertEqual(spacing_filtered, 1)

    def test_order_increment_calculation(self):
        order = get_next_order_number(self.db, 'Next')
        self.assertEqual(order, 2)

        # 175 books currently in Next -> next order is 176
        self.rl_settings['lists']['Next']['content'] = list(range(1, 176))
        self.db.set_pref(READING_LIST_PREF_KEY, json.dumps(self.rl_settings))
        order_175 = get_next_order_number(self.db, 'Next')
        self.assertEqual(order_175, 176)


class TestRealCalibreLibrary(unittest.TestCase):
    """Test against active Calibre library on disk."""

    def test_active_library(self):
        candidate_paths = [
            r'M:\books\Libraries\Library\metadata.db',
            r'E:\Calibre Portable\Calibre Library\Library\metadata.db',
        ]
        db_path = None
        for p in candidate_paths:
            if os.path.exists(p):
                db_path = p
                break

        if not db_path:
            self.skipTest("No Calibre library found on disk.")

        conn = sqlite3.connect(db_path)
        prefs = dict(conn.execute('SELECT key, val FROM preferences').fetchall())
        rl_raw = prefs.get(READING_LIST_PREF_KEY, '{}')
        rl_data = json.loads(rl_raw) if isinstance(rl_raw, str) else rl_raw

        lists = rl_data.get('lists', {})
        list_name = 'Next' if 'Next' in lists else ('02 - Next' if '02 - Next' in lists else list(lists.keys())[0])
        next_content = lists.get(list_name, {}).get('content', [])

        print(f"\n[Active Library Test: {db_path}]")
        print(f"  Target list '{list_name}': {len(next_content)} books (Next order will be #{len(next_content) + 1})")

        self.assertGreater(len(next_content), 0)


class TestBookSelectorDialog(unittest.TestCase):
    """UI test for BookSelectorDialog selection clearing behavior."""

    @classmethod
    def setUpClass(cls):
        try:
            from qt.core import QApplication
            cls.app = QApplication.instance() or QApplication([])
        except Exception:
            cls.app = None

    def setUp(self):
        if not self.app:
            self.skipTest("Qt QApplication unavailable")

        self.books = {
            1: {'title': 'Book 1', 'authors': ['Author 1'], 'series': None, 'series_index': None, '#kobo_percent_read': 0},
            2: {'title': 'Book 2', 'authors': ['Author 2'], 'series': None, 'series_index': None, '#kobo_percent_read': 0},
            3: {'title': 'Book 3', 'authors': ['Author 3'], 'series': None, 'series_index': None, '#kobo_percent_read': 0},
        }
        self.rl_settings = {'lists': {'Next': {'content': []}}}
        self.db = DummyDatabase(
            prefs_dict={READING_LIST_PREF_KEY: json.dumps(self.rl_settings)},
            books_data=self.books
        )

        class MockGUI:
            pass

        self.gui = MockGUI()
        self.gui.current_db = self.db
        self.gui.iactions = {}

    def test_table_clears_selection_on_reload(self):
        from dialogs import BookSelectorDialog
        dlg = BookSelectorDialog(self.gui)
        self.assertEqual(dlg.table.rowCount(), 3)
        self.assertEqual(len(dlg.table.selectedIndexes()), 0)

        # Select a row (simulating user or random pick)
        dlg.table.selectRow(1)
        self.assertGreater(len(dlg.table.selectedIndexes()), 0)
        self.assertTrue(dlg.table.currentIndex().isValid())

        # Reload data (as happens when a book is added or table refreshed)
        dlg.reload_data()

        # Selection and active cell must be cleared
        self.assertEqual(len(dlg.table.selectedIndexes()), 0)
        self.assertFalse(dlg.table.currentIndex().isValid())

    def test_random_pick_and_reload_clearing(self):
        from dialogs import BookSelectorDialog
        dlg = BookSelectorDialog(self.gui)
        dlg.handle_pick_random()
        self.assertGreater(len(dlg.table.selectedIndexes()), 0)
        selected_ids = dlg.get_selected_book_ids()
        self.assertEqual(len(selected_ids), 1)

        # Re-populating/reloading table must clear selection
        dlg.reload_data()
        self.assertEqual(len(dlg.table.selectedIndexes()), 0)
        self.assertFalse(dlg.table.currentIndex().isValid())


if __name__ == '__main__':
    suite = unittest.TestSuite()
    suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(TestCalibreBookSelector))
    suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(TestBookSelectorDialog))
    suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(TestRealCalibreLibrary))
    res = unittest.TextTestRunner(verbosity=2).run(suite)
    sys.exit(0 if res.wasSuccessful() else 1)

