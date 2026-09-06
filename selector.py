import json
import random
from collections import OrderedDict

try:
    from calibre_plugins.calibre_book_selector.config import (
        get_pref,
        KEY_TARGET_LIST,
        KEY_PERCENT_READ_COLUMN,
        KEY_EXCLUDE_PERCENT_READ,
        KEY_ENFORCE_SERIES_ORDER,
        KEY_MIN_AUTHOR_SEPARATION,
        KEY_MIN_SERIES_SEPARATION,
        DEFAULT_TARGET_LIST,
        DEFAULT_PERCENT_READ_COLUMN,
        DEFAULT_EXCLUDE_PERCENT_READ,
        DEFAULT_MIN_AUTHOR_SEPARATION,
        DEFAULT_MIN_SERIES_SEPARATION,
    )
except ImportError:
    from config import (
        get_pref,
        KEY_TARGET_LIST,
        KEY_PERCENT_READ_COLUMN,
        KEY_EXCLUDE_PERCENT_READ,
        KEY_ENFORCE_SERIES_ORDER,
        KEY_MIN_AUTHOR_SEPARATION,
        KEY_MIN_SERIES_SEPARATION,
        DEFAULT_TARGET_LIST,
        DEFAULT_PERCENT_READ_COLUMN,
        DEFAULT_EXCLUDE_PERCENT_READ,
        DEFAULT_MIN_AUTHOR_SEPARATION,
        DEFAULT_MIN_SERIES_SEPARATION,
    )

READING_LIST_PREF_KEY = 'namespaced:ReadingListPlugin:settings'


def get_reading_list_settings(db):
    """
    Retrieve Reading List plugin preferences dict from the Calibre database.
    Works across both db.new_api and legacy db interfaces.
    """
    raw_val = None
    try:
        if hasattr(db, 'pref'):
            raw_val = db.pref(READING_LIST_PREF_KEY)
        elif hasattr(db, 'new_api') and hasattr(db.new_api, 'pref'):
            raw_val = db.new_api.pref(READING_LIST_PREF_KEY)
        elif hasattr(db, 'backend') and hasattr(db.backend, 'prefs'):
            raw_val = db.backend.prefs.get(READING_LIST_PREF_KEY)
    except Exception:
        pass

    if not raw_val:
        return {}

    if isinstance(raw_val, dict):
        return raw_val

    if isinstance(raw_val, str):
        try:
            return json.loads(raw_val)
        except Exception:
            return {}

    return {}


def set_reading_list_settings(db, settings_dict):
    """
    Save updated Reading List plugin settings dict back into database preferences.
    """
    val = json.dumps(settings_dict, indent=2)
    try:
        if hasattr(db, 'set_pref'):
            db.set_pref(READING_LIST_PREF_KEY, val)
        elif hasattr(db, 'new_api') and hasattr(db.new_api, 'set_pref'):
            db.new_api.set_pref(READING_LIST_PREF_KEY, val)
        elif hasattr(db, 'backend') and hasattr(db.backend, 'prefs'):
            db.backend.prefs.set(READING_LIST_PREF_KEY, val)
    except Exception as e:
        print(f"[CalibreBookSelector] Error saving Reading List settings: {e}")
        return False
    return True


def resolve_list_name(db, list_name=None):
    """
    Resolve the actual list name in Reading List settings.
    If 'Next' is requested but only '02 - Next' exists in the library, fall back cleanly.
    """
    if list_name is None:
        list_name = get_pref(KEY_TARGET_LIST, DEFAULT_TARGET_LIST)

    settings = get_reading_list_settings(db)
    lists = settings.get('lists', {})
    if list_name in lists:
        return list_name
    if list_name == 'Next' and '02 - Next' in lists:
        return '02 - Next'
    return list_name


