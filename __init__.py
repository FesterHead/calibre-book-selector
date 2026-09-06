__license__   = 'MIT'
__copyright__ = '2026, FesterHead'

from calibre.customize import InterfaceActionBase


class CalibreBookSelectorPlugin(InterfaceActionBase):
    name = 'Calibre Book Selector'
    description = (
        'Intelligently select eligible books and series entries to add '
        'to your Reading List queue with automatic order progression.'
    )
    supported_platforms = ['windows', 'osx', 'linux']
    author = 'FesterHead'
    version = (1, 0, 1)
    minimum_calibre_version = (6, 0, 0)

    actual_plugin = 'calibre_plugins.calibre_book_selector.action:BookSelectorAction'

    def is_customizable(self):
        return True

    def config_widget(self):
        try:
            from calibre_plugins.calibre_book_selector.dialogs import ConfigWidget
        except ImportError:
            from dialogs import ConfigWidget
        return ConfigWidget()

    def save_settings(self, config_widget):
        config_widget.save_settings()

    def custom_init(self):
        pass

