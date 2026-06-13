import json
import base64
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QImage, QPixmap, QIcon
from PyQt5.QtCore import QByteArray

app = QApplication([])

with open('data/app_index.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
apps = data['apps']

test_apps = [a for a in apps if a.get('icon_data')][:3]

for i, app_data in enumerate(test_apps):
    print(f"\nApp {i+1}: {app_data['name']}")
    icon_data = app_data['icon_data']
    print(f"Icon data length: {len(icon_data)}")
    
    try:
        raw = base64.b64decode(icon_data)
        print(f"Decoded bytes: {len(raw)}")
        
        qimg = QImage()
        qimg.loadFromData(QByteArray(raw))
        print(f"Image null: {qimg.isNull()}")
        if not qimg.isNull():
            print(f"Image size: {qimg.width()}x{qimg.height()}")
            pixmap = QPixmap.fromImage(qimg.scaled(24, 24))
            icon = QIcon(pixmap)
            print("Icon created successfully")
    except Exception as e:
        print(f"Error: {e}")