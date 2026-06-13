"""插件设置对话框 - 根据插件的 settings_schema 自动生成配置表单"""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSlider,
    QSpinBox,
    QVBoxLayout,
)


class PluginSettingsDialog(QDialog):
    """通用插件配置对话框"""

    def __init__(self, plugin, parent=None):
        super().__init__(parent)
        self.plugin = plugin
        self.schema = plugin.get_settings_schema()
        self.current_settings = plugin.get_settings()
        self.widgets = {}

        self.setWindowTitle(f"插件设置 - {plugin.name}")
        self.setMinimumWidth(440)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        info_label = QLabel(f"{self.plugin.name}  v{self.plugin.version}")
        info_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #333;")
        layout.addWidget(info_label)

        desc_label = QLabel(self.plugin.description)
        desc_label.setStyleSheet("color: #888; font-size: 12px;")
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)

        if self.plugin.author:
            author_label = QLabel(f"作者: {self.plugin.author}")
            author_label.setStyleSheet("color: #aaa; font-size: 11px;")
            layout.addWidget(author_label)

        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet("background: #ddd;")
        layout.addWidget(line)

        if not self.schema:
            no_config = QLabel("此插件没有可配置的选项。")
            no_config.setStyleSheet("color: #999; font-size: 13px;")
            no_config.setAlignment(Qt.AlignCenter)
            layout.addWidget(no_config)
        else:
            group = QGroupBox("配置选项")
            group_layout = QVBoxLayout()
            group_layout.setSpacing(10)

            for item in self.schema:
                row = self._create_setting_row(item)
                if row:
                    group_layout.addLayout(row)

            group.setLayout(group_layout)
            layout.addWidget(group)

        layout.addStretch()

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        reset_btn = QPushButton("恢复默认")
        reset_btn.setStyleSheet("""
            QPushButton {
                background: #f0f0f0; color: #666; border: 1px solid #ddd;
                border-radius: 6px; padding: 6px 16px; min-width: 80px;
            }
            QPushButton:hover { background: #e8e8e8; }
        """)
        reset_btn.clicked.connect(self._reset_defaults)
        btn_layout.addWidget(reset_btn)

        ok_btn = QPushButton("确定")
        ok_btn.setStyleSheet("""
            QPushButton {
                background: #4A90D9; color: white; border: none;
                border-radius: 6px; padding: 6px 16px; min-width: 80px;
            }
            QPushButton:hover { background: #3A80C9; }
        """)
        ok_btn.clicked.connect(self._save_and_close)
        btn_layout.addWidget(ok_btn)

        cancel_btn = QPushButton("取消")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background: #f0f0f0; color: #666; border: 1px solid #ddd;
                border-radius: 6px; padding: 6px 16px; min-width: 80px;
            }
            QPushButton:hover { background: #e8e8e8; }
        """)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        layout.addLayout(btn_layout)

    def _create_setting_row(self, schema_item):
        """根据 schema 定义创建一行设置控件"""
        key = schema_item.get("key")
        label_text = schema_item.get("label", key)
        stype = schema_item.get("type", "text")
        default = schema_item.get("default", "")
        description = schema_item.get("description", "")

        row = QVBoxLayout()
        row.setSpacing(4)

        if stype == "_section_header":
            section_label = QLabel(f"\n◆ {label_text}")
            section_label.setStyleSheet(
                "color: #4A90D9; font-size: 13px; font-weight: bold;"
            )
            row.addWidget(section_label)

            if description:
                desc = QLabel(f"  {description}")
                desc.setStyleSheet("color: #999; font-size: 11px;")
                desc.setWordWrap(True)
                row.addWidget(desc)
            return row

        label_row = QHBoxLayout()
        lbl = QLabel(label_text)
        lbl.setStyleSheet("font-weight: bold; color: #444; font-size: 13px;")
        label_row.addWidget(lbl)
        label_row.addStretch()
        row.addLayout(label_row)

        if stype == "text":
            widget = QLineEdit()
            widget.setText(str(self.current_settings.get(key, default)))
            widget.setStyleSheet("""
                QLineEdit {
                    background: white; border: 1px solid #ddd; border-radius: 6px;
                    padding: 6px 10px; color: #333; font-size: 13px;
                }
                QLineEdit:focus { border-color: #4A90D9; }
            """)
            row.addWidget(widget)
            self.widgets[key] = widget

        elif stype == "number":
            widget = QSpinBox()
            min_val = schema_item.get("min", 0)
            max_val = schema_item.get("max", 99999)
            widget.setRange(min_val, max_val)
            widget.setValue(int(self.current_settings.get(key, default)))
            widget.setStyleSheet("""
                QSpinBox {
                    background: white; border: 1px solid #ddd; border-radius: 6px;
                    padding: 6px 10px; min-width: 100px; color: #333; font-size: 13px;
                }
                QSpinBox:focus { border-color: #4A90D9; }
            """)
            row.addWidget(widget)
            self.widgets[key] = widget

        elif stype == "slider":
            slider_container = QVBoxLayout()
            
            slider_row = QHBoxLayout()
            widget = QSlider(Qt.Horizontal)
            widget.setTickPosition(QSlider.TicksBelow)
            min_val = schema_item.get("min", 0)
            max_val = schema_item.get("max", 100)
            widget.setRange(min_val, max_val)
            widget.setValue(int(self.current_settings.get(key, default)))
            widget.setTickInterval(schema_item.get("tick_interval", (max_val - min_val) // 10 or 1))
            widget.setStyleSheet("""
                QSlider::groove:horizontal {
                    border: 1px solid #ddd;
                    height: 6px;
                    background: #f0f0f0;
                    border-radius: 3px;
                }
                QSlider::handle:horizontal {
                    background: #4A90D9;
                    width: 16px;
                    margin: -5px 0;
                    border-radius: 8px;
                }
                QSlider::sub-page:horizontal {
                    background: #4A90D9;
                    border-radius: 3px;
                }
            """)
            slider_row.addWidget(widget)
            
            value_label = QLabel(str(widget.value()))
            value_label.setStyleSheet("color: #666; font-size: 12px; min-width: 30px;")
            value_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            slider_row.addWidget(value_label)
            
            widget.valueChanged.connect(lambda v, lbl=value_label: lbl.setText(str(v)))
            self.widgets[key] = widget
            
            slider_container.addLayout(slider_row)
            
            if description:
                desc = QLabel(description)
                desc.setStyleSheet("color: #999; font-size: 11px;")
                desc.setWordWrap(True)
                slider_container.addWidget(desc)
            
            row.addLayout(slider_container)

        elif stype == "select":
            widget = QComboBox()
            options = schema_item.get("options", [])
            current_val = self.current_settings.get(key, default)
            selected_idx = 0
            for i, opt in enumerate(options):
                if isinstance(opt, dict):
                    widget.addItem(opt.get("label", ""), opt.get("value", ""))
                    if str(opt.get("value", "")) == str(current_val):
                        selected_idx = i
                else:
                    widget.addItem(str(opt), opt)
                    if str(opt) == str(current_val):
                        selected_idx = i
            widget.setCurrentIndex(selected_idx)
            widget.setStyleSheet("""
                QComboBox {
                    background: white; border: 1px solid #ddd; border-radius: 6px;
                    padding: 6px 10px; min-width: 150px; color: #333; font-size: 13px;
                }
                QComboBox:focus { border-color: #4A90D9; }
                QComboBox::drop-down { border: none; width: 24px; }
            """)
            row.addWidget(widget)
            self.widgets[key] = widget

        elif stype == "checkbox":
            widget = QCheckBox(schema_item.get("check_label", "启用"))
            val = self.current_settings.get(key, default)
            if isinstance(val, str):
                val = val.lower() in ("true", "1", "yes")
            widget.setChecked(bool(val))
            widget.setStyleSheet("""
                QCheckBox {
                    font-size: 13px; color: #444; padding: 4px 0px;
                    spacing: 8px;
                }
                QCheckBox::indicator {
                    width: 18px; height: 18px; border-radius: 3px;
                    border: 1px solid #999;
                }
                QCheckBox::indicator:checked {
                    background: #4A90D9; border: 1px solid #4A90D9;
                }
            """)
            row.addWidget(widget)
            self.widgets[key] = widget

        elif stype == "button":
            widget = QPushButton()
            button_text = schema_item.get("text", "点击")
            widget.setText(button_text)
            widget.setStyleSheet("""
                QPushButton {
                    background: #28a745; color: white; border: none;
                    border-radius: 6px; padding: 8px 16px; min-width: 140px;
                    font-size: 13px; font-weight: bold;
                }
                QPushButton:hover { background: #218838; }
                QPushButton:pressed { background: #1e7e34; }
            """)
            callback_key = schema_item.get("callback_key", f"on_{key}")
            if hasattr(self.plugin, callback_key):
                widget.clicked.connect(getattr(self.plugin, callback_key))
            elif hasattr(self.plugin, key):
                widget.clicked.connect(getattr(self.plugin, key))
            row.addWidget(widget)

        if description and stype not in ("_section_header", "slider"):
            desc = QLabel(description)
            desc.setStyleSheet("color: #999; font-size: 11px;")
            desc.setWordWrap(True)
            row.addWidget(desc)

        return row

    def _collect_values(self):
        """从控件中收集当前值"""
        values = {}
        for key, widget in self.widgets.items():
            if isinstance(widget, QLineEdit):
                values[key] = widget.text()
            elif isinstance(widget, QSpinBox):
                values[key] = widget.value()
            elif isinstance(widget, QSlider):
                values[key] = widget.value()
            elif isinstance(widget, QComboBox):
                values[key] = widget.currentData()
            elif isinstance(widget, QCheckBox):
                values[key] = widget.isChecked()
        return values

    def _save_and_close(self):
        values = self._collect_values()
        self.plugin.save_settings(values)
        self.plugin.on_settings_changed()
        self.accept()

    def _reset_defaults(self):
        defaults = self.plugin.get_default_settings()
        for key, widget in self.widgets.items():
            default_val = defaults.get(key)
            if default_val is None:
                continue
            if isinstance(widget, QLineEdit):
                widget.setText(str(default_val))
            elif isinstance(widget, QSpinBox):
                widget.setValue(int(default_val))
            elif isinstance(widget, QSlider):
                widget.setValue(int(default_val))
            elif isinstance(widget, QComboBox):
                for i in range(widget.count()):
                    if str(widget.itemData(i)) == str(default_val):
                        widget.setCurrentIndex(i)
                        break
            elif isinstance(widget, QCheckBox):
                widget.setChecked(bool(default_val))
