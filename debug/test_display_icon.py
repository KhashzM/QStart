import sys
import base64
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout
from PyQt5.QtGui import QIcon, QPixmap, QImage
from PyQt5.QtCore import QByteArray

app = QApplication(sys.argv)

window = QWidget()
window.setWindowTitle("Icon Display Test")
window.resize(400, 300)

layout = QVBoxLayout(window)

# Load icon from index
with open('data/app_index.json', 'r', encoding='utf-8') as f:
    import json
    data = json.load(f)
    apps = data['apps']
    
    test_app = next((a for a in apps if a.get('icon_data')), None)
    if test_app:
        icon_data = test_app['icon_data']
        raw = base64.b64decode(icon_data)
        qimg = QImage()
        qimg.loadFromData(QByteArray(raw))
        
        label = QLabel(f"App: {test_app['name']}\nSize: {qimg.width()}x{qimg.height()}")
        layout.addWidget(label)
        
        # Show the icon as a pixmap
        pixmap = QPixmap.fromImage(qimg.scaled(64, 64))
        icon_label = QLabel()
        icon_label.setPixmap(pixmap)
        layout.addWidget(icon_label)
        
        # Also test with QIcon
        icon = QIcon(pixmap)
        print(f"Icon is null: {icon.isNull()}")
    else:
        label = QLabel("No app with icon data found")
        layout.addWidget(label)

window.show()
sys.exit(app.exec_())