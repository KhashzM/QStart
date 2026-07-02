"""自定义热键管理对话框"""

import os

from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtWidgets import (
    QApplication,
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QFrame,
    QVBoxLayout,
    QWidget,
    QFileDialog,
    QMessageBox,
)


class HotkeyCaptureButton(QPushButton):
    """支持按键捕获的按钮"""
    
    hotkey_captured = pyqtSignal(str)
    
    def __init__(self, initial_hotkey="", parent=None):
        super().__init__(parent)
        self.hotkey = initial_hotkey
        self.is_capturing = False
        self.captured_modifiers = set()
        self.captured_key = ""
        self.capture_timer = QTimer(self)
        self.capture_timer.setSingleShot(True)
        self.capture_timer.timeout.connect(self._stop_capture)
        
        self.setText(self.hotkey if self.hotkey else "点击设置")
        self._apply_normal_style()
        self.clicked.connect(self._start_capture)
    
    def _apply_normal_style(self):
        self.setStyleSheet("""
            QPushButton {
                background: white;
                color: #333;
                border: 1px solid #ddd;
                border-radius: 8px;
                padding: 7px 12px;
                min-width: 150px;
                text-align: center;
                font-family: "Microsoft YaHei UI";
                font-size: 13px;
                font-weight: 500;
            }
            QPushButton:hover {
                border-color: #4A90D9;
                background: #f7fbff;
            }
            QPushButton:pressed {
                background: #edf4ff;
            }
        """)
    
    def _apply_capturing_style(self):
        self.setStyleSheet("""
            QPushButton {
                background: #fff3cd;
                color: #856404;
                border: 1px solid #ffeeba;
                border-radius: 8px;
                padding: 7px 12px;
                min-width: 150px;
                text-align: center;
                font-family: "Microsoft YaHei UI";
                font-size: 13px;
                font-weight: 500;
            }
        """)
    
    def _start_capture(self):
        if self.is_capturing:
            return
        self.is_capturing = True
        self.captured_modifiers = set()
        self.captured_key = ""
        self.setText("请按下快捷键...")
        self._apply_capturing_style()
        self.grabKeyboard()
        self.capture_timer.start(3000)
    
    def _stop_capture(self):
        if not self.is_capturing:
            return
        self.is_capturing = False
        self.releaseKeyboard()
        self.capture_timer.stop()
        
        if self.captured_key:
            parts = sorted(list(self.captured_modifiers)) + [self.captured_key]
            self.hotkey = "+".join(parts)
            self.setText(self.hotkey)
            self.hotkey_captured.emit(self.hotkey)
        else:
            self.setText(self.hotkey if self.hotkey else "点击设置")
        
        self._apply_normal_style()
    
    def keyPressEvent(self, event):
        if not self.is_capturing:
            super().keyPressEvent(event)
            return
        
        key = event.key()
        
        # 记录修饰键
        if key == Qt.Key_Control:
            self.captured_modifiers.add("ctrl")
        elif key == Qt.Key_Alt:
            self.captured_modifiers.add("alt")
        elif key == Qt.Key_Shift:
            self.captured_modifiers.add("shift")
        elif key == Qt.Key_Meta:
            self.captured_modifiers.add("win")
        else:
            # 记录主键
            key_name = self._get_key_name(key)
            if key_name:
                self.captured_key = key_name
        
        # 更新显示
        if self.captured_modifiers or self.captured_key:
            parts = sorted(list(self.captured_modifiers))
            if self.captured_key:
                parts.append(self.captured_key)
            display_text = "+".join(parts) if parts else "请按下快捷键..."
            self.setText(display_text)
        
        event.accept()
    
    def keyReleaseEvent(self, event):
        if not self.is_capturing:
            super().keyReleaseEvent(event)
            return
        
        # 当释放非修饰键时，完成捕获
        key = event.key()
        if key not in (Qt.Key_Control, Qt.Key_Alt, Qt.Key_Shift, Qt.Key_Meta):
            QTimer.singleShot(100, self._stop_capture)
        
        event.accept()
    
    def _get_key_name(self, key):
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
        if key == Qt.Key_Escape:
            return "esc"
        if Qt.Key_F1 <= key <= Qt.Key_F24:
            return f"f{key - Qt.Key_F1 + 1}"
        if Qt.Key_0 <= key <= Qt.Key_9:
            return str(key - Qt.Key_0)
        if Qt.Key_A <= key <= Qt.Key_Z:
            return chr(key).lower()
        return None
    
    def get_hotkey(self):
        return self.hotkey
    
    def set_hotkey(self, hotkey):
        self.hotkey = hotkey
        self.setText(self.hotkey if self.hotkey else "点击设置")


