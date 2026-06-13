import base64

from PyQt5.QtCore import QByteArray, QSize, Qt
from PyQt5.QtGui import QFont, QIcon, QImage, QPainter, QPixmap
from PyQt5.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from app_icon import load_app_icon


DEFAULT_ICONS = {
    ".exe": "🚀",
    ".lnk": "🔗",
    ".bat": "📜",
    ".cmd": "📜",
    ".py": "🐍",
    ".js": "🟨",
    ".html": "🌐",
}

MAX_PINNED_APPS = 7


class PinnedAppsDialog(QDialog):
    def __init__(self, available_apps, pinned_items, parent=None):
        super().__init__(parent)
        self.available_apps = sorted(available_apps, key=lambda app: app["name"].lower())
        self.selected_apps = []
        self.selected_paths = set()
        self.app_icon = load_app_icon()

        self.setWindowTitle("管理固定快捷方式")
        if self.app_icon:
            self.setWindowIcon(self.app_icon)
        self.setFixedSize(620, 700)
        self.setStyleSheet(
            """
            QDialog {
                background: #f5f5f5;
            }
            QLabel {
                color: #555;
            }
            QLineEdit, QListWidget {
                background: white;
                border: 1px solid #d8d8d8;
                border-radius: 8px;
            }
            QListWidget::item:selected {
                background: #e8f2ff;
                color: #1f4e79;
            }
            QPushButton {
                background: #4A90D9;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 6px 16px;
                min-width: 80px;
            }
            QPushButton:hover {
                background: #3A80C9;
            }
            QPushButton:pressed {
                background: #2A70B9;
            }
            """
        )

        self._init_ui()
        self._load_pinned_items(pinned_items)
        self._refresh_available_list()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        title = QLabel("点击下方列表添加固定软件，点击上方已固定的软件可移除")
        title.setStyleSheet("font-size: 13px; color: #666;")
        layout.addWidget(title)

        selected_label = QLabel(f"已固定软件（最多 {MAX_PINNED_APPS} 个）")
        selected_label.setStyleSheet("font-weight: bold; color: #333;")
        layout.addWidget(selected_label)

        self.selected_list = QListWidget()
        self.selected_list.setViewMode(QListWidget.IconMode)
        self.selected_list.setFlow(QListWidget.LeftToRight)
        self.selected_list.setWrapping(False)
        self.selected_list.setResizeMode(QListWidget.Adjust)
        self.selected_list.setIconSize(QSize(32, 32))
        self.selected_list.setGridSize(QSize(96, 82))
        self.selected_list.setWordWrap(True)
        self.selected_list.setSpacing(4)
        self.selected_list.setMinimumHeight(94)
        self.selected_list.setMaximumHeight(94)
        self.selected_list.itemClicked.connect(self._remove_selected_item)
        layout.addWidget(self.selected_list)

        search_label = QLabel("已检索到的软件")
        search_label.setStyleSheet("font-weight: bold; color: #333;")
        layout.addWidget(search_label)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("输入名称筛选可添加的软件...")
        self.search_input.textChanged.connect(self._refresh_available_list)
        layout.addWidget(self.search_input)

        self.available_list = QListWidget()
        self.available_list.setIconSize(QSize(24, 24))
        self.available_list.itemClicked.connect(self._toggle_available_item)
        layout.addWidget(self.available_list)

        footer_layout = QHBoxLayout()
        footer_layout.addStretch()
        self.clear_button = QPushButton("清空固定")
        self.clear_button.clicked.connect(self._clear_selected)
        footer_layout.addWidget(self.clear_button)
        self.ok_button = QPushButton("确定")
        self.ok_button.clicked.connect(self.accept)
        footer_layout.addWidget(self.ok_button)
        self.cancel_button = QPushButton("取消")
        self.cancel_button.clicked.connect(self.reject)
        footer_layout.addWidget(self.cancel_button)
        layout.addLayout(footer_layout)

    def _load_pinned_items(self, pinned_items):
        pinned_by_path = {item["path"].lower(): item for item in self.available_apps}

        for item in pinned_items:
            app = pinned_by_path.get(item["path"].lower())
            if app is None:
                app = item
            self._append_selected_app(app)

    def _append_selected_app(self, app):
        normalized_path = app["path"].lower()
        if normalized_path in self.selected_paths:
            return

        self.selected_paths.add(normalized_path)
        self.selected_apps.append(app)
        self._refresh_selected_list()

    def _refresh_selected_list(self):
        self.selected_list.clear()
        for app in self.selected_apps:
            item = QListWidgetItem(self.load_icon_from_data(app.get("icon_data"), app.get("extension", "")), app["name"])
            item.setToolTip(app["name"])
            item.setTextAlignment(Qt.AlignHCenter | Qt.AlignTop)
            item.setData(Qt.UserRole, app)
            self.selected_list.addItem(item)

    def _refresh_available_list(self):
        query = self.search_input.text().strip().lower()
        self.available_list.clear()

        for app in self.available_apps:
            if query and query not in app["name"].lower():
                continue

            item = QListWidgetItem(self.load_icon_from_data(app.get("icon_data"), app.get("extension", "")), app["name"])
            item.setToolTip(app["path"])
            item.setData(Qt.UserRole, app)

            if app["path"].lower() in self.selected_paths:
                item.setText(f"{app['name']}  [已固定]")

            self.available_list.addItem(item)

    def _toggle_available_item(self, item):
        app = item.data(Qt.UserRole)
        normalized_path = app["path"].lower()

        if normalized_path in self.selected_paths:
            self.selected_apps = [entry for entry in self.selected_apps if entry["path"].lower() != normalized_path]
            self.selected_paths.remove(normalized_path)
        else:
            if len(self.selected_apps) >= MAX_PINNED_APPS:
                QMessageBox.information(self, "数量已满", f"固定快捷方式最多只能添加 {MAX_PINNED_APPS} 个。")
                return
            self.selected_apps.append(app)
            self.selected_paths.add(normalized_path)

        self._refresh_selected_list()
        self._refresh_available_list()

    def _remove_selected_item(self, item):
        app = item.data(Qt.UserRole)
        normalized_path = app["path"].lower()
        self.selected_apps = [entry for entry in self.selected_apps if entry["path"].lower() != normalized_path]
        if normalized_path in self.selected_paths:
            self.selected_paths.remove(normalized_path)
        self._refresh_selected_list()
        self._refresh_available_list()

    def _clear_selected(self):
        self.selected_apps = []
        self.selected_paths.clear()
        self._refresh_selected_list()
        self._refresh_available_list()

    def get_selected_items(self):
        return [{"name": app["name"], "path": app["path"]} for app in self.selected_apps]

    def load_icon_from_data(self, icon_data, ext):
        if icon_data:
            try:
                raw = base64.b64decode(icon_data)
                qimg = QImage()
                qimg.loadFromData(QByteArray(raw))
                if not qimg.isNull():
                    pixmap = QPixmap.fromImage(
                        qimg.scaled(32, 32, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    )
                    return QIcon(pixmap)
            except Exception:
                pass

        return self._emoji_icon(DEFAULT_ICONS.get(ext, "📄"))

    def _emoji_icon(self, emoji):
        pixmap = QPixmap(32, 32)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setFont(QFont("Segoe UI Emoji", 20))
        painter.drawText(pixmap.rect(), Qt.AlignCenter, emoji)
        painter.end()
        return QIcon(pixmap)
