import base64
import os
import subprocess

from PyQt5.QtCore import QByteArray, QSize, Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QFont, QIcon, QImage, QPainter, QPixmap, QStandardItem, QStandardItemModel
from PyQt5.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListView,
    QMainWindow,
    QSizePolicy,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from config import MAX_RESULTS, WINDOW_HEIGHT, WINDOW_WIDTH
from searcher import Searcher

DEFAULT_ICONS = {
    ".exe": "🚀",
    ".lnk": "🔗",
    ".bat": "📜",
    ".cmd": "📜",
    ".py": "🐍",
    ".js": "🟨",
    ".html": "🌐",
}

PINNED_ROW_LIMIT = 7
PINNED_BUTTON_WIDTH = 70
PINNED_BUTTON_HEIGHT = 72
PINNED_PANEL_HEIGHT = 84


class MainWindow(QMainWindow):
    toggle_signal = pyqtSignal()
    refresh_signal = pyqtSignal(list)

    def __init__(self, apps, plugin_manager=None):
        super().__init__()
        self.apps = apps
        self.searcher = Searcher(apps)
        self.plugin_manager = plugin_manager
        self.pinned_apps = []
        self.is_pinned_mode = False
        self.is_plugin_mode = False
        self.is_plugin_action_mode = False  # 当前是否处于插件动作模式
        self.current_action_plugin = None   # 当前动作模式的插件实例
        self.current_action_context = None  # 当前动作模式的上下文
        self.selected_index = 0
        self.run_hotkey = "enter"
        self.window_x = 0
        self.window_y = 0
        self.current_theme = "light"

        self.toggle_signal.connect(self.do_toggle)
        self.refresh_signal.connect(self.do_refresh)

        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("QStart")
        self.expanded_height = WINDOW_HEIGHT
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        main_layout.setAlignment(Qt.AlignTop)

        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("搜索应用、文件夹或快捷方式...")
        self.search_bar.setFont(QFont("Microsoft YaHei", 14))
        self.search_bar.setMinimumHeight(48)
        self.search_bar.textChanged.connect(self.on_search)
        self.search_bar.returnPressed.connect(self.launch_selected)
        self.search_bar.installEventFilter(self)
        main_layout.addWidget(self.search_bar)

        self.pinned_panel = QWidget()
        self.pinned_panel.setFixedHeight(PINNED_PANEL_HEIGHT)
        self.pinned_layout = QHBoxLayout(self.pinned_panel)
        self.pinned_layout.setContentsMargins(6, 4, 6, 4)
        self.pinned_layout.setSpacing(6)
        main_layout.addWidget(self.pinned_panel)

        self.results_view = QListView()
        self.results_view.setIconSize(QSize(32, 32))
        self.results_view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.results_view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.results_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.results_view.doubleClicked.connect(self.launch_app)
        self.results_view.clicked.connect(self.on_item_click)
        main_layout.addWidget(self.results_view)

        footer_layout = QHBoxLayout()
        self.status_label = QLabel()
        footer_layout.addWidget(self.status_label)
        footer_layout.addStretch()
        main_layout.addLayout(footer_layout)

        self.model = QStandardItemModel()
        self.results_view.setModel(self.model)

        self.set_theme("light")
        self.compact_height = (
            main_layout.contentsMargins().top()
            + self.search_bar.minimumSizeHint().height()
            + main_layout.contentsMargins().bottom()
        )
        self._set_search_results_mode()
        self._set_window_height(self.compact_height)
        self.status_label.setText(f"共 {len(self.apps)} 个应用")
        self.results_view.hide()
        self.pinned_panel.hide()
        self.status_label.hide()

    def center_window(self, window_x=0, window_y=0):
        if window_x != 0 or window_y != 0:
            self.window_x = window_x
            self.window_y = window_y

        screen_geo = QApplication.desktop().screenGeometry()
        window_width = self.frameGeometry().width()
        window_height = self.frameGeometry().height()

        if self.window_x == 0 and self.window_y == 0:
            x = (screen_geo.width() - window_width) // 2
            y = (screen_geo.height() - window_height) // 2
        else:
            x = self.window_x
            y = self.window_y

        self.move(x, y)

    def set_position(self, window_x, window_y):
        self.window_x = window_x
        self.window_y = window_y
        if self.isVisible():
            self.center_window()

    def set_pinned_apps(self, pinned_apps):
        self.pinned_apps = pinned_apps[:PINNED_ROW_LIMIT]
        self._rebuild_pinned_buttons()
        if not self.search_bar.text().strip():
            self.show_pinned_apps()

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

    def on_search(self, query):
        QTimer.singleShot(0, lambda: self.do_search(query))

    def do_search(self, query):
        if not query.strip():
            self.show_pinned_apps()
            return

        # 优先检查插件关键词路由
        if self.plugin_manager:
            plugin = self.plugin_manager.route(query)
            if plugin:
                parts = query.strip().split(None, 1)
                kw = parts[0].lower() if parts else ""
                args = parts[1] if len(parts) > 1 else ""
                context = {"keyword": kw}

                if plugin.trigger_mode == "action":
                    # 动作模式：只显示预览，不执行。按回车由 launch_selected 触发。
                    self.is_plugin_action_mode = True
                    self.current_action_plugin = plugin
                    self.current_action_context = context
                    preview_text = plugin.preview(args)
                    if preview_text:
                        self.show_plugin_preview(preview_text, plugin.name, args)
                    else:
                        self.show_plugin_preview(f"按回车执行: {plugin.name}", plugin.name, args)
                    return
                else:
                    # 实时模式：立即执行 handle()
                    self.is_plugin_action_mode = False
                    self.current_action_plugin = None
                    self.current_action_context = None
                    result = self.plugin_manager.handle(plugin, args, context=context)
                    self.show_plugin_result(result, plugin.name)
                    return

        # 普通应用搜索（返回的是已排好序的结果）
        all_results = self.searcher.search(query, MAX_RESULTS)

        # 将结果分为精确匹配和模糊匹配两组
        exact_results = []
        fuzzy_results = []
        q_normalized = self.searcher._normalize(query) if hasattr(self.searcher, '_normalize') else query.lower()
        for app in all_results:
            name_normalized = self.searcher._normalize(app["name"]) if hasattr(self.searcher, '_normalize') else app["name"].lower()
            # 精确匹配：名称包含查询词 或 名称以查询词开头
            if q_normalized and (q_normalized in name_normalized or name_normalized.startswith(q_normalized)):
                exact_results.append(app)
            else:
                fuzzy_results.append(app)

        # 组装最终结果：精确匹配 → AI 问答 → 模糊匹配
        final_results = exact_results[:]

        # 插入 AI 问答条目（在精确匹配和模糊匹配之间）
        ai_results = []
        if self.plugin_manager:
            ai_plugin = self.plugin_manager.get_plugin("AI 问答")
            if ai_plugin and self.plugin_manager.is_enabled("AI 问答"):
                ai_results = ai_plugin.get_ai_search_results(query)

        final_results.extend(ai_results)
        final_results.extend(fuzzy_results)

        # 将其他插件的全局搜索结果追加到末尾
        if self.plugin_manager:
            other_plugin_results = self.plugin_manager.search_all(query)
            # 过滤掉 AI 问答插件的结果（已单独处理）
            other_plugin_results = [r for r in other_plugin_results if r.get("source") != "ai_qa"]
            final_results.extend(other_plugin_results)

        self.show_results(final_results)
        self.selected_index = 0
        if self.model.rowCount() > 0:
            self.results_view.setCurrentIndex(self.model.index(0, 0))

    def show_pinned_apps(self):
        old_pos = self.pos()
        self.model.clear()

        if not self.pinned_apps:
            self.results_view.hide()
            self.pinned_panel.hide()
            self.status_label.hide()
            self.is_pinned_mode = False
            self._set_window_height(self.compact_height)
            self.move(old_pos)
            return

        self.is_pinned_mode = True
        self.results_view.hide()
        self.pinned_panel.show()
        self.status_label.show()
        self.status_label.hide()
        self.status_label.setText("固定快捷方式")
        self._set_window_height(self.compact_height + PINNED_PANEL_HEIGHT + 24)
        self.move(old_pos)

    def show_plugin_preview(self, preview_text, plugin_name, args):
        """显示动作模式的预览提示"""
        old_pos = self.pos()
        self.is_pinned_mode = False
        self.is_plugin_mode = True
        self.model.clear()

        # 创建一个预览条目，按回车可触发执行
        item = QStandardItem(f"▶ {preview_text}")
        item.setIcon(self._emoji_icon("▶️"))
        action_data = {
            "name": f"[{plugin_name}] {preview_text}",
            "path": f"plugin_action:{plugin_name}",
            "extension": ".plugin",
            "_is_plugin_action": True,
        }
        item.setData(action_data, Qt.UserRole)
        self.model.appendRow(item)

        self.pinned_panel.hide()
        self.results_view.show()
        # 临时降低 results_view 的最小高度，避免撑大窗口
        self.results_view.setMinimumHeight(44)
        self.status_label.show()
        self.status_label.setText(f"[{plugin_name}] 按回车执行")
        self._set_window_height(self.compact_height + 44 + 24 + 10)
        self.selected_index = 0
        self.results_view.setCurrentIndex(self.model.index(0, 0))
        self.move(old_pos)

    def execute_current_plugin_action(self):
        """执行当前动作模式插件的 handle()"""
        if not self.current_action_plugin:
            return

        query = self.search_bar.text().strip()
        parts = query.split(None, 1)
        args = parts[1] if len(parts) > 1 else ""

        result = self.plugin_manager.handle(
            self.current_action_plugin, args, context=self.current_action_context
        )
        self.show_plugin_result(result, self.current_action_plugin.name)

        # 清理状态
        self.is_plugin_action_mode = False
        self.current_action_plugin = None
        self.current_action_context = None

    def show_plugin_result(self, result, plugin_name):
        """显示插件处理结果"""
        old_pos = self.pos()
        self.is_pinned_mode = False
        self.is_plugin_mode = True
        self.model.clear()

        message = result.get("message", "")
        result_type = result.get("type", "none")
        hide_window = result.get("hide_window", False)

        if hide_window:
            self.hide()
            return

        if result_type == "results":
            # 插件返回了一组可选结果
            items = result.get("data", [])
            for item_data in items:
                name = item_data.get("name", "未命名")
                std = QStandardItem(name)
                icon_str = item_data.get("icon", "📄")
                std.setIcon(self._emoji_icon(icon_str))
                std.setData(item_data, Qt.UserRole)
                self.model.appendRow(std)

            self.pinned_panel.hide()
            self.results_view.show()
            # 根据结果数量调整高度
            row_count = len(items)
            row_height = 40
            list_height = min(row_count * row_height, 300)
            self.results_view.setMinimumHeight(max(list_height, 44))
            self.status_label.show()
            self.status_label.setText(f"[{plugin_name}] {message}" if message else f"[{plugin_name}]")
            total_height = self.compact_height + list_height + 24 + 10
            self._set_window_height(min(total_height, self.expanded_height))
        else:
            # display / launch / none - 显示消息文本
            self.results_view.hide()
            self.pinned_panel.hide()
            self.status_label.show()
            self.status_label.setText(f"[{plugin_name}] {message}" if message else f"[{plugin_name}]")
            self._set_window_height(self.compact_height + 24 + 10)

        self.move(old_pos)

    def show_results(self, apps):
        self.is_pinned_mode = False
        self.is_plugin_mode = False
        self._set_search_results_mode()
        # 恢复 results_view 的默认最小高度
        self.results_view.setMinimumHeight(300)
        self.model.clear()

        if not apps:
            self.results_view.hide()
            self.pinned_panel.hide()
            self.status_label.hide()
            self._set_window_height(self.compact_height)
            return

        for app in apps:
            item = QStandardItem(app["name"])
            item.setIcon(self.load_icon_from_data(app.get("icon_data"), app.get("extension", "")))
            item.setData(app, Qt.UserRole)
            self.model.appendRow(item)

        self.pinned_panel.hide()
        self.results_view.show()
        self.status_label.show()
        self.status_label.hide()
        self.status_label.setText(f"找到 {len(apps)} 个结果")
        self._set_window_height(self.expanded_height)

    def _set_window_height(self, height):
        current_pos = self.pos()
        self.setFixedSize(WINDOW_WIDTH, height)
        if self.isVisible():
            self.move(current_pos)

    def _set_search_results_mode(self):
        self.results_view.setViewMode(QListView.ListMode)
        self.results_view.setFlow(QListView.TopToBottom)
        self.results_view.setWrapping(False)
        self.results_view.setMovement(QListView.Static)
        self.results_view.setResizeMode(QListView.Fixed)
        self.results_view.setGridSize(QSize())
        self.results_view.setSpacing(0)
        self.results_view.setMinimumHeight(300)
        self.results_view.setMaximumHeight(16777215)

    def _rebuild_pinned_buttons(self):
        while self.pinned_layout.count():
            item = self.pinned_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        for app in self.pinned_apps:
            button = QToolButton()
            button.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
            button.setIcon(self.load_icon_from_data(app.get("icon_data"), app.get("extension", "")))
            button.setIconSize(QSize(32, 32))
            button.setText(app["name"])
            button.setToolTip(app["name"])
            button.setFixedSize(PINNED_BUTTON_WIDTH, PINNED_BUTTON_HEIGHT)
            button.setAutoRaise(False)
            button.clicked.connect(lambda checked=False, current_app=app: self.launch_app_by_data(current_app))
            self.pinned_layout.addWidget(button)

        while self.pinned_layout.count() < PINNED_ROW_LIMIT:
            spacer = QWidget()
            spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            spacer.setObjectName("pinned-spacer")
            self.pinned_layout.addWidget(spacer)

        self._apply_pinned_button_style()

    def _apply_pinned_button_style(self):
        if self.current_theme == "dark":
            button_style = """
                QToolButton {
                    background: rgba(40, 40, 40, 0.95);
                    border: 1px solid rgba(80, 80, 80, 0.8);
                    border-radius: 10px;
                    color: #eee;
                    padding: 3px 4px 1px 4px;
                    font-size: 11px;
                    qproperty-toolButtonStyle: ToolButtonTextUnderIcon;
                }
                QToolButton::menu-indicator {
                    image: none;
                }
                QToolButton:hover {
                    background: rgba(74, 144, 217, 0.18);
                    border-color: rgba(74, 144, 217, 0.45);
                }
                QToolButton:pressed {
                    background: rgba(74, 144, 217, 0.28);
                }
            """
            panel_style = """
                QWidget {
                    background: rgba(40, 40, 40, 0.95);
                    border: 1px solid rgba(80, 80, 80, 0.8);
                    border-radius: 8px;
                }
                QWidget#pinned-spacer {
                    background: transparent;
                    border: none;
                }
            """
        else:
            button_style = """
                QToolButton {
                    background: rgba(255, 255, 255, 0.95);
                    border: 1px solid rgba(200, 200, 200, 0.8);
                    border-radius: 10px;
                    color: #333;
                    padding: 3px 4px 1px 4px;
                    font-size: 11px;
                    qproperty-toolButtonStyle: ToolButtonTextUnderIcon;
                }
                QToolButton::menu-indicator {
                    image: none;
                }
                QToolButton:hover {
                    background: rgba(74, 144, 217, 0.12);
                    border-color: rgba(74, 144, 217, 0.45);
                }
                QToolButton:pressed {
                    background: rgba(74, 144, 217, 0.22);
                }
            """
            panel_style = """
                QWidget {
                    background: rgba(255, 255, 255, 0.95);
                    border: 1px solid rgba(200, 200, 200, 0.8);
                    border-radius: 8px;
                }
                QWidget#pinned-spacer {
                    background: transparent;
                    border: none;
                }
            """

        self.pinned_panel.setStyleSheet(panel_style)
        for index in range(self.pinned_layout.count()):
            widget = self.pinned_layout.itemAt(index).widget()
            if isinstance(widget, QToolButton):
                widget.setStyleSheet(button_style)

    def launch_app_by_data(self, app):
        # 检查是否是插件结果（含 action 回调）
        action = app.get("action") if isinstance(app, dict) else None
        if callable(action):
            try:
                action()
            except Exception as exc:
                print(f"Plugin action failed: {exc}")
            self.hide()
            self.search_bar.clear()
            return

        try:
            path = app.get("path", "") if isinstance(app, dict) else ""
            if not path:
                return
            if os.path.isdir(path):
                subprocess.Popen(f'explorer "{path}"', shell=True)
            else:
                subprocess.Popen([path], shell=True)
            self.hide()
            self.search_bar.clear()
        except Exception as exc:
            print(f"Failed to launch {app.get('path', '?')}: {exc}")

    def launch_app(self, index):
        item = self.model.itemFromIndex(index)
        if item is None:
            return

        app = item.data(Qt.UserRole)
        if not app:
            return

        self.launch_app_by_data(app)

    def launch_selected(self):
        # 如果当前处于插件动作模式，按回车执行插件
        if self.is_plugin_action_mode and self.current_action_plugin:
            self.execute_current_plugin_action()
            return

        current_index = self.results_view.currentIndex()
        if current_index.isValid():
            self.launch_app(current_index)

    def on_item_click(self, index):
        self.selected_index = index.row()

    def eventFilter(self, obj, event):
        if obj == self.search_bar and event.type() == event.KeyPress:
            if event.key() == Qt.Key_Down and not self.is_pinned_mode:
                if self.selected_index < self.model.rowCount() - 1:
                    self.selected_index += 1
                    self.results_view.setCurrentIndex(self.model.index(self.selected_index, 0))
                return True

            if event.key() == Qt.Key_Up and not self.is_pinned_mode:
                if self.selected_index > 0:
                    self.selected_index -= 1
                    self.results_view.setCurrentIndex(self.model.index(self.selected_index, 0))
                return True

            if event.key() == Qt.Key_Escape:
                self.hide()
                return True

            if self._matches_run_hotkey(event) and self.model.rowCount() > 0 and not self.is_pinned_mode:
                self.launch_selected()
                return True

        return super().eventFilter(obj, event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.hide()
        elif self._matches_run_hotkey(event) and not self.is_pinned_mode:
            self.launch_selected()
        super().keyPressEvent(event)

    def _matches_run_hotkey(self, event):
        key = event.key()

        if self.run_hotkey == "enter":
            return key in (Qt.Key_Enter, Qt.Key_Return)
        if self.run_hotkey == "space":
            return key == Qt.Key_Space
        if self.run_hotkey == "tab":
            return key == Qt.Key_Tab
        if self.run_hotkey == "backspace":
            return key == Qt.Key_Backspace
        if self.run_hotkey == "delete":
            return key == Qt.Key_Delete
        if self.run_hotkey.startswith("f") and len(self.run_hotkey) <= 3:
            try:
                f_num = int(self.run_hotkey[1:])
                return key == Qt.Key_F1 + f_num - 1
            except ValueError:
                return False
        if self.run_hotkey.isdigit() and len(self.run_hotkey) == 1:
            return key == Qt.Key_0 + int(self.run_hotkey)
        if len(self.run_hotkey) == 1 and self.run_hotkey.isalpha():
            return key == getattr(Qt, f"Key_{self.run_hotkey.upper()}")

        return False

    def set_run_hotkey(self, hotkey):
        self.run_hotkey = hotkey

    def showEvent(self, event):
        super().showEvent(event)
        self.activateWindow()
        if self.window_x != 0 or self.window_y != 0:
            self.move(self.window_x, self.window_y)

    def resizeEvent(self, event):
        old_pos = self.pos()
        super().resizeEvent(event)
        self.move(old_pos)

    def changeEvent(self, event):
        old_pos = self.pos()
        super().changeEvent(event)
        self.move(old_pos)

    def set_theme(self, theme):
        self.current_theme = theme
        if theme == "dark":
            self.setStyleSheet(
                """
                QMainWindow {
                    background: rgba(30, 30, 30, 0.98);
                    border-radius: 12px;
                }
                """
            )
            self.search_bar.setStyleSheet(
                """
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
                """
            )
            self.results_view.setStyleSheet(
                """
                QListView {
                    background: rgba(40, 40, 40, 0.95);
                    border: 1px solid rgba(80, 80, 80, 0.8);
                    border-radius: 8px;
                    color: #eee;
                    padding: 4px 6px;
                }
                QListView::item {
                    padding: 4px 8px;
                    margin: 2px 4px;
                    height: 40px;
                    border-radius: 6px;
                }
                QListView::item:hover {
                    background: rgba(74, 144, 217, 0.2);
                }
                QListView::item:selected {
                    background: rgba(74, 144, 217, 0.3);
                }
                """
            )
            self.status_label.setStyleSheet("color: #888; font-size: 12px;")
        else:
            self.setStyleSheet(
                """
                QMainWindow {
                    background: rgba(245, 245, 245, 0.98);
                    border-radius: 12px;
                }
                """
            )
            self.search_bar.setStyleSheet(
                """
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
                """
            )
            self.results_view.setStyleSheet(
                """
                QListView {
                    background: rgba(255, 255, 255, 0.95);
                    border: 1px solid rgba(200, 200, 200, 0.8);
                    border-radius: 8px;
                    color: #333;
                    padding: 4px 6px;
                }
                QListView::item {
                    padding: 4px 8px;
                    margin: 2px 4px;
                    height: 40px;
                    border-radius: 6px;
                }
                QListView::item:hover {
                    background: rgba(74, 144, 217, 0.2);
                }
                QListView::item:selected {
                    background: rgba(74, 144, 217, 0.3);
                }
                """
            )
            self.status_label.setStyleSheet("color: #666; font-size: 12px;")

        self._apply_pinned_button_style()

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
            self.show()
            self.activateWindow()
            self.search_bar.setFocus()

    def do_refresh(self, apps):
        self.apps = apps
        self.searcher = Searcher(apps)
        self.status_label.setText(f"共 {len(apps)} 个应用")
