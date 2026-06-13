import os

from PyQt5.QtCore import QSettings, QTimer, Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QDialog,
    QFileDialog,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QRadioButton,
    QScrollArea,
    QSlider,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from app_icon import load_app_icon
from pinned_apps_dialog import PinnedAppsDialog


class SettingsDialog(QDialog):
    settings_changed = pyqtSignal(str, int, list, list, str, str, int, int)

    def __init__(self, available_apps=None, parent=None):
        super().__init__(parent)
        self.available_apps = available_apps or []
        self.pinned_items = []
        self.app_icon = load_app_icon()

        self.setWindowTitle("QStart 设置")
        if self.app_icon:
            self.setWindowIcon(self.app_icon)
        self.setFixedSize(460, 780)
        self.setStyleSheet(
            """
            QDialog {
                background: #f5f5f5;
                border-radius: 8px;
            }
            QGroupBox {
                font-weight: bold;
                color: #333;
                border: 1px solid #ddd;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QRadioButton {
                padding: 5px;
                color: #333;
            }
            QRadioButton:hover {
                color: #4A90D9;
            }
            QRadioButton::indicator {
                width: 16px;
                height: 16px;
            }
            QSlider::groove:horizontal {
                height: 8px;
                background: #ddd;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #4A90D9;
                width: 20px;
                margin: -6px 0;
                border-radius: 10px;
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
            QListWidget {
                border: 1px solid #ddd;
                border-radius: 6px;
                background: white;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #eee;
            }
            QListWidget::item:hover {
                background: #f0f5ff;
            }
            QLabel {
                color: #666;
            }
            QSpinBox {
                background: white;
                border: 1px solid #ddd;
                border-radius: 8px;
                padding: 6px 10px;
                min-width: 90px;
                color: #333;
                font-size: 13px;
            }
            QSpinBox:hover {
                border-color: #b8cbe0;
            }
            QSpinBox:focus {
                border-color: #4A90D9;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                width: 20px;
                border: none;
                background: transparent;
                margin-right: 4px;
            }
            QSpinBox::up-button:hover, QSpinBox::down-button:hover {
                background: #eef5ff;
                border-radius: 5px;
            }
            QSpinBox::up-button:pressed, QSpinBox::down-button:pressed {
                background: #dcecff;
            }
            QSpinBox::up-arrow {
                image: none;
                width: 0px;
                height: 0px;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-bottom: 7px solid #5a6b7d;
            }
            QSpinBox::down-arrow {
                image: none;
                width: 0px;
                height: 0px;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 7px solid #5a6b7d;
            }
            """
        )

        self.settings = QSettings("QStart", "QStart")
        self.listening_hotkey = False
        self.listening_target = ""
        self.open_mod_key = "ctrl"
        self.open_main_key = "space"
        self.run_hotkey = "enter"
        self.key_timer = QTimer(self)
        self.key_timer.setSingleShot(True)
        self.key_timer.timeout.connect(self.stop_listen_hotkey)

        self.init_ui()
        self.load_settings()

    def init_ui(self):
        outer_layout = QVBoxLayout()
        outer_layout.setContentsMargins(0, 0, 0, 0)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setFrameShape(QFrame.NoFrame)

        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        theme_group = QGroupBox("主题设置")
        theme_layout = QHBoxLayout()
        theme_layout.setSpacing(20)
        self.light_radio = QRadioButton("浅色主题")
        self.dark_radio = QRadioButton("深色主题")
        theme_layout.addWidget(self.light_radio)
        theme_layout.addWidget(self.dark_radio)
        theme_group.setLayout(theme_layout)
        layout.addWidget(theme_group)

        opacity_group = QGroupBox("窗口透明度")
        opacity_layout = QVBoxLayout()
        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setRange(50, 100)
        self.opacity_slider.setTickInterval(10)
        self.opacity_slider.setTickPosition(QSlider.TicksBelow)
        opacity_layout.addWidget(self.opacity_slider)

        opacity_value_layout = QHBoxLayout()
        opacity_value_layout.addStretch()
        self.opacity_value = QLabel("100%")
        self.opacity_value.setStyleSheet("font-weight: bold; color: #4A90D9;")
        opacity_value_layout.addWidget(self.opacity_value)
        opacity_layout.addLayout(opacity_value_layout)
        opacity_group.setLayout(opacity_layout)
        layout.addWidget(opacity_group)

        position_group = QGroupBox("搜索框位置")
        position_layout = QVBoxLayout()
        position_xy_layout = QHBoxLayout()
        position_xy_layout.addWidget(QLabel("X 坐标:"))
        self.x_spin = QSpinBox()
        self.x_spin.setRange(0, 3840)
        self.x_spin.setSuffix(" px")
        position_xy_layout.addWidget(self.x_spin)
        position_xy_layout.addWidget(QLabel("Y 坐标:"))
        self.y_spin = QSpinBox()
        self.y_spin.setRange(0, 2160)
        self.y_spin.setSuffix(" px")
        position_xy_layout.addWidget(self.y_spin)
        position_layout.addLayout(position_xy_layout)

        position_note = QLabel("提示: 坐标为 0 时将在屏幕中央显示")
        position_note.setStyleSheet("color: #999; font-size: 11px;")
        position_layout.addWidget(position_note)
        position_group.setLayout(position_layout)
        layout.addWidget(position_group)

        hotkey_group = QGroupBox("快捷键设置")
        hotkey_layout = QVBoxLayout()

        open_layout = QHBoxLayout()
        open_layout.addWidget(QLabel("打开窗口:"))
        self.open_mod_button = self._create_hotkey_button(80)
        self.open_main_button = self._create_hotkey_button(100)
        open_layout.addWidget(self.open_mod_button)
        open_layout.addWidget(QLabel("+"))
        open_layout.addWidget(self.open_main_button)
        hotkey_layout.addLayout(open_layout)

        run_layout = QHBoxLayout()
        run_layout.addWidget(QLabel("运行程序:"))
        self.run_hotkey_button = self._create_hotkey_button(100)
        run_layout.addWidget(self.run_hotkey_button)
        hotkey_layout.addLayout(run_layout)

        hotkey_group.setLayout(hotkey_layout)
        layout.addWidget(hotkey_group)

        custom_group = QGroupBox("自定义快捷方式")
        custom_layout = QVBoxLayout()
        custom_note = QLabel("用于补充检索不到的软件或文件")
        custom_note.setStyleSheet("color: #999; font-size: 11px;")
        custom_layout.addWidget(custom_note)

        self.custom_list = QListWidget()
        self.custom_list.setMinimumHeight(120)
        custom_layout.addWidget(self.custom_list)

        custom_button_layout = QHBoxLayout()
        self.add_custom_button = QPushButton("添加")
        self.remove_custom_button = QPushButton("删除")
        self.add_custom_button.clicked.connect(self.add_custom_item)
        self.remove_custom_button.clicked.connect(self.remove_custom_item)
        custom_button_layout.addWidget(self.add_custom_button)
        custom_button_layout.addWidget(self.remove_custom_button)
        custom_layout.addLayout(custom_button_layout)
        custom_group.setLayout(custom_layout)
        layout.addWidget(custom_group)

        pinned_group = QGroupBox("固定快捷方式")
        pinned_layout = QVBoxLayout()
        pinned_note = QLabel("搜索框为空时显示在下方固定栏中")
        pinned_note.setStyleSheet("color: #999; font-size: 11px;")
        pinned_layout.addWidget(pinned_note)

        self.pinned_preview = QListWidget()
        self.pinned_preview.setMinimumHeight(120)
        pinned_layout.addWidget(self.pinned_preview)

        pinned_button_layout = QHBoxLayout()
        self.manage_pinned_button = QPushButton("管理固定软件")
        self.clear_pinned_button = QPushButton("清空")
        self.manage_pinned_button.clicked.connect(self.manage_pinned_items)
        self.clear_pinned_button.clicked.connect(self.clear_pinned_items)
        pinned_button_layout.addWidget(self.manage_pinned_button)
        pinned_button_layout.addWidget(self.clear_pinned_button)
        pinned_layout.addLayout(pinned_button_layout)
        pinned_group.setLayout(pinned_layout)
        layout.addWidget(pinned_group)

        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet("background: #ddd;")
        layout.addWidget(line)

        footer_layout = QHBoxLayout()
        footer_layout.addStretch()
        self.ok_button = QPushButton("确定")
        self.cancel_button = QPushButton("取消")
        self.ok_button.clicked.connect(self.save_settings)
        self.cancel_button.clicked.connect(self.reject)
        footer_layout.addWidget(self.ok_button)
        footer_layout.addWidget(self.cancel_button)
        layout.addLayout(footer_layout)

        self.opacity_slider.valueChanged.connect(self.on_opacity_change)
        self.open_mod_button.clicked.connect(lambda: self.start_listen_mod("open"))
        self.open_main_button.clicked.connect(lambda: self.start_listen_main("open"))
        self.run_hotkey_button.clicked.connect(self.start_listen_run)

        scroll_area.setWidget(content_widget)
        outer_layout.addWidget(scroll_area)
        self.setLayout(outer_layout)

    def _create_hotkey_button(self, min_width):
        button = QPushButton()
        button.setStyleSheet(self._normal_button_style(min_width))
        return button

    def load_settings(self):
        theme = self.settings.value("theme", "light")
        if theme == "dark":
            self.dark_radio.setChecked(True)
        else:
            self.light_radio.setChecked(True)

        opacity = int(self.settings.value("opacity", 100))
        self.opacity_slider.setValue(opacity)
        self.opacity_value.setText(f"{opacity}%")

        self.x_spin.setValue(int(self.settings.value("window_x", 0)))
        self.y_spin.setValue(int(self.settings.value("window_y", 0)))

        open_hotkey = self.settings.value("open_hotkey", "ctrl + space")
        parts = open_hotkey.split(" + ")
        self.open_mod_key = parts[0] if len(parts) > 0 else "ctrl"
        self.open_main_key = parts[1] if len(parts) > 1 else "space"
        self.open_mod_button.setText(self.open_mod_key)
        self.open_main_button.setText(self.open_main_key)

        self.run_hotkey = self.settings.value("run_hotkey", "enter")
        self.run_hotkey_button.setText(self.run_hotkey)

        self._load_items_into_list(self.custom_list, self.settings.value("custom_items", []))
        self.pinned_items = self.settings.value("pinned_items", [])
        self._refresh_pinned_preview()

    def _load_items_into_list(self, list_widget, items):
        list_widget.clear()
        for item in items:
            QListWidgetItem(f"{item['name']} - {item['path']}", list_widget)

    def _refresh_pinned_preview(self):
        self.pinned_preview.clear()
        for item in self.pinned_items:
            QListWidgetItem(f"{item['name']} - {item['path']}", self.pinned_preview)

    def manage_pinned_items(self):
        dialog = PinnedAppsDialog(self.available_apps, self.pinned_items, self)
        if self.app_icon:
            dialog.setWindowIcon(self.app_icon)
        if dialog.exec_():
            self.pinned_items = dialog.get_selected_items()
            self._refresh_pinned_preview()

    def clear_pinned_items(self):
        self.pinned_items = []
        self._refresh_pinned_preview()

    def start_listen_mod(self, target):
        self._begin_hotkey_capture(f"{target}_mod", self.open_mod_button, "请按下修饰键...")

    def start_listen_main(self, target):
        self._begin_hotkey_capture(f"{target}_main", self.open_main_button, "请按下主键...")

    def start_listen_run(self):
        self._begin_hotkey_capture("run", self.run_hotkey_button, "请按下单键...")

    def _begin_hotkey_capture(self, target, button, text):
        if self.listening_hotkey:
            self.stop_listen_hotkey()

        self.listening_hotkey = True
        self.listening_target = target
        button.setText(text)
        button.setStyleSheet(
            """
            QPushButton {
                background: #fff3cd;
                color: #856404;
                border: 1px solid #ffeeba;
                border-radius: 4px;
                padding: 6px 12px;
                min-width: 100px;
                text-align: center;
            }
            """
        )

        self.grabKeyboard()
        self.key_timer.start(2000)

    def stop_listen_hotkey(self):
        self.listening_hotkey = False
        self.key_timer.stop()

        if self.listening_target == "open_mod":
            if not self.open_mod_key:
                self.open_mod_key = "ctrl"
            self.open_mod_button.setText(self.open_mod_key)
            self.open_mod_button.setStyleSheet(self._normal_button_style(80))
        elif self.listening_target == "open_main":
            if not self.open_main_key:
                self.open_main_key = "space"
            self.open_main_button.setText(self.open_main_key)
            self.open_main_button.setStyleSheet(self._normal_button_style(100))
        elif self.listening_target == "run":
            if not self.run_hotkey:
                self.run_hotkey = "enter"
            self.run_hotkey_button.setText(self.run_hotkey)
            self.run_hotkey_button.setStyleSheet(self._normal_button_style(100))

        self.listening_target = ""
        self.releaseKeyboard()

    def _normal_button_style(self, min_width):
        return (
            f"""
            QPushButton {{
                background: white;
                color: #333;
                border: 1px solid #ddd;
                border-radius: 8px;
                padding: 7px 12px;
                min-width: {min_width}px;
                text-align: center;
                font-family: "Microsoft YaHei UI";
                font-size: 13px;
                font-weight: 500;
                letter-spacing: 0.5px;
            }}
            QPushButton:hover {{
                border-color: #4A90D9;
                background: #f7fbff;
            }}
            QPushButton:pressed {{
                background: #edf4ff;
            }}
            """
        )

    def keyPressEvent(self, event):
        if not self.listening_hotkey:
            super().keyPressEvent(event)
            return

        key_name = self.get_key_name(event.key(), self.listening_target)
        if key_name:
            if self.listening_target == "open_mod":
                self.open_mod_key = key_name
                self.open_mod_button.setText(key_name)
            elif self.listening_target == "open_main":
                self.open_main_key = key_name
                self.open_main_button.setText(key_name)
            elif self.listening_target == "run":
                self.run_hotkey = key_name
                self.run_hotkey_button.setText(key_name)

        self.stop_listen_hotkey()
        event.accept()

    def get_key_name(self, key, target):
        if target.endswith("_mod"):
            if key == Qt.Key_Control:
                return "ctrl"
            if key == Qt.Key_Alt:
                return "alt"
            if key == Qt.Key_Shift:
                return "shift"
            return None

        if key == Qt.Key_Space:
            return "space"
        if key in (Qt.Key_Enter, Qt.Key_Return):
            return "enter"
        if key == Qt.Key_Tab:
            return "tab"
        if key == Qt.Key_Backspace:
            return "backspace"
        if key == Qt.Key_Delete:
            return "delete"
        if Qt.Key_F1 <= key <= Qt.Key_F12:
            return f"f{key - Qt.Key_F1 + 1}"
        if Qt.Key_0 <= key <= Qt.Key_9:
            return str(key - Qt.Key_0)
        if Qt.Key_A <= key <= Qt.Key_Z:
            return chr(key).lower()
        return None

    def closeEvent(self, event):
        if self.listening_hotkey:
            self.stop_listen_hotkey()
        super().closeEvent(event)

    def on_opacity_change(self, value):
        self.opacity_value.setText(f"{value}%")

    def add_custom_item(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "选择文件", "", "所有文件 (*.*)")
        if file_path:
            name = os.path.splitext(os.path.basename(file_path))[0]
            QListWidgetItem(f"{name} - {file_path}", self.custom_list)

    def remove_custom_item(self):
        for item in self.custom_list.selectedItems():
            self.custom_list.takeItem(self.custom_list.row(item))

    def _extract_items(self, list_widget):
        items = []
        for i in range(list_widget.count()):
            item_text = list_widget.item(i).text()
            if " - " in item_text:
                name, path = item_text.rsplit(" - ", 1)
                items.append({"name": name, "path": path})
        return items

    def save_settings(self):
        theme = "dark" if self.dark_radio.isChecked() else "light"
        opacity = self.opacity_slider.value()
        window_x = self.x_spin.value()
        window_y = self.y_spin.value()
        open_hotkey = f"{self.open_mod_key} + {self.open_main_key}"
        custom_items = self._extract_items(self.custom_list)

        self.settings.setValue("theme", theme)
        self.settings.setValue("opacity", opacity)
        self.settings.setValue("window_x", window_x)
        self.settings.setValue("window_y", window_y)
        self.settings.setValue("custom_items", custom_items)
        self.settings.setValue("pinned_items", self.pinned_items)
        self.settings.setValue("open_hotkey", open_hotkey)
        self.settings.setValue("run_hotkey", self.run_hotkey)

        self.settings_changed.emit(
            theme,
            opacity,
            custom_items,
            self.pinned_items,
            open_hotkey,
            self.run_hotkey,
            window_x,
            window_y,
        )
        self.accept()

    def get_theme(self):
        return "dark" if self.dark_radio.isChecked() else "light"

    def get_opacity(self):
        return self.opacity_slider.value() / 100.0
