import os
import zipfile
import subprocess
import sys
import json

PLUGIN_ZIP = 'calibre-book-selector.zip'
CALIBRE_CUSTOMIZE = r'E:\Calibre Portable\Calibre\calibre-customize.exe'
CALIBRE_SETTINGS_DIR = r'E:\Calibre Portable\Calibre Settings'
GUI_JSON_PATH = os.path.join(CALIBRE_SETTINGS_DIR, 'gui.json')

FILES_TO_PACKAGE = [
    '__init__.py',
    'action.py',
    'config.py',
    'dialogs.py',
    'selector.py',
    'plugin-import-name-calibre_book_selector.txt',
    'CHANGELOG.md',
    'README.md',
    'about.txt',
    'LICENSE',
    'images/icon.png',
]

def build_zip():
    print(f"Building {PLUGIN_ZIP}...")
    if os.path.exists(PLUGIN_ZIP):
        os.remove(PLUGIN_ZIP)

    with zipfile.ZipFile(PLUGIN_ZIP, 'w', compression=zipfile.ZIP_DEFLATED) as z:
        for item in FILES_TO_PACKAGE:
            if os.path.exists(item):
                z.write(item, arcname=item)
                print(f"  Added: {item}")
            else:
                print(f"  WARNING: Missing {item}")
    print(f"Successfully created {PLUGIN_ZIP} ({os.path.getsize(PLUGIN_ZIP)} bytes)")

def add_to_toolbar():
    """Ensure 'Calibre Book Selector' is placed on the main toolbar in gui.json."""
    if not os.path.exists(GUI_JSON_PATH):
        return
    try:
        with open(GUI_JSON_PATH, 'r', encoding='utf-8') as f:
            gui_cfg = json.load(f)

        toolbar = gui_cfg.get('action-layout-toolbar', [])
        action_name = 'Calibre Book Selector'
        if action_name not in toolbar:
            # Insert right after 'Reading List' if present, otherwise append
            if 'Reading List' in toolbar:
                idx = toolbar.index('Reading List') + 1
                toolbar.insert(idx, action_name)
            else:
                toolbar.append(action_name)

            gui_cfg['action-layout-toolbar'] = toolbar
            with open(GUI_JSON_PATH, 'w', encoding='utf-8') as f:
                json.dump(gui_cfg, f, indent=2)
            print(f"Added '{action_name}' to main toolbar in {GUI_JSON_PATH}")
    except Exception as e:
        print(f"Notice: Could not auto-add to toolbar layout: {e}")

def install_plugin():
    if os.path.exists(CALIBRE_CUSTOMIZE):
        print(f"\nInstalling plugin to {CALIBRE_SETTINGS_DIR}...")
        env = os.environ.copy()
        env['CALIBRE_CONFIG_DIRECTORY'] = CALIBRE_SETTINGS_DIR

        res = subprocess.run([CALIBRE_CUSTOMIZE, '-a', PLUGIN_ZIP], env=env, capture_output=True, text=True)
        print(res.stdout)
        if res.stderr:
            print("STDERR:", res.stderr)

        add_to_toolbar()
        return res.returncode == 0
    else:
        print(f"Calibre customize tool not found at {CALIBRE_CUSTOMIZE}")
        return False

if __name__ == '__main__':
    build_zip()
    if '--install' in sys.argv or '-i' in sys.argv:
        install_plugin()
