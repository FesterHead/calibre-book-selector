import random
from collections import OrderedDict

from qt.core import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QLineEdit,
    QHeaderView,
    QAbstractItemView,
    Qt,
    QIcon,
    QMessageBox,
    QCheckBox,
    QSpinBox,
    QGroupBox,
    pyqtSignal,
    QFont,
    QWidget,
)

# Qt 5/6 compatible flag aliases
USER_ROLE = getattr(getattr(Qt, 'ItemDataRole', None), 'UserRole', getattr(Qt, 'UserRole', 256))
DISPLAY_ROLE = getattr(getattr(Qt, 'ItemDataRole', None), 'DisplayRole', getattr(Qt, 'DisplayRole', 0))
CHECKED_STATE = getattr(getattr(Qt, 'CheckState', None), 'Checked', getattr(Qt, 'Checked', 2))
UNCHECKED_STATE = getattr(getattr(Qt, 'CheckState', None), 'Unchecked', getattr(Qt, 'Unchecked', 0))
ALIGN_CENTER = getattr(getattr(Qt, 'AlignmentFlag', None), 'AlignCenter', getattr(Qt, 'AlignCenter', 0x0084))

try:
    from calibre_plugins.calibre_book_selector.config import (
        get_pref,
        set_pref,
        reset_to_defaults,
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
    from calibre_plugins.calibre_book_selector.selector import (
        get_eligible_books,
        get_next_order_number,
        add_books_to_target_list,
        resolve_list_name,
    )
except ImportError:
    from config import (
        get_pref,
        set_pref,
        reset_to_defaults,
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
    from selector import (
        get_eligible_books,
        get_next_order_number,
        add_books_to_target_list,
        resolve_list_name,
    )


class ConfigWidget(QWidget):
    """
    Configuration widget used inside Calibre Preferences -> Plugins -> Customize Plugin,
    and embedded inside ConfigDialog.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Target List Group
        queue_group = QGroupBox("Target Reading List", self)
        queue_layout = QVBoxLayout(queue_group)

        target_desc = QLabel(
            "Selected books will be added to your reading queue:", self
        )
        queue_layout.addWidget(target_desc)

        target_row = QHBoxLayout()
        target_lbl = QLabel("Queue List Name:", self)
        self.target_edit = QLineEdit(self)
        self.target_edit.setText(get_pref(KEY_TARGET_LIST, DEFAULT_TARGET_LIST))
        target_row.addWidget(target_lbl)
        target_row.addWidget(self.target_edit)
        queue_layout.addLayout(target_row)

        layout.addWidget(queue_group)

        # Read Status Exclusion Group
        read_group = QGroupBox("Read Book Exclusions", self)
        read_layout = QVBoxLayout(read_group)

        self.exclude_read_checkbox = QCheckBox(
            "Exclude books with read progress (% Read > 0)", self
        )
        self.exclude_read_checkbox.setChecked(
            bool(get_pref(KEY_EXCLUDE_PERCENT_READ, DEFAULT_EXCLUDE_PERCENT_READ))
        )
        read_layout.addWidget(self.exclude_read_checkbox)

        col_row = QHBoxLayout()
        col_lbl = QLabel("Percent Read Column:", self)
        self.col_edit = QLineEdit(self)
        self.col_edit.setText(get_pref(KEY_PERCENT_READ_COLUMN, DEFAULT_PERCENT_READ_COLUMN))
        self.col_edit.setToolTip("Lookup name of the custom column (e.g. #kobo_percent_read)")
        col_row.addWidget(col_lbl)
        col_row.addWidget(self.col_edit)
        read_layout.addLayout(col_row)

        layout.addWidget(read_group)

        # Spacing & Separation Rules Group
        spacing_group = QGroupBox("Author & Series Spacing Constraints", self)
        spacing_layout = QVBoxLayout(spacing_group)

        spacing_desc = QLabel(
            "Minimum spacing required between books by the same author or from the same series at the end of the Next list:", self
        )
        spacing_desc.setWordWrap(True)
        spacing_layout.addWidget(spacing_desc)

        # Author Separation SpinBox
        author_row = QHBoxLayout()
        author_lbl = QLabel("Minimum Author Separation (books):", self)
        self.author_spin = QSpinBox(self)
        self.author_spin.setRange(0, 100)
        self.author_spin.setValue(int(get_pref(KEY_MIN_AUTHOR_SEPARATION, DEFAULT_MIN_AUTHOR_SEPARATION)))
        self.author_spin.setToolTip("Set to 0 to disable author spacing")
        author_row.addWidget(author_lbl)
        author_row.addStretch(1)
        author_row.addWidget(self.author_spin)
        spacing_layout.addLayout(author_row)

        # Series Separation SpinBox
        series_row = QHBoxLayout()
        series_lbl = QLabel("Minimum Series Separation (books):", self)
        self.series_spin = QSpinBox(self)
        self.series_spin.setRange(0, 100)
        self.series_spin.setValue(int(get_pref(KEY_MIN_SERIES_SEPARATION, DEFAULT_MIN_SERIES_SEPARATION)))
        self.series_spin.setToolTip("Set to 0 to disable series spacing")
        series_row.addWidget(series_lbl)
        series_row.addStretch(1)
        series_row.addWidget(self.series_spin)
        spacing_layout.addLayout(series_row)

        layout.addWidget(spacing_group)

        # Rules Group
        rules_group = QGroupBox("Series Progression Rules", self)
        rules_layout = QVBoxLayout(rules_group)

        self.series_checkbox = QCheckBox(
            "Enforce Series Progression (Always select lowest available number in series)", self
        )
        self.series_checkbox.setChecked(get_pref(KEY_ENFORCE_SERIES_ORDER, True))
        rules_layout.addWidget(self.series_checkbox)
        layout.addWidget(rules_group)

        # Reset row
        reset_row = QHBoxLayout()
        self.reset_btn = QPushButton("Reset to Defaults", self)
        self.reset_btn.clicked.connect(self.handle_reset)
        reset_row.addWidget(self.reset_btn)
        reset_row.addStretch(1)
        layout.addLayout(reset_row)

    def handle_reset(self):
        self.target_edit.setText(DEFAULT_TARGET_LIST)
        self.exclude_read_checkbox.setChecked(DEFAULT_EXCLUDE_PERCENT_READ)
        self.col_edit.setText(DEFAULT_PERCENT_READ_COLUMN)
        self.author_spin.setValue(DEFAULT_MIN_AUTHOR_SEPARATION)
        self.series_spin.setValue(DEFAULT_MIN_SERIES_SEPARATION)
        self.series_checkbox.setChecked(True)

    def save_settings(self):
        target = self.target_edit.text().strip() or DEFAULT_TARGET_LIST
        col = self.col_edit.text().strip() or DEFAULT_PERCENT_READ_COLUMN

        set_pref(KEY_TARGET_LIST, target)
        set_pref(KEY_PERCENT_READ_COLUMN, col)
        set_pref(KEY_EXCLUDE_PERCENT_READ, self.exclude_read_checkbox.isChecked())
        set_pref(KEY_MIN_AUTHOR_SEPARATION, self.author_spin.value())
        set_pref(KEY_MIN_SERIES_SEPARATION, self.series_spin.value())
        set_pref(KEY_ENFORCE_SERIES_ORDER, self.series_checkbox.isChecked())


class ConfigDialog(QDialog):
    """
    Configuration dialog launched from the Calibre Book Selector toolbar menu.
    """
    def __init__(self, gui=None, parent=None):
        super().__init__(parent or gui)
        self.gui = gui
        self.setWindowTitle("Configure Calibre Book Selector")
        self.setMinimumWidth(500)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        self.config_widget = ConfigWidget(self)
        layout.addWidget(self.config_widget)

        # Button row (Cancel, Save)
        btn_layout = QHBoxLayout()
        btn_layout.addStretch(1)

        self.cancel_btn = QPushButton("Cancel", self)
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)

        self.save_btn = QPushButton("Save Settings", self)
        self.save_btn.setDefault(True)
        self.save_btn.clicked.connect(self.handle_save)
        btn_layout.addWidget(self.save_btn)

        layout.addLayout(btn_layout)

    def handle_save(self):
        self.config_widget.save_settings()
        self.accept()


class BookSelectorDialog(QDialog):
    """
    Main interactive Book Selector dialog.
    Displays eligible books conforming to read status exclusions, series progression rules,
    and author/series spacing constraints.
    """
    books_added_signal = pyqtSignal(list, str)

    def __init__(self, gui, parent=None):
        parent_widget = parent if parent is not None else (gui if isinstance(gui, QWidget) else None)
        super().__init__(parent_widget)
        self.gui = gui
        self.db = gui.current_db
        self.setWindowTitle("Book Selector - Next Reading Queue")
        self.resize(920, 580)

        self.all_eligible_books = []
        self.displayed_books = []

        self.setup_ui()
        self.reload_data()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(10)

        # Header Info Card
        header_card = QGroupBox(self)
        header_layout = QHBoxLayout(header_card)
        header_layout.setContentsMargins(12, 8, 12, 8)

        self.stats_label = QLabel("Loading eligible books...", self)
        stats_font = QFont()
        stats_font.setPointSize(10)
        self.stats_label.setFont(stats_font)
        header_layout.addWidget(self.stats_label)

        header_layout.addStretch(1)

        self.target_badge_label = QLabel("", self)
        badge_font = QFont()
        badge_font.setBold(True)
        self.target_badge_label.setFont(badge_font)
        header_layout.addWidget(self.target_badge_label)

        main_layout.addWidget(header_card)

        # Search / Filter Bar & Actions
        search_layout = QHBoxLayout()
        search_layout.setSpacing(8)

        search_label = QLabel("Search:", self)
        search_layout.addWidget(search_label)

        self.search_input = QLineEdit(self)
        self.search_input.setPlaceholderText("Filter by Title, Author, Series, or Tag...")
        self.search_input.setClearButtonEnabled(True)
        self.search_input.textChanged.connect(self.filter_table)
        search_layout.addWidget(self.search_input, 1)

        self.refresh_btn = QPushButton("🔄 Refresh", self)
        self.refresh_btn.setToolTip("Reload book list from library")
        self.refresh_btn.clicked.connect(self.reload_data)
        search_layout.addWidget(self.refresh_btn)

        self.config_btn = QPushButton("⚙️ Settings", self)
        self.config_btn.setToolTip("Configure queue, exclusions, and spacing rules")
        self.config_btn.clicked.connect(self.open_config)
        search_layout.addWidget(self.config_btn)

        main_layout.addLayout(search_layout)

        # Table of eligible books
        self.table = QTableWidget(self)
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Title", "Author", "Series", "Series #", "Tags"])
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows if hasattr(QAbstractItemView, 'SelectionBehavior') else QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection if hasattr(QAbstractItemView, 'SelectionMode') else QAbstractItemView.ExtendedSelection)
        self.table.setSortingEnabled(True)
        self.table.verticalHeader().setVisible(True)
        self.table.horizontalHeader().setStretchLastSection(True)
        resize_stretch = getattr(getattr(QHeaderView, 'ResizeMode', None), 'Stretch', getattr(QHeaderView, 'Stretch', 1))
        resize_to_contents = getattr(getattr(QHeaderView, 'ResizeMode', None), 'ResizeToContents', getattr(QHeaderView, 'ResizeToContents', 3))
        self.table.horizontalHeader().setSectionResizeMode(0, resize_stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, resize_to_contents)
        self.table.horizontalHeader().setSectionResizeMode(2, resize_to_contents)
        self.table.horizontalHeader().setSectionResizeMode(3, resize_to_contents)
        self.table.doubleClicked.connect(self.handle_add_selected)

        main_layout.addWidget(self.table, 1)

        # Bottom Action Bar
        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(10)

        self.random_btn = QPushButton("🎲 Pick Random Book", self)
        self.random_btn.setToolTip("Pick a random eligible book and select it in the table")
        self.random_btn.clicked.connect(self.handle_pick_random)
        bottom_layout.addWidget(self.random_btn)

        self.quick_random_add_btn = QPushButton("⚡ Add Random Book Now", self)
        self.quick_random_add_btn.setToolTip("Immediately pick and add a random eligible book to the Next list")
        self.quick_random_add_btn.clicked.connect(self.handle_add_random_now)
        bottom_layout.addWidget(self.quick_random_add_btn)

        bottom_layout.addStretch(1)

        self.add_selected_btn = QPushButton("➕ Add Selected to List", self)
        self.add_selected_btn.setDefault(True)
        self.add_selected_btn.setStyleSheet("font-weight: bold;")
        self.add_selected_btn.clicked.connect(self.handle_add_selected)
        bottom_layout.addWidget(self.add_selected_btn)

        self.close_btn = QPushButton("Close", self)
        self.close_btn.clicked.connect(self.accept)
        bottom_layout.addWidget(self.close_btn)

        main_layout.addLayout(bottom_layout)

    def reload_data(self):
        """Fetch eligible books from database and update UI."""
        target_list = get_pref(KEY_TARGET_LIST, DEFAULT_TARGET_LIST)
        actual_target = resolve_list_name(self.db, target_list)
        exclude_read = get_pref(KEY_EXCLUDE_PERCENT_READ, DEFAULT_EXCLUDE_PERCENT_READ)
        col = get_pref(KEY_PERCENT_READ_COLUMN, DEFAULT_PERCENT_READ_COLUMN)
        enforce_series = get_pref(KEY_ENFORCE_SERIES_ORDER, True)
        author_spacing = get_pref(KEY_MIN_AUTHOR_SEPARATION, DEFAULT_MIN_AUTHOR_SEPARATION)
        series_spacing = get_pref(KEY_MIN_SERIES_SEPARATION, DEFAULT_MIN_SERIES_SEPARATION)

        eligible, total, excluded, series_filtered, spacing_filtered = get_eligible_books(
            self.db,
            target_list=actual_target,
            exclude_percent_read=exclude_read,
            percent_read_column=col,
            enforce_series=enforce_series,
            min_author_separation=author_spacing,
            min_series_separation=series_spacing,
        )
        self.all_eligible_books = eligible

        next_order = get_next_order_number(self.db, actual_target)

        spacing_info = f" &nbsp;|&nbsp; Spacing cooldown: {spacing_filtered}" if spacing_filtered > 0 else ""
        self.stats_label.setText(
            f"<b>{len(eligible)}</b> eligible books &nbsp;|&nbsp; "
            f"Library: {total} &nbsp;|&nbsp; "
            f"Excluded: {excluded} (read or in {actual_target}) &nbsp;|&nbsp; "
            f"Series filtered: {series_filtered}"
            f"{spacing_info}"
        )
        self.target_badge_label.setText(
            f"Target: <i>{actual_target}</i> &rarr; Next Order: <b>#{next_order}</b>"
        )
        self.add_selected_btn.setText(f"➕ Add Selected to '{actual_target}' (Order #{next_order})")

        self.filter_table()

    def filter_table(self):
        """Filter table items based on search input query."""
        query = self.search_input.text().strip().lower()
        if not query:
            self.displayed_books = list(self.all_eligible_books)
        else:
            self.displayed_books = [
                b for b in self.all_eligible_books
                if query in b['title'].lower()
                or query in b['author'].lower()
                or (b['series'] and query in b['series'].lower())
                or query in b['tags'].lower()
            ]
        self.populate_table()

    def populate_table(self):
        """Populate QTableWidget with currently filtered books."""
        self.table.setSortingEnabled(False)
        self.table.clearSelection()
        self.table.setCurrentItem(None)
        self.table.setRowCount(len(self.displayed_books))

        for row, book in enumerate(self.displayed_books):
            # Title
            title_item = QTableWidgetItem(book['title'])
            title_item.setData(USER_ROLE, book['id'])
            self.table.setItem(row, 0, title_item)

            # Author
            author_item = QTableWidgetItem(book['author'])
            self.table.setItem(row, 1, author_item)

            # Series
            series_item = QTableWidgetItem(book['series'] or "")
            self.table.setItem(row, 2, series_item)

            # Series index
            s_idx_item = QTableWidgetItem()
            if book['series_index'] is not None:
                s_idx_item.setData(DISPLAY_ROLE, book['series_index'])
            else:
                s_idx_item.setText("")
            s_idx_item.setTextAlignment(ALIGN_CENTER)
            self.table.setItem(row, 3, s_idx_item)

            # Tags
            tags_item = QTableWidgetItem(book['tags'])
            self.table.setItem(row, 4, tags_item)

        self.table.setSortingEnabled(True)

    def get_selected_book_ids(self):
        """Return list of book IDs selected in the table."""
        selected_rows = sorted(set(index.row() for index in self.table.selectedIndexes()))
        ids = []
        for r in selected_rows:
            item = self.table.item(r, 0)
            if item:
                bid = item.data(USER_ROLE)
                if bid is not None:
                    ids.append(bid)
        return ids

    def handle_pick_random(self):
        """Select a random book from currently displayed list and focus it."""
        if not self.displayed_books:
            QMessageBox.information(self, "No Books", "No eligible books to select.")
            return

        rand_idx = random.randrange(len(self.displayed_books))
        chosen_book = self.displayed_books[rand_idx]

        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item and item.data(USER_ROLE) == chosen_book['id']:
                self.table.clearSelection()
                self.table.selectRow(row)
                self.table.scrollToItem(item)
                break

    def handle_add_random_now(self):
        """Pick a random eligible book and immediately add it to target list."""
        if not self.all_eligible_books:
            QMessageBox.information(self, "No Books", "No eligible books available to add.")
            return

        chosen = random.choice(self.all_eligible_books)
        target_list = get_pref(KEY_TARGET_LIST, DEFAULT_TARGET_LIST)
        actual_target = resolve_list_name(self.db, target_list)

        success, added, start_order, err = add_books_to_target_list(
            self.gui, self.db, [chosen['id']], actual_target
        )
        if success:
            series_desc = f" ({chosen['series']} #{chosen['series_index']:g})" if chosen['series'] else ""
            msg = (
                f"Successfully added <b>{chosen['title']}</b>{series_desc} to <b>{actual_target}</b>.<br><br>"
                f"Assigned Order: <b>#{start_order}</b>"
            )
            QMessageBox.information(self, "Book Added", msg)
            self.reload_data()
            self.table.clearSelection()
            self.table.setCurrentItem(None)
            self.books_added_signal.emit([chosen['id']], actual_target)
        else:
            QMessageBox.critical(self, "Error", f"Failed to add book: {err}")

    def handle_add_selected(self):
        """Add all selected books in the table to the target reading list."""
        selected_ids = self.get_selected_book_ids()
        if not selected_ids:
            QMessageBox.information(self, "No Selection", "Please select one or more books from the table first.")
            return

        target_list = get_pref(KEY_TARGET_LIST, DEFAULT_TARGET_LIST)
        actual_target = resolve_list_name(self.db, target_list)
        success, added, start_order, err = add_books_to_target_list(
            self.gui, self.db, selected_ids, actual_target
        )

        if success:
            end_order = start_order + len(added) - 1
            order_desc = f"#{start_order}" if len(added) == 1 else f"#{start_order} through #{end_order}"
            msg = (
                f"Successfully added <b>{len(added)}</b> book(s) to <b>{actual_target}</b>.<br><br>"
                f"Assigned Order: <b>{order_desc}</b>"
            )
            QMessageBox.information(self, "Books Added", msg)
            self.reload_data()
            self.table.clearSelection()
            self.table.setCurrentItem(None)
            self.books_added_signal.emit(added, actual_target)
        else:
            QMessageBox.critical(self, "Error", f"Failed to add books: {err}")

    def open_config(self):
        """Open settings dialog."""
        cfg_dlg = ConfigDialog(self.gui, self)
        if cfg_dlg.exec_():
            self.reload_data()
