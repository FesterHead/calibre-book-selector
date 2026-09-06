from qt.core import QMenu, QMessageBox, QToolButton
from calibre.gui2.actions import InterfaceAction

try:
    from calibre_plugins.calibre_book_selector.config import (
        get_pref,
        KEY_TARGET_LIST,
        KEY_PERCENT_READ_COLUMN,
        KEY_EXCLUDE_PERCENT_READ,
        KEY_ENFORCE_SERIES_ORDER,
        DEFAULT_TARGET_LIST,
    )
    from calibre_plugins.calibre_book_selector.selector import (
        pick_random_eligible_book,
        add_books_to_target_list,
        resolve_list_name,
    )
    from calibre_plugins.calibre_book_selector.dialogs import (
        BookSelectorDialog,
        ConfigDialog,
    )
except ImportError:
    from config import (
        get_pref,
        KEY_TARGET_LIST,
        KEY_PERCENT_READ_COLUMN,
        KEY_EXCLUDE_PERCENT_READ,
        KEY_ENFORCE_SERIES_ORDER,
        DEFAULT_TARGET_LIST,
    )
    from selector import (
        pick_random_eligible_book,
        add_books_to_target_list,
        resolve_list_name,
    )
    from dialogs import (
        BookSelectorDialog,
        ConfigDialog,
    )


class BookSelectorAction(InterfaceAction):
    name = 'Calibre Book Selector'
    action_spec = (
        'Book Selector',
        'images/icon.png',
        'Select and queue eligible books for your reading list',
        None,
    )
    popup_type = getattr(getattr(QToolButton, 'ToolButtonPopupMode', None), 'MenuButtonPopup', getattr(QToolButton, 'MenuButtonPopup', 1))
    action_type = 'current'

    def genesis(self):
        # Set up the main toolbar action button and its popup menu
        icon = get_icons('images/icon.png', 'Book Selector')
        self.qaction.setIcon(icon)
        self.qaction.triggered.connect(self.show_selector_dialog)

        # Build dropdown menu
        self.menu = QMenu(self.gui)
        self.qaction.setMenu(self.menu)

        # 1. Main Dialog Action
        self.selector_menu_action = self.menu.addAction(
            icon,
            'Select Next Book(s)...',
            self.show_selector_dialog
        )

        # 2. Quick Random Book Action
        self.quick_random_action = self.menu.addAction(
            'Add Random Eligible Book to Next Queue',
            self.add_random_book_quick
        )

        self.menu.addSeparator()

        # 3. Settings Action
        self.config_menu_action = self.menu.addAction(
            'Customize Plugin Settings...',
            self.show_config_dialog
        )

    def gui_layout_complete(self):
        pass

    def show_selector_dialog(self):
        """Open the interactive book selector dialog."""
        dlg = BookSelectorDialog(self.gui)
        dlg.books_added_signal.connect(self.on_books_added)
        dlg.exec_()

    def add_random_book_quick(self):
        """1-click quick action to pick and add a random eligible book."""
        db = self.gui.current_db
        target_list = get_pref(KEY_TARGET_LIST, DEFAULT_TARGET_LIST)
        actual_target = resolve_list_name(db, target_list)
        enforce_series = get_pref(KEY_ENFORCE_SERIES_ORDER, True)

        chosen = pick_random_eligible_book(
            db, target_list=actual_target, enforce_series=enforce_series
        )

        if not chosen:
            QMessageBox.information(
                self.gui,
                "No Books Available",
                "No eligible books found in your library matching the current criteria."
            )
            return

        success, added, start_order, err = add_books_to_target_list(
            self.gui, db, [chosen['id']], actual_target
        )

        if success:
            series_desc = f" ({chosen['series']} #{chosen['series_index']:g})" if chosen['series'] else ""
            msg = (
                f"Added <b>{chosen['title']}</b>{series_desc} to <b>{actual_target}</b> at Order <b>#{start_order}</b>."
            )
            if hasattr(self.gui, 'status_bar'):
                self.gui.status_bar.showMessage(
                    f"Book Selector: Added '{chosen['title']}' to {actual_target} (Order #{start_order})", 5000
                )
            QMessageBox.information(self.gui, "Book Added to Queue", msg)
            self.on_books_added([chosen['id']], actual_target)
        else:
            QMessageBox.critical(self.gui, "Error", f"Failed to add book: {err}")

    def show_config_dialog(self):
        """Open the plugin configuration dialog."""
        dlg = ConfigDialog(self.gui)
        dlg.exec_()

    def on_books_added(self, book_ids, target_list):
        """Refresh library view and tags view when books are added."""
        try:
            if hasattr(self.gui, 'library_view'):
                self.gui.library_view.model().refresh_ids(set(book_ids))
            if hasattr(self.gui, 'tags_view'):
                self.gui.tags_view.recount()
        except Exception as e:
            print(f"[CalibreBookSelector] Error refreshing UI: {e}")
