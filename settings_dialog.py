import os
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QSlider,
    QPushButton, QListWidget, QListWidgetItem, QFileDialog,
    QGroupBox, QButtonGroup, QRadioButton, QFrame, QLineEdit, QSpinBox
)
from PyQt5.QtCore import Qt, pyqtSignal, QSettings, QTimer

class SettingsDialog(QDialog):
    settings_changed = pyqtSignal(str, int, list, str, str, int, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("QStart 设置")
        self.setFixedSize(450, 700)
        self.setStyleSheet("""
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
                border-radius: 4px;
                padding: 4px 8px;
                min-width: 80px;
            }
        """)

        self.settings = QSettings('QStart', 'QStart')

        self.init_ui()
        self.load_settings()

    def init_ui(self):
        layout = QVBoxLayout()
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

        opacity_value_layout = QHBoxLayout()
        self.opacity_value = QLabel("100%")
        self.opacity_value.setStyleSheet("font-weight: bold; color: #4A90D9;")
        opacity_value_layout.addStretch()
        opacity_value_layout.addWidget(self.opacity_value)

        opacity_layout.addWidget(self.opacity_slider)
        opacity_layout.addLayout(opacity_value_layout)
        opacity_group.setLayout(opacity_layout)
        layout.addWidget(opacity_group)

        position_group = QGroupBox("搜索框位置")
        position_layout = QVBoxLayout()

        position_xy_layout = QHBoxLayout()
        position_xy_layout.addWidget(QLabel("X坐标:"))
        self.x_spin = QSpinBox()
        self.x_spin.setRange(0, 3840)
        self.x_spin.setSuffix(" px")
        self.x_spin.setStyleSheet("""
            QSpinBox {
                background: white;
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 4px 8px;
                min-width: 100px;
            }
        """)
        position_xy_layout.addWidget(self.x_spin)
        position_xy_layout.addWidget(QLabel("Y坐标:"))
        self.y_spin = QSpinBox()
        self.y_spin.setRange(0, 2160)
        self.y_spin.setSuffix(" px")
        self.y_spin.setStyleSheet("""
            QSpinBox {
                background: white;
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 4px 8px;
                min-width: 100px;
            }
        """)
        position_xy_layout.addWidget(self.y_spin)
        position_layout.addLayout(position_xy_layout)

        position_note = QLabel("提示: 设置为0将在屏幕中央显示")
        position_note.setStyleSheet("color: #999; font-size: 11px;")
        position_layout.addWidget(position_note)

        position_group.setLayout(position_layout)
        layout.addWidget(position_group)

        hotkey_group = QGroupBox("快捷键设置")
        hotkey_layout = QVBoxLayout()

        open_win_layout = QHBoxLayout()
        open_win_layout.addWidget(QLabel("打开窗口:"))
        self.open_mod_button = QPushButton()
        self.open_mod_button.setStyleSheet("""
            QPushButton {
                background: white;
                color: #333;
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 6px 12px;
                min-width: 80px;
                text-align: center;
            }
            QPushButton:hover {
                border-color: #4A90D9;
            }
            QPushButton:pressed {
                background: #f0f5ff;
            }
        """)
        open_win_layout.addWidget(self.open_mod_button)
        open_win_layout.addWidget(QLabel("+"))
        self.open_main_button = QPushButton()
        self.open_main_button.setStyleSheet("""
            QPushButton {
                background: white;
                color: #333;
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 6px 12px;
                min-width: 100px;
                text-align: center;
            }
            QPushButton:hover {
                border-color: #4A90D9;
            }
            QPushButton:pressed {
                background: #f0f5ff;
            }
        """)
        open_win_layout.addWidget(self.open_main_button)
        hotkey_layout.addLayout(open_win_layout)

        run_app_layout = QHBoxLayout()
        run_app_layout.addWidget(QLabel("运行程序:"))
        self.run_hotkey_button = QPushButton()
        self.run_hotkey_button.setStyleSheet("""
            QPushButton {
                background: white;
                color: #333;
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 6px 12px;
                min-width: 100px;
                text-align: center;
            }
            QPushButton:hover {
                border-color: #4A90D9;
            }
            QPushButton:pressed {
                background: #f0f5ff;
            }
        """)
        run_app_layout.addWidget(self.run_hotkey_button)
        hotkey_layout.addLayout(run_app_layout)

        hotkey_group.setLayout(hotkey_layout)
        layout.addWidget(hotkey_group)

        custom_group = QGroupBox("自定义快捷方式")
        custom_layout = QVBoxLayout()

        self.custom_list = QListWidget()
        self.custom_list.setMinimumHeight(120)

        button_layout = QHBoxLayout()
        self.add_button = QPushButton("添加")
        self.remove_button = QPushButton("删除")

        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.remove_button)

        custom_layout.addWidget(self.custom_list)
        custom_layout.addLayout(button_layout)
        custom_group.setLayout(custom_layout)
        layout.addWidget(custom_group)

        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet("background: #ddd;")
        layout.addWidget(line)

        footer_layout = QHBoxLayout()
        self.ok_button = QPushButton("确定")
        self.cancel_button = QPushButton("取消")

        footer_layout.addStretch()
        footer_layout.addWidget(self.ok_button)
        footer_layout.addWidget(self.cancel_button)

        layout.addLayout(footer_layout)

        self.setLayout(layout)

        self.opacity_slider.valueChanged.connect(self.on_opacity_change)
        self.add_button.clicked.connect(self.add_custom_item)
        self.remove_button.clicked.connect(self.remove_custom_item)
        self.ok_button.clicked.connect(self.save_settings)
        self.cancel_button.clicked.connect(self.reject)
        self.open_mod_button.clicked.connect(lambda: self.start_listen_mod('open'))
        self.open_main_button.clicked.connect(lambda: self.start_listen_main('open'))
        self.run_hotkey_button.clicked.connect(lambda: self.start_listen_run())

        self.listening_hotkey = False
        self.listening_target = ''
        self.key_timer = None

    def load_settings(self):
        theme = self.settings.value('theme', 'light')
        if theme == 'dark':
            self.dark_radio.setChecked(True)
        else:
            self.light_radio.setChecked(True)

        opacity = self.settings.value('opacity', 100)
        self.opacity_slider.setValue(int(opacity))
        self.opacity_value.setText(f"{opacity}%")

        self.x_spin.setValue(int(self.settings.value('window_x', 0)))
        self.y_spin.setValue(int(self.settings.value('window_y', 0)))

        open_hotkey = self.settings.value('open_hotkey', 'ctrl + space')
        parts = open_hotkey.split(' + ')
        self.open_mod_key = parts[0] if len(parts) > 0 else 'ctrl'
        self.open_main_key = parts[1] if len(parts) > 1 else 'space'
        self.open_mod_button.setText(self.open_mod_key)
        self.open_main_button.setText(self.open_main_key)

        self.run_hotkey = self.settings.value('run_hotkey', 'enter')
        self.run_hotkey_button.setText(self.run_hotkey)

        custom_items = self.settings.value('custom_items', [])
        for item in custom_items:
            QListWidgetItem(f"{item['name']} - {item['path']}", self.custom_list)

    def start_listen_mod(self, target):
        if self.listening_hotkey:
            self.stop_listen_hotkey()

        self.listening_hotkey = True
        self.listening_target = f'{target}_mod'

        self.open_mod_button.setText("请按下修饰键...")
        self.open_mod_button.setStyleSheet("""
            QPushButton {
                background: #fff3cd;
                color: #856404;
                border: 1px solid #ffeeba;
                border-radius: 4px;
                padding: 6px 12px;
                min-width: 80px;
                text-align: center;
            }
        """)

        self.grabKeyboard()
        if self.key_timer:
            self.key_timer.stop()
        self.key_timer = QTimer.singleShot(2000, self.stop_listen_hotkey)

    def start_listen_main(self, target):
        if self.listening_hotkey:
            self.stop_listen_hotkey()

        self.listening_hotkey = True
        self.listening_target = f'{target}_main'

        self.open_main_button.setText("请按下主键...")
        self.open_main_button.setStyleSheet("""
            QPushButton {
                background: #fff3cd;
                color: #856404;
                border: 1px solid #ffeeba;
                border-radius: 4px;
                padding: 6px 12px;
                min-width: 100px;
                text-align: center;
            }
        """)

        self.grabKeyboard()
        if self.key_timer:
            self.key_timer.stop()
        self.key_timer = QTimer.singleShot(2000, self.stop_listen_hotkey)

    def start_listen_run(self):
        if self.listening_hotkey:
            self.stop_listen_hotkey()

        self.listening_hotkey = True
        self.listening_target = 'run'

        self.run_hotkey_button.setText("请按下单键...")
        self.run_hotkey_button.setStyleSheet("""
            QPushButton {
                background: #fff3cd;
                color: #856404;
                border: 1px solid #ffeeba;
                border-radius: 4px;
                padding: 6px 12px;
                min-width: 100px;
                text-align: center;
            }
        """)

        self.grabKeyboard()
        if self.key_timer:
            self.key_timer.stop()
        self.key_timer = QTimer.singleShot(2000, self.stop_listen_hotkey)

    def stop_listen_hotkey(self):
        self.listening_hotkey = False

        if self.listening_target == 'open_mod':
            button = self.open_mod_button
            if not self.open_mod_key:
                self.open_mod_key = 'ctrl'
            button.setText(self.open_mod_key)
            button.setStyleSheet("""
                QPushButton {
                    background: white;
                    color: #333;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    padding: 6px 12px;
                    min-width: 80px;
                    text-align: center;
                }
                QPushButton:hover {
                    border-color: #4A90D9;
                }
            """)
        elif self.listening_target == 'open_main':
            button = self.open_main_button
            if not self.open_main_key:
                self.open_main_key = 'space'
            button.setText(self.open_main_key)
            button.setStyleSheet("""
                QPushButton {
                    background: white;
                    color: #333;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    padding: 6px 12px;
                    min-width: 100px;
                    text-align: center;
                }
                QPushButton:hover {
                    border-color: #4A90D9;
                }
            """)
        elif self.listening_target == 'run':
            button = self.run_hotkey_button
            if not self.run_hotkey:
                self.run_hotkey = 'enter'
            button.setText(self.run_hotkey)
            button.setStyleSheet("""
                QPushButton {
                    background: white;
                    color: #333;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    padding: 6px 12px;
                    min-width: 100px;
                    text-align: center;
                }
                QPushButton:hover {
                    border-color: #4A90D9;
                }
            """)

        self.releaseKeyboard()

    def keyPressEvent(self, event):
        if not self.listening_hotkey:
            super().keyPressEvent(event)
            return

        key = event.key()
        key_name = self.get_key_name(key, self.listening_target)

        if key_name:
            if self.listening_target == 'open_mod':
                self.open_mod_key = key_name
                self.open_mod_button.setText(key_name)
            elif self.listening_target == 'open_main':
                self.open_main_key = key_name
                self.open_main_button.setText(key_name)
            elif self.listening_target == 'run':
                self.run_hotkey = key_name
                self.run_hotkey_button.setText(key_name)

        self.stop_listen_hotkey()
        event.accept()

    def get_key_name(self, key, target):
        if target.endswith('_mod'):
            if key == Qt.Key_Control:
                return 'ctrl'
            elif key == Qt.Key_Alt:
                return 'alt'
            elif key == Qt.Key_Shift:
                return 'shift'
        else:
            if key == Qt.Key_Space:
                return 'space'
            elif key == Qt.Key_Enter or key == Qt.Key_Return:
                return 'enter'
            elif key == Qt.Key_Tab:
                return 'tab'
            elif key == Qt.Key_Backspace:
                return 'backspace'
            elif key == Qt.Key_Delete:
                return 'delete'
            elif key >= Qt.Key_F1 and key <= Qt.Key_F12:
                return f'f{key - Qt.Key_F1 + 1}'
            elif key >= Qt.Key_0 and key <= Qt.Key_9:
                return str(key - Qt.Key_0)
            elif key >= Qt.Key_A and key <= Qt.Key_Z:
                return chr(key).lower()
        return None

    def closeEvent(self, event):
        if self.listening_hotkey:
            self.stop_listen_hotkey()
        super().closeEvent(event)

    def on_opacity_change(self, value):
        self.opacity_value.setText(f"{value}%")

    def add_custom_item(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择文件", "", "所有文件 (*.*)"
        )
        if file_path:
            name = os.path.splitext(os.path.basename(file_path))[0]
            QListWidgetItem(f"{name} - {file_path}", self.custom_list)

    def remove_custom_item(self):
        selected = self.custom_list.selectedItems()
        if selected:
            for item in selected:
                self.custom_list.takeItem(self.custom_list.row(item))

    def save_settings(self):
        theme = 'dark' if self.dark_radio.isChecked() else 'light'
        opacity = self.opacity_slider.value()

        window_x = self.x_spin.value()
        window_y = self.y_spin.value()

        open_mod = getattr(self, 'open_mod_key', 'ctrl')
        open_main = getattr(self, 'open_main_key', 'space')
        open_hotkey = f"{open_mod} + {open_main}"

        run_hotkey = self.run_hotkey if hasattr(self, 'run_hotkey') else 'enter'

        custom_items = []
        for i in range(self.custom_list.count()):
            item_text = self.custom_list.item(i).text()
            if ' - ' in item_text:
                name, path = item_text.rsplit(' - ', 1)
                custom_items.append({'name': name, 'path': path})

        self.settings.setValue('theme', theme)
        self.settings.setValue('opacity', opacity)
        self.settings.setValue('window_x', window_x)
        self.settings.setValue('window_y', window_y)
        self.settings.setValue('custom_items', custom_items)
        self.settings.setValue('open_hotkey', open_hotkey)
        self.settings.setValue('run_hotkey', run_hotkey)

        self.settings_changed.emit(theme, opacity, custom_items, open_hotkey, run_hotkey, window_x, window_y)
        self.accept()

    def get_theme(self):
        return 'dark' if self.dark_radio.isChecked() else 'light'

    def get_opacity(self):
        return self.opacity_slider.value() / 100.0
