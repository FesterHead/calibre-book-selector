from calibre.utils.config import JSONConfig

# Configuration key constants
KEY_TARGET_LIST = 'target_list'
KEY_PERCENT_READ_COLUMN = 'percent_read_column'
KEY_EXCLUDE_PERCENT_READ = 'exclude_percent_read'
KEY_ENFORCE_SERIES_ORDER = 'enforce_series_order'
KEY_MIN_AUTHOR_SEPARATION = 'min_author_separation'
KEY_MIN_SERIES_SEPARATION = 'min_series_separation'
KEY_AUTO_REFRESH_GUI = 'auto_refresh_gui'
KEY_RANDOM_SEED_ON_OPEN = 'random_seed_on_open'
KEY_AUTO_ADD_SERIES_DECIMALS = 'auto_add_series_decimals'

# Default values
DEFAULT_TARGET_LIST = 'Next'
DEFAULT_PERCENT_READ_COLUMN = '#kobo_percent_read'
DEFAULT_EXCLUDE_PERCENT_READ = True
DEFAULT_MIN_AUTHOR_SEPARATION = 6
DEFAULT_MIN_SERIES_SEPARATION = 6
DEFAULT_AUTO_ADD_SERIES_DECIMALS = True

DEFAULT_PREFERENCES = {
    KEY_TARGET_LIST: DEFAULT_TARGET_LIST,
    KEY_PERCENT_READ_COLUMN: DEFAULT_PERCENT_READ_COLUMN,
    KEY_EXCLUDE_PERCENT_READ: DEFAULT_EXCLUDE_PERCENT_READ,
    KEY_ENFORCE_SERIES_ORDER: True,
    KEY_MIN_AUTHOR_SEPARATION: DEFAULT_MIN_AUTHOR_SEPARATION,
    KEY_MIN_SERIES_SEPARATION: DEFAULT_MIN_SERIES_SEPARATION,
    KEY_AUTO_REFRESH_GUI: True,
    KEY_RANDOM_SEED_ON_OPEN: True,
    KEY_AUTO_ADD_SERIES_DECIMALS: DEFAULT_AUTO_ADD_SERIES_DECIMALS,
}

plugin_prefs = JSONConfig('plugins/calibre_book_selector')

def get_pref(key, default=None):
    """Retrieve a preference value with fallback to defaults."""
    if default is None:
        default = DEFAULT_PREFERENCES.get(key)
    return plugin_prefs.get(key, default)

def set_pref(key, value):
    """Save a preference value to persistent config."""
    plugin_prefs[key] = value

def reset_to_defaults():
    """Reset all plugin preferences to standard defaults."""
    for key, val in DEFAULT_PREFERENCES.items():
        plugin_prefs[key] = val
