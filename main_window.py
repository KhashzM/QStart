import sys
import os
import subprocess
import base64
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QListView, QLabel
)
from PyQt5.QtGui import QFont, QIcon, QPixmap, QImage, QStandardItemModel, QStandardItem, QColor
from PyQt5.QtCore import Qt, QTimer, QByteArray, pyqtSignal, QSize
from config import WINDOW_WIDTH, WINDOW_HEIGHT, MAX_RESULTS
from searcher import Searcher

DEFAULT_ICONS = {
    ".exe": "📦",
    ".lnk": "🔗",
    ".bat": "📜",
    ".cmd": "📜",
    ".py": "🐍",
    ".js": "📄",
    ".html": "🌐",
}

class MainWindow(QMainWindow):
    toggle_signal = pyqtSignal()
    refresh_signal = pyqtSignal(list)

    def __init__(self, apps):
        super().__init__()
        self.apps = apps
        self.searcher = Searcher(apps)
        self.selected_index = 0
        self.run_hotkey = 'enter'

        self.toggle_signal.connect(self.do_toggle)
        self.refresh_signal.connect(self.do_refresh)

        self.init_ui()
        self.center_window()

    def init_ui(self):
        self.setWindowTitle("QStart")
        self.setFixedSize(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("搜索应用程序...")
        self.search_bar.setFont(QFont("Microsoft YaHei", 14))
        self.search_bar.setStyleSheet("""
            QLineEdit {
                background: rgba(255, 255, 255, 0.95);
                border: 1px solid rgba(200, 200, 200, 0.8);
                border-radius: 8px;
                padding: 10px 15px;
                color: #333;
            }
            QLineEdit:focus {
                border-color: #4A90D9;
                outline: none;
            }
        """)
        self.search_bar.textChanged.connect(self.on_search)
        self.search_bar.returnPressed.connect(self.launch_selected)
        self.search_bar.installEventFilter(self)
        main_layout.addWidget(self.search_bar)

        self.results_view = QListView()
        self.results_view.setIconSize(QSize(32, 32))
        self.results_view.setStyleSheet("""
            QListView {
                background: rgba(255, 255, 255, 0.95);
                border: 1px solid rgba(200, 200, 200, 0.8);
                border-radius: 8px;
                color: #333;
            }
            QListView::item {
                padding: 4px 8px;
                height: 40px;
            }
            QListView::item:hover {
                background: rgba(74, 144, 217, 0.2);
            }
            QListView::item:selected {
                background: rgba(74, 144, 217, 0.3);
            }
        """)
        self.results_view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.results_view.doubleClicked.connect(self.launch_app)
        self.results_view.clicked.connect(self.on_item_click)
        main_layout.addWidget(self.results_view)

        self.footer_layout = QHBoxLayout()
        self.status_label = QLabel(f"共 {len(self.apps)} 个应用")
        self.status_label.setStyleSheet("color: #666; font-size: 12px;")
        self.footer_layout.addWidget(self.status_label)

        self.footer_layout.addStretch()

        main_layout.addLayout(self.footer_layout)

        self.setStyleSheet("""
            QMainWindow {
                background: rgba(245, 245, 245, 0.98);
                border-radius: 12px;
            }
        """)

        self.model = QStandardItemModel()
        self.results_view.setModel(self.model)

        self.results_view.hide()
        self.status_label.hide()

    def center_window(self, window_x=0, window_y=0):
        screen_geo = QApplication.desktop().screenGeometry()
        screen_width = screen_geo.width()
        screen_height = screen_geo.height()
        window_width = self.frameGeometry().width()
        window_height = self.frameGeometry().height()

        if window_x == 0 and window_y == 0:
            x = (screen_width - window_width) // 2
            y = (screen_height - window_height) // 2
        else:
            x = window_x
            y = window_y

        self.move(x, y)

    def set_position(self, window_x, window_y):
        if self.isVisible():
            self.center_window(window_x, window_y)

    def load_icon_from_data(self, icon_data, ext):
        if icon_data:
            try:
                raw = base64.b64decode(icon_data)
                qimg = QImage()
                qimg.loadFromData(QByteArray(raw))
                if not qimg.isNull():
                    pixmap = QPixmap.fromImage(qimg.scaled(32, 32, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                    return QIcon(pixmap)
            except Exception:
                pass

        return self._emoji_icon(DEFAULT_ICONS.get(ext, "📄"))

    def _emoji_icon(self, emoji):
        pixmap = QPixmap(32, 32)
        pixmap.fill(Qt.transparent)
        painter = __import__('PyQt5.QtGui', fromlist=['QPainter']).QPainter(pixmap)
        painter.setPen(__import__('PyQt5.QtGui', fromlist=['QColor']).QColor(255, 255, 255))
        font = __import__('PyQt5.QtGui', fromlist=['QFont']).QFont("Segoe UI Emoji", 20)
        painter.setFont(font)
        painter.drawText(pixmap.rect(), Qt.AlignCenter, emoji)
        painter.end()
        return QIcon(pixmap)

    def on_search(self, query):
        QTimer.singleShot(0, lambda: self.do_search(query))

    def do_search(self, query):
        if not query.strip():
            self.show_results([])
            return

        results = self.searcher.search(query, MAX_RESULTS)
        self.show_results(results)
        self.selected_index = 0
        if self.model.rowCount() > 0:
            self.results_view.setCurrentIndex(self.model.index(0, 0))

    def show_results(self, apps):
        self.model.clear()

        if not apps:
            self.results_view.hide()
            self.status_label.hide()
            return

        for app in apps:
            icon = self.load_icon_from_data(app.get("icon_data"), app.get("extension", ""))
            item = QStandardItem(app["name"])
            item.setIcon(icon)
            item.setData(app, Qt.UserRole)
            self.model.appendRow(item)

        self.results_view.show()
        self.status_label.show()
        self.status_label.setText(f"找到 {len(apps)} 个结果")

    def launch_app(self, index):
        item = self.model.itemFromIndex(index)
        if item:
            app = item.data(Qt.UserRole)
            if app:
                try:
                    path = app["path"]
                    if os.path.isdir(path):
                        subprocess.Popen(f'explorer "{path}"', shell=True)
                    else:
                        subprocess.Popen([path], shell=True)
                    self.hide()
                    self.search_bar.clear()
                except Exception as e:
                    print(f"Failed to launch {app['path']}: {e}")

    def launch_selected(self):
        current_index = self.results_view.currentIndex()
        if current_index.isValid():
            self.launch_app(current_index)

    def on_item_click(self, index):
        self.selected_index = index.row()

    def eventFilter(self, obj, event):
        if obj == self.search_bar:
            if event.type() == event.KeyPress:
                if event.key() == Qt.Key_Down:
                    if self.selected_index < self.model.rowCount() - 1:
                        self.selected_index += 1
                        self.results_view.setCurrentIndex(self.model.index(self.selected_index, 0))
                    return True
                elif event.key() == Qt.Key_Up:
                    if self.selected_index > 0:
                        self.selected_index -= 1
                        self.results_view.setCurrentIndex(self.model.index(self.selected_index, 0))
                    return True
                elif event.key() == Qt.Key_Escape:
                    self.hide()
                    return True
                elif self._matches_run_hotkey(event) and self.model.rowCount() > 0:
                    self.launch_selected()
                    return True
        return super().eventFilter(obj, event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.hide()
        elif self._matches_run_hotkey(event):
            self.launch_selected()
        super().keyPressEvent(event)

    def _matches_run_hotkey(self, event):
        key = event.key()

        if self.run_hotkey == 'enter':
            return key == Qt.Key_Enter or key == Qt.Key_Return
        elif self.run_hotkey == 'space':
            return key == Qt.Key_Space
        elif self.run_hotkey == 'tab':
            return key == Qt.Key_Tab
        elif self.run_hotkey == 'backspace':
            return key == Qt.Key_Backspace
        elif self.run_hotkey == 'delete':
            return key == Qt.Key_Delete
        elif self.run_hotkey.startswith('f') and len(self.run_hotkey) <= 3:
            try:
                f_num = int(self.run_hotkey[1:])
                return key == Qt.Key_F1 + f_num - 1
            except:
                pass
        elif self.run_hotkey.isdigit() and len(self.run_hotkey) == 1:
            return key == Qt.Key_0 + int(self.run_hotkey)
        elif len(self.run_hotkey) == 1 and self.run_hotkey.isalpha():
            return key == getattr(Qt, f'Key_{self.run_hotkey.upper()}')

        return False

    def set_run_hotkey(self, hotkey):
        self.run_hotkey = hotkey

    def showEvent(self, event):
        super().showEvent(event)
        self.activateWindow()

    def set_theme(self, theme):
        if theme == 'dark':
            self.setStyleSheet("""
                QMainWindow {
                    background: rgba(30, 30, 30, 0.98);
                    border-radius: 12px;
                }
            """)
            self.search_bar.setStyleSheet("""
                QLineEdit {
                    background: rgba(40, 40, 40, 0.95);
                    border: 1px solid rgba(80, 80, 80, 0.8);
                    border-radius: 8px;
                    padding: 10px 15px;
                    color: #eee;
                }
                QLineEdit:focus {
                    border-color: #4A90D9;
                    outline: none;
                }
                QLineEdit::placeholder {
                    color: #666;
                }
            """)
            self.results_view.setStyleSheet("""
                QListView {
                    background: rgba(40, 40, 40, 0.95);
                    border: 1px solid rgba(80, 80, 80, 0.8);
                    border-radius: 8px;
                    color: #eee;
                }
                QListView::item {
                    padding: 4px 8px;
                    height: 40px;
                }
                QListView::item:hover {
                    background: rgba(74, 144, 217, 0.2);
                }
                QListView::item:selected {
                    background: rgba(74, 144, 217, 0.3);
                }
            """)
            self.status_label.setStyleSheet("color: #888; font-size: 12px;")
        else:
            self.setStyleSheet("""
                QMainWindow {
                    background: rgba(245, 245, 245, 0.98);
                    border-radius: 12px;
                }
            """)
            self.search_bar.setStyleSheet("""
                QLineEdit {
                    background: rgba(255, 255, 255, 0.95);
                    border: 1px solid rgba(200, 200, 200, 0.8);
                    border-radius: 8px;
                    padding: 10px 15px;
                    color: #333;
                }
                QLineEdit:focus {
                    border-color: #4A90D9;
                    outline: none;
                }
            """)
            self.results_view.setStyleSheet("""
                QListView {
                    background: rgba(255, 255, 255, 0.95);
                    border: 1px solid rgba(200, 200, 200, 0.8);
                    border-radius: 8px;
                    color: #333;
                }
                QListView::item {
                    padding: 4px 8px;
                    height: 40px;
                }
                QListView::item:hover {
                    background: rgba(74, 144, 217, 0.2);
                }
                QListView::item:selected {
                    background: rgba(74, 144, 217, 0.3);
                }
            """)
            self.status_label.setStyleSheet("color: #666; font-size: 12px;")

    def set_opacity(self, opacity):
        self.setWindowOpacity(opacity)
        self.raise_()
        QTimer.singleShot(0, self._set_focus)

    def _set_focus(self):
        self.search_bar.clear()
        self.search_bar.setFocus(Qt.PopupFocusReason)

    def do_toggle(self):
        if self.isVisible():
            self.hide()
        else:
            self.center_window()
            self.show()
            self.activateWindow()
            self.search_bar.setFocus()

    def do_refresh(self, apps):
        self.apps = apps
        self.searcher = Searcher(apps)
        self.status_label.setText(f"共 {len(apps)} 个应用")
        self.show_results(apps[:MAX_RESULTS])
