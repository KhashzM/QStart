import sys
sys.path.insert(0, 'src')

from PyQt5.QtWidgets import QApplication, QFileIconProvider
from PyQt5.QtCore import QFileInfo, QByteArray, QBuffer, QIODevice
from PyQt5.QtGui import QPixmap, QImage, QIcon
import base64
import json

app = QApplication(sys.argv)

with open('data/app_index.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
apps = data['apps']

print(f"Total apps: {len(apps)}")

has_icon = sum(1 for a in apps if a.get('icon_data'))
print(f"Apps with icon data: {has_icon}")

if has_icon > 0:
    test_app = next((a for a in apps if a.get('icon_data')), None)
    print(f"\nTesting app: {test_app['name']}")
    print(f"Icon data length: {len(test_app['icon_data'])}")
    
    try:
        raw = base64.b64decode(test_app['icon_data'])
        print(f"Decoded bytes: {len(raw)}")
        
        qimg = QImage()
        qimg.loadFromData(QByteArray(raw))
        print(f"Image null: {qimg.isNull()}")
        if not qimg.isNull():
            print(f"Image size: {qimg.width()}x{qimg.height()}")
            print(f"Image format: {qimg.format()}")
            
            pixmap = QPixmap.fromImage(qimg)
            print(f"Pixmap null: {pixmap.isNull()}")
            
            icon = QIcon(pixmap)
            print(f"Icon null: {icon.isNull()}")
    except Exception as e:
        print(f"Error: {e}")

print("\n--- Testing QFileIconProvider directly ---")
if apps:
    test_path = apps[0]['path']
    if test_path.lower().endswith('.lnk'):
        print(f"Path is .lnk, skipping")
    else:
        provider = QFileIconProvider()
        file_info = QFileInfo(test_path)
        icon = provider.icon(file_info)
        print(f"Icon null from provider: {icon.isNull()}")
        
        if not icon.isNull():
            pixmap = icon.pixmap(32, 32)
            print(f"Pixmap null: {pixmap.isNull()}")
            if not pixmap.isNull():
                ba = QByteArray()
                buf = QBuffer(ba)
                buf.open(QIODevice.WriteOnly)
                saved = pixmap.save(buf, "PNG")
                buf.close()
                print(f"Saved successfully: {saved}")
                print(f"PNG data length: {ba.size()}")