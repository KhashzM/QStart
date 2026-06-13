import sys
from PyQt5.QtWidgets import QApplication, QListWidget, QListWidgetItem, QWidget, QVBoxLayout
from PyQt5.QtGui import QIcon, QPixmap, QImage
from PyQt5.QtCore import QByteArray, Qt, QSize
import base64

app = QApplication(sys.argv)

window = QWidget()
window.setWindowTitle("Icon Test")
window.resize(400, 300)

layout = QVBoxLayout(window)

list_widget = QListWidget()
list_widget.setIconSize(QSize(32, 32))
list_widget.setStyleSheet("""
    QListWidget {
        background: rgba(40, 40, 40, 0.9);
        color: white;
    }
    QListWidget::item {
        padding-left: 40px;
        height: 40px;
    }
""")

pixmap = QPixmap(32, 32)
pixmap.fill(Qt.red)
icon = QIcon(pixmap)

item = QListWidgetItem("Test App")
item.setIcon(icon)
list_widget.addItem(item)

layout.addWidget(list_widget)
window.show()

sys.exit(app.exec_())