def get_list_book_ids(db, list_name=None):
    """
    Get the ordered list of book IDs in a given Reading List list.
    """
    actual_name = resolve_list_name(db, list_name)
    settings = get_reading_list_settings(db)
    lists = settings.get('lists', {})
    list_info = lists.get(actual_name, {})
    return list(list_info.get('content', []))


def _get_field_fn(db):
    """Return a consistent field getter function for Calibre DB."""
    if hasattr(db, 'new_api'):
        return db.new_api.field_for
    else:
        return lambda f, bid: db.get_field(bid, f, default_value=None)


def _is_book_read_or_in_progress(get_field, bid, percent_column):
    """
    Check if a book is read or in progress based on percent read column (e.g. #kobo_percent_read > 0).
    """
    try:
        val = get_field(percent_column, bid)
        if val is None:
            return False
        if isinstance(val, (int, float)):
            return val > 0
        if isinstance(val, str) and val.strip():
            try:
                num = float(val.strip().rstrip('%'))
                return num > 0
            except ValueError:
                return False
    except Exception:
        pass
    return False


def _get_recent_trailing_metadata(db, target_list, author_spacing, series_spacing):
    """
    Examine the trailing books in target list to determine which authors
    and series are currently within the cooldown / spacing window.
    """
    list_ids = get_list_book_ids(db, target_list)
    if not list_ids:
        return set(), set()

    get_field = _get_field_fn(db)
    recent_authors = set()
    recent_series = set()

    if author_spacing > 0:
        trailing_author_ids = list_ids[-author_spacing:]
        for bid in trailing_author_ids:
            try:
                authors = get_field('authors', bid) or ()
                if isinstance(authors, (list, tuple)):
                    for a in authors:
                        if a:
                            recent_authors.add(a.strip().lower())
                elif isinstance(authors, str) and authors.strip():
                    recent_authors.add(authors.strip().lower())
            except Exception:
                pass

    if series_spacing > 0:
        trailing_series_ids = list_ids[-series_spacing:]
        for bid in trailing_series_ids:
            try:
                series = get_field('series', bid)
                if series and isinstance(series, str) and series.strip():
                    recent_series.add(series.strip().lower())
            except Exception:
                pass

    return recent_authors, recent_series


