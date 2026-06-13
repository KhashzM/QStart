import sys
from PyQt5.QtWidgets import QApplication, QWidget, QListView, QVBoxLayout, QStyle
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QIcon
from PyQt5.QtCore import QSize

app = QApplication(sys.argv)

window = QWidget()
window.setWindowTitle("Standard Icon Test")
window.resize(400, 300)

layout = QVBoxLayout(window)

list_view = QListView()
list_view.setIconSize(QSize(48, 48))
layout.addWidget(list_view)

model = QStandardItemModel()
list_view.setModel(model)

style = app.style()
icon_names = [
    QStyle.SP_FileIcon,
    QStyle.SP_DirHomeIcon,
    QStyle.SP_ComputerIcon,
    QStyle.SP_TrashIcon,
    QStyle.SP_DesktopIcon
]
names = ["文件", "文件夹", "电脑", "回收站", "桌面"]

for icon_name, name in zip(icon_names, names):
    icon = style.standardIcon(icon_name)
    item = QStandardItem(icon, name)
    model.appendRow(item)

window.show()
window.activateWindow()

sys.exit(app.exec_())