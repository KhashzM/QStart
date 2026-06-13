"""剪贴板历史对话框 - 类似 Windows 11 剪贴板历史界面"""

import os
from datetime import datetime

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
)


class ClipboardItemWidget(QWidget):
    """单条剪贴板记录"""

    clicked = pyqtSignal(str)  # 点击时发送内容

    def __init__(self, content: str, timestamp: str, parent=None):
        super().__init__(parent)
        self._content = content
        self._setup_ui(content, timestamp)

    def _setup_ui(self, content: str, timestamp: str):
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(52)
        self.setObjectName("clipboard-item")
        self.setStyleSheet("""
            QWidget#clipboard-item {
                background: white;
                border: 1px solid #e8e8e8;
                border-radius: 8px;
            }
            QWidget#clipboard-item:hover {
                background: #f0f7ff;
                border-color: #4A90D9;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 12, 0)
        layout.setSpacing(10)

        # 图标
        icon_label = QLabel("📋")
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

        # 内容区域：单行预览 + 时间信息，垂直居中
        content_layout = QVBoxLayout()
        content_layout.setSpacing(1)
        content_layout.setContentsMargins(0, 0, 0, 0)

        # 预览文本（单行，按像素宽度截断）
        full_preview = content.replace("\n", " ").strip()
        if not full_preview:
            full_preview = "(空白)"

        preview_label = QLabel()
        preview_label.setStyleSheet("color: #333; font-size: 13px;")
        preview_label.setWordWrap(False)
        preview_label.setToolTip(full_preview)
        content_layout.addWidget(preview_label)

        # 用 QFontMetrics 按像素宽度 elide（可用宽度约240px）
        fm = preview_label.fontMetrics()
        elided = fm.elidedText(full_preview, Qt.ElideRight, 240)
        preview_label.setText(elided)

        # 时间和长度
        info_text = f"{timestamp}  |  {len(content)} 字符"
        info_label = QLabel(info_text)
        info_label.setStyleSheet("color: #aaa; font-size: 11px;")
        content_layout.addWidget(info_label)

        layout.addLayout(content_layout, 1)

        # 复制按钮
        copy_btn = QPushButton("复制")
        copy_btn.setFixedSize(50, 28)
        copy_btn.setStyleSheet("""
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
        copy_btn.setCursor(Qt.PointingHandCursor)
        copy_btn.clicked.connect(lambda: self.clicked.emit(self._content))
        layout.addWidget(copy_btn)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self._content)
        super().mousePressEvent(event)


class ClipboardDialog(QDialog):
    """剪贴板历史对话框"""

    def __init__(self, clipboard_plugin, parent=None):
        super().__init__(parent)
        self.plugin = clipboard_plugin
        self.setWindowTitle("剪贴板历史")
        self.setMinimumSize(420, 560)
        self.resize(420, 560)
        self._init_ui()
        self._refresh_list()

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

        title = QLabel("📋 剪贴板历史")
        title.setStyleSheet("color: #eee; font-size: 15px; font-weight: bold;")
        header_layout.addWidget(title)

        header_layout.addStretch()

        # 搜索框
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索...")
        self.search_input.setFixedWidth(140)
        self.search_input.setFixedHeight(28)
        self.search_input.setStyleSheet("""
            QLineEdit {
                background: #444;
                border: 1px solid #555;
                border-radius: 14px;
                padding: 4px 12px;
                color: #eee;
                font-size: 12px;
            }
            QLineEdit:focus { border-color: #4A90D9; }
        """)
        self.search_input.textChanged.connect(self._on_search)
        header_layout.addWidget(self.search_input)

        # 清空按钮
        clear_btn = QPushButton("清空全部")
        clear_btn.setStyleSheet("""
            QPushButton {
                background: #c0392b;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 4px 12px;
                font-size: 12px;
            }
            QPushButton:hover { background: #e74c3c; }
            QPushButton:pressed { background: #a93226; }
        """)
        clear_btn.setAutoDefault(False)
        clear_btn.setDefault(False)
        clear_btn.clicked.connect(self._clear_all)
        header_layout.addWidget(clear_btn)

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
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.NoFrame)
        self.scroll_area.setStyleSheet("QScrollArea { background: #f0f0f0; border: none; }")

        self.list_widget = QWidget()
        self.list_layout = QVBoxLayout(self.list_widget)
        self.list_layout.setContentsMargins(12, 8, 12, 8)
        self.list_layout.setSpacing(6)
        self.list_layout.addStretch()

        self.scroll_area.setWidget(self.list_widget)
        layout.addWidget(self.scroll_area, 1)

        # 底部提示
        footer = QLabel("点击记录即可复制到剪贴板，然后 Ctrl+V 粘贴")
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

    def _refresh_list(self, filter_text=""):
        """刷新列表显示"""
        # 清空旧项
        while self.list_layout.count() > 1:
            item = self.list_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        history = self.plugin.get_history()
        filtered = history

        if filter_text:
            ft = filter_text.lower()
            filtered = [h for h in history if ft in h["content"].lower()]

        # 更新统计
        if filter_text:
            self.stats_bar.setText(f"搜索 \"{filter_text}\" - 找到 {len(filtered)} 条记录")
        else:
            self.stats_bar.setText(f"共 {len(history)} 条记录")

        # 创建列表项
        for record in filtered:
            widget = ClipboardItemWidget(
                content=record["content"],
                timestamp=record.get("time_str", ""),
            )
            widget.clicked.connect(self._on_item_clicked)
            # 插入到 stretch 之前
            count = self.list_layout.count()
            self.list_layout.insertWidget(count - 1, widget)

        # 空状态提示
        if not filtered:
            empty_label = QLabel("暂无剪贴板记录" if not filter_text else "没有匹配的记录")
            empty_label.setAlignment(Qt.AlignCenter)
            empty_label.setStyleSheet("color: #bbb; font-size: 14px; padding: 40px;")
            count = self.list_layout.count()
            self.list_layout.insertWidget(count - 1, empty_label)

    def _on_search(self, text):
        self._refresh_list(text)

    def _on_item_clicked(self, content: str):
        """点击记录：复制到系统剪贴板"""
        clipboard = QApplication.clipboard()
        if clipboard:
            clipboard.setText(content)
            # 短暂高亮提示已复制
            self.stats_bar.setText("✅ 已复制到剪贴板")
            QTimer.singleShot(1500, lambda: self._refresh_list(self.search_input.text()))

    def _clear_all(self):
        """清空所有记录"""
        from PyQt5.QtWidgets import QMessageBox
        reply = QMessageBox.question(
            self,
            "确认清空",
            "确定要清空所有剪贴板历史记录吗？此操作不可撤销。",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self.plugin.clear_history()
            self._refresh_list()

    def showEvent(self, event):
        """每次显示时刷新列表"""
        super().showEvent(event)
        self.search_input.clear()
        self._refresh_list()