def get_eligible_books(
    db,
    target_list=None,
    exclude_percent_read=None,
    percent_read_column=None,
    enforce_series=None,
    min_author_separation=None,
    min_series_separation=None,
):
    """
    Get all books in the library eligible to be added to the Next list.

    Rules applied:
    1. The book must NOT be currently in the target list ('Next').
    2. The book must NOT have read progress if exclude_percent_read is True (default #kobo_percent_read > 0).
    3. If the book is part of a series and enforce_series is True:
       - Only the candidate book with the lowest series_index in that series is eligible.
       - Higher numbered books in that series are filtered out.
    4. Minimum Author Separation:
       - If min_author_separation > 0, books by authors appearing in the trailing N books of target list are filtered out.
    5. Minimum Series Separation:
       - If min_series_separation > 0, books belonging to series appearing in the trailing N books of target list are filtered out.

    Returns:
        tuple (eligible_books, total_library_count, excluded_count, series_filtered_count, spacing_filtered_count)
    """
    if target_list is None:
        target_list = get_pref(KEY_TARGET_LIST, DEFAULT_TARGET_LIST)
    actual_target = resolve_list_name(db, target_list)

    if exclude_percent_read is None:
        exclude_percent_read = get_pref(KEY_EXCLUDE_PERCENT_READ, DEFAULT_EXCLUDE_PERCENT_READ)
    if percent_read_column is None:
        percent_read_column = get_pref(KEY_PERCENT_READ_COLUMN, DEFAULT_PERCENT_READ_COLUMN)
    if enforce_series is None:
        enforce_series = get_pref(KEY_ENFORCE_SERIES_ORDER, True)
    if min_author_separation is None:
        min_author_separation = get_pref(KEY_MIN_AUTHOR_SEPARATION, DEFAULT_MIN_AUTHOR_SEPARATION)
    if min_series_separation is None:
        min_series_separation = get_pref(KEY_MIN_SERIES_SEPARATION, DEFAULT_MIN_SERIES_SEPARATION)

    target_list_book_ids = set(get_list_book_ids(db, actual_target))
    get_field = _get_field_fn(db)

    # Fetch all book IDs in the library
    if hasattr(db, 'new_api'):
        all_book_ids = db.new_api.all_book_ids()
    else:
        all_book_ids = db.all_ids()

    total_count = len(all_book_ids)
    candidate_books = []

    for bid in all_book_ids:
        # Exclude books already in the Next list
        if bid in target_list_book_ids:
            continue

        # Exclude books already read or in progress
        if exclude_percent_read and _is_book_read_or_in_progress(get_field, bid, percent_read_column):
            continue

        try:
            title = get_field('title', bid) or 'Untitled'
            raw_authors = get_field('authors', bid) or ()
            if isinstance(raw_authors, (list, tuple)):
                author_list = [a.strip() for a in raw_authors if a and a.strip()]
                author_str = ' & '.join(author_list)
            else:
                author_str = str(raw_authors).strip()
                author_list = [author_str] if author_str else []

            series = get_field('series', bid)
            series_index = get_field('series_index', bid)
            if series_index is None:
                series_index = 1.0
            else:
                try:
                    series_index = float(series_index)
                except (ValueError, TypeError):
                    series_index = 1.0

            tags = get_field('tags', bid) or ()
            if isinstance(tags, (list, tuple)):
                tag_str = ', '.join(tags)
            else:
                tag_str = str(tags)

            rating = get_field('rating', bid) or 0
            pubdate = get_field('pubdate', bid)

            candidate_books.append({
                'id': bid,
                'title': title,
                'author': author_str,
                'author_list': author_list,
                'series': series if series else None,
                'series_index': series_index if series else None,
                'tags': tag_str,
                'rating': rating,
                'pubdate': pubdate,
            })
        except Exception as e:
            print(f"[CalibreBookSelector] Error loading metadata for book ID {bid}: {e}")

    excluded_count = total_count - len(candidate_books)

    # 1. Apply series lowest-index progression filter if enabled
    series_filtered_count = 0
    if enforce_series:
        standalone_books = []
        series_map = {}  # series_name -> list of candidate books

        for book in candidate_books:
            s_name = book['series']
            if not s_name:
                standalone_books.append(book)
            else:
                series_map.setdefault(s_name, []).append(book)

        series_selected_books = list(standalone_books)
        for s_name, books_in_series in series_map.items():
            books_in_series.sort(key=lambda x: (x['series_index'], x['id']))
            lowest_book = books_in_series[0]
            series_selected_books.append(lowest_book)
            series_filtered_count += (len(books_in_series) - 1)
        candidate_books = series_selected_books

    # 2. Apply author and series separation / cooldown spacing rules
    recent_authors, recent_series = _get_recent_trailing_metadata(
        db, actual_target, min_author_separation, min_series_separation
    )

    eligible_books = []
    spacing_filtered_count = 0

    for book in candidate_books:
        # Check author separation
        book_authors_lower = {a.lower() for a in book['author_list']}
        if min_author_separation > 0 and (book_authors_lower & recent_authors):
            spacing_filtered_count += 1
            continue

        # Check series separation
        if min_series_separation > 0 and book['series'] and (book['series'].strip().lower() in recent_series):
            spacing_filtered_count += 1
            continue

        eligible_books.append(book)

    # Sort final eligible books
    eligible_books.sort(key=lambda b: (
        (b['series'] or b['title']).lower(),
        b['series_index'] if b['series_index'] is not None else 0,
        b['title'].lower()
    ))

    return eligible_books, total_count, excluded_count, series_filtered_count, spacing_filtered_count


