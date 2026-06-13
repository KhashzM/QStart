import sys
from PyQt5.QtWidgets import QApplication, QWidget, QListView, QVBoxLayout, QLineEdit
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QIcon, QPixmap, QColor
from PyQt5.QtCore import Qt, QSize

app = QApplication(sys.argv)

window = QWidget()
window.setWindowTitle("ListView Icon Test")
window.resize(400, 300)

layout = QVBoxLayout(window)

search_bar = QLineEdit()
search_bar.setPlaceholderText("Search...")
layout.addWidget(search_bar)

list_view = QListView()
list_view.setIconSize(QSize(32, 32))
layout.addWidget(list_view)

model = QStandardItemModel()
list_view.setModel(model)

# Create simple color icons
colors = [QColor(Qt.red), QColor(Qt.blue), QColor(Qt.green), QColor(Qt.yellow), QColor(255, 165, 0)]
names = ["App 1", "App 2", "App 3", "App 4", "App 5"]

for i, (color, name) in enumerate(zip(colors, names)):
    pixmap = QPixmap(32, 32)
    pixmap.fill(color)
    icon = QIcon(pixmap)
    item = QStandardItem(icon, name)
    model.appendRow(item)

window.show()
sys.exit(app.exec_())