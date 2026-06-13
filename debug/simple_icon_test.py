import sys
from PyQt5.QtWidgets import QApplication, QWidget, QListView, QVBoxLayout
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QIcon, QPixmap, QColor
from PyQt5.QtCore import Qt, QSize

app = QApplication(sys.argv)

window = QWidget()
window.setWindowTitle("Icon Test")
window.resize(400, 300)

layout = QVBoxLayout(window)

list_view = QListView()
list_view.setIconSize(QSize(48, 48))
layout.addWidget(list_view)

model = QStandardItemModel()
list_view.setModel(model)

colors = [QColor(Qt.red), QColor(Qt.blue), QColor(Qt.green), QColor(Qt.yellow)]
names = ["红色应用", "蓝色应用", "绿色应用", "黄色应用"]

for color, name in zip(colors, names):
    pixmap = QPixmap(48, 48)
    pixmap.fill(color)
    icon = QIcon(pixmap)
    item = QStandardItem(icon, name)
    model.appendRow(item)

window.show()
window.activateWindow()

sys.exit(app.exec_())