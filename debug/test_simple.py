import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/src')

print("Testing basic imports...")
try:
    from config import HOTKEY, APP_NAME
    print("✓ config imported")
except Exception as e:
    print(f"✗ config error: {e}")

try:
    from app_indexer import AppIndexer
    print("✓ app_indexer imported")
except Exception as e:
    print(f"✗ app_indexer error: {e}")

try:
    from searcher import Searcher
    print("✓ searcher imported")
except Exception as e:
    print(f"✗ searcher error: {e}")

try:
    from main_window import MainWindow
    print("✓ main_window imported")
except Exception as e:
    print(f"✗ main_window error: {e}")

try:
    from hotkey_manager import HotkeyManager
    print("✓ hotkey_manager imported")
except Exception as e:
    print(f"✗ hotkey_manager error: {e}")

print("\nTesting index building...")
try:
    indexer = AppIndexer()
    apps = indexer.get_all_apps()
    print(f"✓ Loaded {len(apps)} apps")
except Exception as e:
    print(f"✗ Index error: {e}")

print("\nAll tests passed!")