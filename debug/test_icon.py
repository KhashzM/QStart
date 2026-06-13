import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

import json
from PyQt5.QtWidgets import QApplication
app = QApplication(sys.argv)

from app_indexer import AppIndexer
indexer = AppIndexer()
indexer.load_index()
apps = indexer.apps

if apps:
    test_app = None
    for a in apps:
        if a["extension"] == ".exe":
            test_app = a
            break
    
    if not test_app:
        test_app = apps[0]
    
    print(f"Testing icon extraction for: {test_app['name']}")
    print(f"Path: {test_app['path']}")
    
    icon_data = indexer.extract_icon_simple(test_app["path"])
    if icon_data:
        print(f"Success! Icon data length: {len(icon_data)}")
    else:
        print("Failed to extract icon with extract_icon_simple")
        
    icon_data2 = indexer.extract_icon_base64(test_app["path"])
    if icon_data2:
        print(f"Success with base64 method! Icon data length: {len(icon_data2)}")
    else:
        print("Failed to extract icon with extract_icon_base64")
else:
    print("No apps found")