def pick_random_eligible_book(
    db,
    target_list=None,
    exclude_percent_read=None,
    percent_read_column=None,
    enforce_series=None,
    min_author_separation=None,
    min_series_separation=None,
):
    """
    Select a single random book from the list of eligible books.
    """
    eligible_books, total, excluded, series_filt, space_filt = get_eligible_books(
        db,
        target_list=target_list,
        exclude_percent_read=exclude_percent_read,
        percent_read_column=percent_read_column,
        enforce_series=enforce_series,
        min_author_separation=min_author_separation,
        min_series_separation=min_series_separation,
    )
    if not eligible_books:
        return None
    return random.choice(eligible_books)


def get_next_order_number(db, target_list=None):
    """
    Calculate the next sequential Order number (1-based index)
    that will be assigned to a book added to target_list.
    """
    current_ids = get_list_book_ids(db, target_list)
    return len(current_ids) + 1


def add_books_to_target_list(gui, db, book_ids, target_list=None):
    """
    Add one or more books to the target Reading List ('Next').
    If GUI and Reading List plugin are present, delegates to Reading List action
    for automatic custom column updating and UI synchronization.
    Otherwise updates DB preferences directly.

    Returns:
        tuple (success, added_ids, starting_order, error_message)
    """
    if not book_ids:
        return False, [], 0, "No books specified to add."

    actual_target = resolve_list_name(db, target_list)
    starting_order = get_next_order_number(db, actual_target)

    # Check if Reading List plugin action is active in the Calibre GUI
    if gui is not None and hasattr(gui, 'iactions') and 'Reading List' in gui.iactions:
        try:
            rl_action = gui.iactions['Reading List']
            success = rl_action.add_books_to_list(
                actual_target, book_ids, refresh_screen=True, display_warnings=False
            )
            if success:
                return True, book_ids, starting_order, None
        except Exception as e:
            print(f"[CalibreBookSelector] Calling Reading List plugin failed: {e}. Falling back to direct update.")

    # Fallback to direct DB update
    try:
        settings = get_reading_list_settings(db)
        if 'lists' not in settings:
            settings['lists'] = {}

        if actual_target not in settings['lists']:
            settings['lists'][actual_target] = {
                'content': [],
                'displayTopMenu': False,
                'listType': 'SYNCNEW',
                'modifyAction': 'TAGADDREMOVE',
                'populateSearch': '',
                'populateType': 'POPMANUAL',
                'restoreSort': False,
                'seriesColumn': '#read_order',
                'seriesName': 'Next Queue',
                'sortList': True,
                'syncAuto': True,
                'syncClear': False,
                'syncDevice': '',
                'tagsColumn': '#reading_list',
                'tagsText': actual_target,
            }

        list_content = settings['lists'][actual_target].get('content', [])
        content_set = set(list_content)

        added = []
        for bid in book_ids:
            if bid not in content_set:
                list_content.append(bid)
                content_set.add(bid)
                added.append(bid)

        settings['lists'][actual_target]['content'] = list_content
        set_reading_list_settings(db, settings)

        # If custom tag column is specified in list definition, apply tags
        tags_col = settings['lists'][actual_target].get('tagsColumn')
        tags_text = settings['lists'][actual_target].get('tagsText')
        if tags_col and tags_text:
            try:
                for bid in added:
                    if hasattr(db, 'new_api'):
                        existing_tags = list(db.new_api.field_for(tags_col, bid) or ())
                        if tags_text not in existing_tags:
                            existing_tags.append(tags_text)
                            db.new_api.set_field(tags_col, {bid: existing_tags})
                    elif hasattr(db, 'set_custom'):
                        db.set_custom(bid, tags_text, label=tags_col[1:] if tags_col.startswith('#') else tags_col)
            except Exception as tag_err:
                print(f"[CalibreBookSelector] Warning setting tag column: {tag_err}")

        return True, added, starting_order, None

    except Exception as e:
        return False, [], 0, f"Failed to add books to {actual_target}: {str(e)}"