class HotkeyItemWidget(QWidget):
    """单条热键记录"""

    edit_clicked = pyqtSignal(dict)
    delete_clicked = pyqtSignal(dict)

    def __init__(self, hotkey_data: dict, parent=None):
        super().__init__(parent)
        self._data = hotkey_data
        self._setup_ui(hotkey_data)

    def _setup_ui(self, hotkey_data: dict):
        self.setFixedHeight(56)
        self.setObjectName("hotkey-item")
        self.setStyleSheet("""
            QWidget#hotkey-item {
                background: white;
                border: 1px solid #e8e8e8;
                border-radius: 8px;
            }
            QWidget#hotkey-item:hover {
                background: #f0f7ff;
                border-color: #4A90D9;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 12, 0)
        layout.setSpacing(10)

        # 图标
        hotkey_type = hotkey_data.get("type", "app")
        icon_text = "⚡" if hotkey_type == "command" else "⌨️"
        icon_label = QLabel(icon_text)
        icon_label.setFixedSize(28, 28)
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet("""
            QLabel {
                background: #f5f5f5;
                border-radius: 6px;
                font-size: 14px;
            }
        """)
        layout.addWidget(icon_label)

        # 内容区域：热键 + 程序名称
        content_layout = QVBoxLayout()
        content_layout.setSpacing(2)
        content_layout.setContentsMargins(0, 0, 0, 0)

        name_label = QLabel(hotkey_data.get("name", "未命名"))
        name_label.setStyleSheet("color: #333; font-size: 13px; font-weight: 500;")
        content_layout.addWidget(name_label)

        hotkey_label = QLabel(f"热键: {hotkey_data.get('hotkey', '')} | {'命令' if hotkey_type == 'command' else '程序'}")
        hotkey_label.setStyleSheet("color: #888; font-size: 11px;")
        content_layout.addWidget(hotkey_label)

        layout.addLayout(content_layout, 1)

        # 路径/命令预览（单行截断）
        path_preview = hotkey_data.get("path", "")
        path_label = QLabel()
        path_label.setStyleSheet("color: #666; font-size: 11px;")
        path_label.setWordWrap(False)
        path_label.setToolTip(path_preview)
        fm = path_label.fontMetrics()
        elided = fm.elidedText(path_preview, Qt.ElideMiddle, 200)
        path_label.setText(elided)
        layout.addWidget(path_label, 1)

        # 编辑按钮
        edit_btn = QPushButton("编辑")
        edit_btn.setFixedSize(50, 28)
        edit_btn.setStyleSheet("""
            QPushButton {
                background: #4A90D9;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 12px;
            }
            QPushButton:hover { background: #3A80C9; }
            QPushButton:pressed { background: #2A70B9; }
        """)
        edit_btn.setCursor(Qt.PointingHandCursor)
        edit_btn.clicked.connect(lambda: self.edit_clicked.emit(self._data))
        layout.addWidget(edit_btn)

        # 删除按钮
        delete_btn = QPushButton("删除")
        delete_btn.setFixedSize(50, 28)
        delete_btn.setStyleSheet("""
            QPushButton {
                background: #c0392b;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 12px;
            }
            QPushButton:hover { background: #e74c3c; }
            QPushButton:pressed { background: #a93226; }
        """)
        delete_btn.setCursor(Qt.PointingHandCursor)
        delete_btn.clicked.connect(lambda: self.delete_clicked.emit(self._data))
        layout.addWidget(delete_btn)


class HotkeyEditDialog(QDialog):
    """热键编辑对话框"""

    def __init__(self, hotkey_data: dict = None, parent=None):
        super().__init__(parent)
        self._data = hotkey_data or {}
        self.setWindowTitle("编辑热键" if hotkey_data else "添加热键")
        self.setMinimumSize(460, 300)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        # 类型选择
        type_label = QLabel("热键类型")
        type_label.setStyleSheet("color: #333; font-size: 13px; font-weight: 500;")
        layout.addWidget(type_label)

        type_layout = QHBoxLayout()
        type_layout.setSpacing(12)
        
        self.type_app_radio = QPushButton("🖥️ 启动程序")
        self.type_app_radio.setCheckable(True)
        self.type_app_radio.setStyleSheet("""
            QPushButton {
                background: white;
                color: #333;
                border: 2px solid #ddd;
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 13px;
                font-weight: 500;
            }
            QPushButton:checked {
                background: #4A90D9;
                color: white;
                border-color: #4A90D9;
            }
            QPushButton:hover { border-color: #4A90D9; }
        """)
        type_layout.addWidget(self.type_app_radio)
        
        self.type_command_radio = QPushButton("⚡ 插件命令")
        self.type_command_radio.setCheckable(True)
        self.type_command_radio.setStyleSheet("""
            QPushButton {
                background: white;
                color: #333;
                border: 2px solid #ddd;
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 13px;
                font-weight: 500;
            }
            QPushButton:checked {
                background: #4A90D9;
                color: white;
                border-color: #4A90D9;
            }
            QPushButton:hover { border-color: #4A90D9; }
        """)
        type_layout.addWidget(self.type_command_radio)
        layout.addLayout(type_layout)
        
        self.type_app_radio.clicked.connect(lambda: self._on_type_changed(True))
        self.type_command_radio.clicked.connect(lambda: self._on_type_changed(False))
        
        hotkey_type = self._data.get("type", "app")
        self.type_app_radio.setChecked(hotkey_type == "app")
        self.type_command_radio.setChecked(hotkey_type == "command")

        # 程序名称
        name_label = QLabel("显示名称")
        name_label.setStyleSheet("color: #333; font-size: 13px; font-weight: 500;")
        layout.addWidget(name_label)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("例如：记事本 或 剪贴板历史")
        self.name_input.setText(self._data.get("name", ""))
        self.name_input.setStyleSheet("""
            QLineEdit {
                background: white;
                border: 1px solid #ddd;
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 13px;
            }
            QLineEdit:focus { border-color: #4A90D9; }
        """)
        layout.addWidget(self.name_input)

        # 热键
        hotkey_label = QLabel("热键组合")
        hotkey_label.setStyleSheet("color: #333; font-size: 13px; font-weight: 500;")
        layout.addWidget(hotkey_label)

        hotkey_hint = QLabel("点击按钮，然后按下要设置的快捷键组合")
        hotkey_hint.setStyleSheet("color: #999; font-size: 11px;")
        layout.addWidget(hotkey_hint)

        self.hotkey_button = HotkeyCaptureButton(self._data.get("hotkey", ""))
        layout.addWidget(self.hotkey_button)

        # 程序路径或命令
        self.path_label = QLabel("程序路径")
        self.path_label.setStyleSheet("color: #333; font-size: 13px; font-weight: 500;")
        layout.addWidget(self.path_label)

        path_layout = QHBoxLayout()
        self.path_input = QLineEdit()
        self.path_input.setPlaceholderText("选择程序或文件路径")
        self.path_input.setText(self._data.get("path", ""))
        self.path_input.setStyleSheet("""
            QLineEdit {
                background: white;
                border: 1px solid #ddd;
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 13px;
            }
            QLineEdit:focus { border-color: #4A90D9; }
        """)
        path_layout.addWidget(self.path_input, 1)

        self.browse_btn = QPushButton("浏览...")
        self.browse_btn.setFixedSize(80, 34)
        self.browse_btn.setStyleSheet("""
            QPushButton {
                background: #f0f0f0;
                color: #333;
                border: 1px solid #ddd;
                border-radius: 6px;
                font-size: 12px;
            }
            QPushButton:hover { background: #e8e8e8; }
        """)
        self.browse_btn.clicked.connect(self._browse_file)
        path_layout.addWidget(self.browse_btn)
        layout.addLayout(path_layout)

        # 按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("取消")
        cancel_btn.setFixedSize(80, 34)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background: #f0f0f0;
                color: #333;
                border: 1px solid #ddd;
                border-radius: 6px;
                font-size: 13px;
            }
            QPushButton:hover { background: #e8e8e8; }
        """)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        save_btn = QPushButton("保存")
        save_btn.setFixedSize(80, 34)
        save_btn.setStyleSheet("""
            QPushButton {
                background: #4A90D9;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 13px;
            }
            QPushButton:hover { background: #3A80C9; }
            QPushButton:pressed { background: #2A70B9; }
        """)
        save_btn.clicked.connect(self._on_save)
        save_btn.setDefault(True)
        btn_layout.addWidget(save_btn)
        layout.addLayout(btn_layout)
        
        self._on_type_changed(hotkey_type == "app")

    def _on_type_changed(self, is_app):
        """类型切换处理"""
        self.type_app_radio.setChecked(is_app)
        self.type_command_radio.setChecked(not is_app)
        is_command = not is_app
        self.path_label.setText("插件命令" if is_command else "程序路径")
        self.path_input.setPlaceholderText("输入插件命令，如 clip list" if is_command else "选择程序或文件路径")
        self.browse_btn.setVisible(not is_command)

    def _browse_file(self):
        """浏览选择文件或文件夹"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择程序",
            "",
            "可执行文件 (*.exe *.lnk *.bat *.cmd);;所有文件 (*.*)"
        )
        if file_path:
            self.path_input.setText(file_path)
            if not self.name_input.text():
                name = os.path.basename(file_path)
                name = os.path.splitext(name)[0]
                self.name_input.setText(name)

    def _on_save(self):
        """保存验证"""
        name = self.name_input.text().strip()
        hotkey = self.hotkey_button.get_hotkey()
        path = self.path_input.text().strip()
        hotkey_type = "command" if self.type_command_radio.isChecked() else "app"

        if not name:
            QMessageBox.warning(self, "提示", "请输入显示名称")
            return
        if not hotkey:
            QMessageBox.warning(self, "提示", "请设置热键组合")
            return
        if not path:
            msg = "请输入插件命令" if hotkey_type == "command" else "请选择有效的程序路径"
            QMessageBox.warning(self, "提示", msg)
            return
        
        if hotkey_type == "app" and not os.path.exists(path):
            QMessageBox.warning(self, "提示", "请选择有效的程序路径")
            return

        self._result = {
            "name": name,
            "hotkey": hotkey,
            "path": path,
            "type": hotkey_type
        }
        self.accept()

    def get_result(self) -> dict:
        return self._result if hasattr(self, "_result") else None


class CustomHotkeysDialog(QDialog):
    """自定义热键管理对话框"""

    def __init__(self, hotkey_plugin, parent=None):
        super().__init__(parent)
        self.plugin = hotkey_plugin
        self.setWindowTitle("自定义热键管理")
        self.setMinimumSize(520, 520)
        self.resize(560, 520)
        self._init_ui()
        self._refresh_list()
    
    def show(self):
        """显示对话框并置顶"""
        super().show()
        self.raise_()
        self.activateWindow()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 顶部标题栏
        header = QWidget()
        header.setFixedHeight(52)
        header.setStyleSheet("""
            QWidget {
                background: #2E2E2E;
                border-bottom: 1px solid #3a3a3a;
            }
        """)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(16, 0, 16, 0)

        title = QLabel("⌨️ 自定义热键管理")
        title.setStyleSheet("color: #eee; font-size: 15px; font-weight: bold;")
        header_layout.addWidget(title)

        header_layout.addStretch()

        # 添加按钮
        add_btn = QPushButton("➕ 添加热键")
        add_btn.setStyleSheet("""
            QPushButton {
                background: #4A90D9;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 16px;
                font-size: 12px;
            }
            QPushButton:hover { background: #3A80C9; }
            QPushButton:pressed { background: #2A70B9; }
        """)
        add_btn.setAutoDefault(False)
        add_btn.setDefault(False)
        add_btn.clicked.connect(self._add_hotkey)
        header_layout.addWidget(add_btn)

        layout.addWidget(header)

        # 统计信息栏
        self.stats_bar = QLabel()
        self.stats_bar.setFixedHeight(28)
        self.stats_bar.setStyleSheet("""
            QLabel {
                background: #f5f5f5;
                border-bottom: 1px solid #eee;
                padding: 0 16px;
                color: #888;
                font-size: 11px;
            }
        """)
        layout.addWidget(self.stats_bar)

        # 列表区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setStyleSheet("QScrollArea { background: #f0f0f0; border: none; }")

        self.list_widget = QWidget()
        self.list_layout = QVBoxLayout(self.list_widget)
        self.list_layout.setContentsMargins(12, 8, 12, 8)
        self.list_layout.setSpacing(8)
        self.list_layout.addStretch()

        scroll_area.setWidget(self.list_widget)
        layout.addWidget(scroll_area, 1)

        # 底部提示
        footer = QLabel("点击热键按钮，然后按下键盘上的按键组合来设置")
        footer.setFixedHeight(32)
        footer.setAlignment(Qt.AlignCenter)
        footer.setStyleSheet("""
            QLabel {
                background: #f5f5f5;
                border-top: 1px solid #eee;
                color: #999;
                font-size: 11px;
            }
        """)
        layout.addWidget(footer)

    def _refresh_list(self):
        """刷新列表显示"""
        # 清空旧项
        while self.list_layout.count() > 1:
            item = self.list_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        hotkeys = self.plugin.get_hotkeys()
        self.stats_bar.setText(f"共 {len(hotkeys)} 个热键配置")

        # 创建列表项
        for hk in hotkeys:
            widget = HotkeyItemWidget(hk)
            widget.edit_clicked.connect(self._edit_hotkey)
            widget.delete_clicked.connect(self._delete_hotkey)
            count = self.list_layout.count()
            self.list_layout.insertWidget(count - 1, widget)

        # 空状态提示
        if not hotkeys:
            empty_label = QLabel("暂无热键配置，点击「添加热键」开始添加")
            empty_label.setAlignment(Qt.AlignCenter)
            empty_label.setStyleSheet("color: #bbb; font-size: 14px; padding: 40px;")
            count = self.list_layout.count()
            self.list_layout.insertWidget(count - 1, empty_label)

    def _add_hotkey(self):
        """添加新热键"""
        dialog = HotkeyEditDialog(parent=self)
        if dialog.exec_() == QDialog.Accepted:
            result = dialog.get_result()
            if result:
                try:
                    success = self.plugin.add_hotkey(
                        result["hotkey"],
                        result["path"],
                        result["name"],
                        result.get("type", "app")
                    )
                    if success:
                        self.stats_bar.setText(f"✅ 已添加热键: {result['hotkey']}")
                        QTimer.singleShot(1500, self._refresh_list)
                    else:
                        QMessageBox.warning(self, "提示", "该热键已存在")
                except RuntimeError as e:
                    QMessageBox.warning(self, "错误", str(e))

    def _edit_hotkey(self, hotkey_data: dict):
        """编辑热键"""
        dialog = HotkeyEditDialog(hotkey_data, parent=self)
        if dialog.exec_() == QDialog.Accepted:
            result = dialog.get_result()
            if result:
                success = self.plugin.update_hotkey(
                    hotkey_data["hotkey"],
                    result["hotkey"],
                    result["path"],
                    result["name"],
                    result.get("type", "app")
                )
                if success:
                    self.stats_bar.setText(f"✅ 已更新热键: {result['hotkey']}")
                    QTimer.singleShot(1500, self._refresh_list)

    def _delete_hotkey(self, hotkey_data: dict):
        """删除热键"""
        reply = QMessageBox.question(
            self,
            "确认删除",
            f"确定要删除热键「{hotkey_data['hotkey']}」吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self.plugin.remove_hotkey(hotkey_data["hotkey"])
            self.stats_bar.setText(f"✅ 已删除热键: {hotkey_data['hotkey']}")
            QTimer.singleShot(1500, self._refresh_list)

    def showEvent(self, event):
        """每次显示时刷新列表"""
        super().showEvent(event)
        self._refresh_list()
