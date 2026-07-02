from PyQt5.QtCore import Qt, QPoint, QEvent
from PyQt5.QtGui import QFont, QColor, QPainter, QPen
from PyQt5.QtWidgets import (
    QTextEdit,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QToolButton,
)

TITLE_BAR_SIZE = 28


class StickyNoteWidget(QWidget):
    def __init__(self, note_id, content="", color="#FFEB3B", opacity=180, position=None, size=None, parent=None):
        super().__init__(parent)
        self.note_id = note_id
        self._content = content
        self._color = color
        self._opacity = opacity
        self._is_dragging = False
        self._drag_start_pos = QPoint()
        self._window_start_pos = QPoint()
        self._is_folded = False
        self._on_save_callback = None
        self._on_todo_callback = None
        self._button_position = "top"

        if position is None:
            position = QPoint(100, 100)
        if size is None:
            size = (300, 250)

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.setMinimumSize(300, 250)
        self.resize(*size)
        self.move(position)

        self._create_text_edit()
        self._init_top_layout()

        self._apply_color()
        self.show()

    def _create_text_edit(self):
        self.text_edit = QTextEdit()
        self.text_edit.setPlainText(self._content)
        self.text_edit.setFont(QFont("Microsoft YaHei", 14))
        self.text_edit.setLineWrapMode(QTextEdit.WidgetWidth)
        self.text_edit.setFrameStyle(0)
        self.text_edit.setStyleSheet(
            """
            QTextEdit {
                background: rgba(255, 255, 255, 0.4);
                border: none;
                padding: 8px;
                color: #333;
                border-radius: 4px;
            }
            QTextEdit:focus {
                outline: none;
                background: rgba(255, 255, 255, 0.6);
            }
            """
        )

    def _init_top_layout(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(3)

        buttons_layout = QHBoxLayout()
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        buttons_layout.setSpacing(4)
        buttons_layout.addStretch()

        self._create_buttons(buttons_layout)

        layout.addLayout(buttons_layout)
        layout.addWidget(self.text_edit, stretch=1)

    def _create_buttons(self, layout):
        btn_style = """
            QToolButton {
                background: rgba(255, 255, 255, 0.6);
                border: none;
                border-radius: 3px;
                font-size: 12px;
                color: #666;
                padding: 2px;
            }
            QToolButton:hover {
                background: rgba(0, 0, 0, 0.1);
            }
            """

        self.drag_btn = QToolButton()
        self.drag_btn.setText("📌")
        self.drag_btn.setFixedSize(22, 22)
        self.drag_btn.setStyleSheet(btn_style)
        self.drag_btn.installEventFilter(self)

        self.todo_btn = QToolButton()
        self.todo_btn.setText("📋")
        self.todo_btn.setFixedSize(22, 22)
        self.todo_btn.setStyleSheet(btn_style)
        self.todo_btn.clicked.connect(self._on_todo)

        self.fold_btn = QToolButton()
        self.fold_btn.setText("−")
        self.fold_btn.setFixedSize(22, 22)
        self.fold_btn.setStyleSheet(btn_style)
        self.fold_btn.clicked.connect(self._toggle_fold)

        layout.addWidget(self.drag_btn)
        layout.addWidget(self.todo_btn)
        layout.addWidget(self.fold_btn)

    def _apply_color(self):
        bg_color = QColor(self._color)
        r, g, b = bg_color.red(), bg_color.green(), bg_color.blue()

        style_sheet = f"StickyNoteWidget {{ background-color: rgba({r}, {g}, {b}, {self._opacity}); border-radius: 10px; }}"
        self.setStyleSheet(style_sheet)
        self.repaint()

    def set_color(self, color):
        self._color = color
        self._apply_color()

    def set_opacity(self, opacity):
        self._opacity = opacity
        self._apply_color()

    def paintEvent(self, event):
        if not self._is_folded:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)

            bg_color = QColor(self._color)
            r, g, b = bg_color.red(), bg_color.green(), bg_color.blue()

            brightness = (r * 299 + g * 587 + b * 114) / 1000
            border_color = QColor("#333333") if brightness > 200 else QColor("#CCCCCC")

            painter.setPen(QPen(border_color, 2))
            painter.setBrush(Qt.NoBrush)
            painter.drawRoundedRect(self.rect(), 10, 10)

        super().paintEvent(event)

    def set_button_position(self, position):
        if self._button_position == position:
            return

        old_width, old_height = self.width(), self.height()
        self._button_position = position

        if position in ("left", "right"):
            self.resize(350, 220)
        else:
            self.resize(300, 250)

        if position == "right":
            self.move(self.x() + old_width - self.width(), self.y())
        elif position == "bottom":
            self.move(self.x(), self.y() + old_height - self.height())

        old_layout = self.layout()
        if old_layout:
            old_layout.removeWidget(self.text_edit)
            self.text_edit.setParent(None)
            QWidget().setLayout(old_layout)

        if position == "top":
            layout = QVBoxLayout(self)
            layout.setContentsMargins(5, 5, 5, 5)
            layout.setSpacing(3)

            buttons_layout = QHBoxLayout()
            buttons_layout.setContentsMargins(0, 0, 0, 0)
            buttons_layout.setSpacing(4)
            buttons_layout.addStretch()

            self._create_buttons(buttons_layout)

            layout.addLayout(buttons_layout)
            layout.addWidget(self.text_edit)

        elif position == "bottom":
            layout = QVBoxLayout(self)
            layout.setContentsMargins(5, 5, 5, 5)
            layout.setSpacing(3)

            layout.addWidget(self.text_edit)

            buttons_layout = QHBoxLayout()
            buttons_layout.setContentsMargins(0, 0, 0, 0)
            buttons_layout.setSpacing(4)
            buttons_layout.addStretch()

            self._create_buttons(buttons_layout)

            layout.addLayout(buttons_layout)

        elif position == "left":
            layout = QHBoxLayout(self)
            layout.setContentsMargins(5, 5, 5, 5)
            layout.setSpacing(3)

            buttons_layout = QVBoxLayout()
            buttons_layout.setContentsMargins(0, 0, 0, 0)
            buttons_layout.setSpacing(2)
            buttons_layout.addStretch()

            self._create_buttons(buttons_layout)

            buttons_layout.addStretch()

            layout.addLayout(buttons_layout)
            layout.addWidget(self.text_edit)

        elif position == "right":
            layout = QHBoxLayout(self)
            layout.setContentsMargins(5, 5, 5, 5)
            layout.setSpacing(3)

            layout.addWidget(self.text_edit)

            buttons_layout = QVBoxLayout()
            buttons_layout.setContentsMargins(0, 0, 0, 0)
            buttons_layout.setSpacing(2)
            buttons_layout.addStretch()

            self._create_buttons(buttons_layout)

            buttons_layout.addStretch()

            layout.addLayout(buttons_layout)

        self._apply_color()
        self.show()
        self.raise_()

    def _toggle_fold(self):
        self._is_folded = not self._is_folded
        if self._is_folded:
            self._unfolded_size = (self.width(), self.height())
            self.fold_btn.setText("+")
            self.text_edit.hide()
            if self._button_position in ("top", "bottom"):
                old_height = self.height()
                new_height = TITLE_BAR_SIZE + 10
                self.setFixedHeight(new_height)
                if self._button_position == "bottom":
                    self.move(self.x(), self.y() + old_height - new_height)
            else:
                old_width = self.width()
                new_width = TITLE_BAR_SIZE + 10
                self.setFixedWidth(new_width)
                if self._button_position == "right":
                    self.move(self.x() + old_width - new_width, self.y())
        else:
            self.fold_btn.setText("−")
            self.text_edit.show()
            if hasattr(self, '_unfolded_size'):
                self.setFixedSize(*self._unfolded_size)
            elif self._button_position in ("top", "bottom"):
                self.setFixedSize(300, 250)
            else:
                self.setFixedSize(350, 220)
            if self._button_position == "bottom" or self._button_position == "right":
                old_pos = self.pos()
                if self._button_position == "bottom":
                    self.move(old_pos.x(), old_pos.y() - self.height() + TITLE_BAR_SIZE + 10)
                else:
                    self.move(old_pos.x() - self.width() + TITLE_BAR_SIZE + 10, old_pos.y())
        self._save()

    def _on_todo(self):
        if self._on_todo_callback:
            self._on_todo_callback()

    def _toggle_drag_mode(self):
        pass

    def _on_text_changed(self):
        self._content = self.text_edit.toPlainText()
        self._save()

    def _save(self):
        if self._on_save_callback:
            self._on_save_callback(
                self.note_id,
                {
                    "content": self._content,
                    "color": self._color,
                    "opacity": self._opacity,
                    "x": self.x(),
                    "y": self.y(),
                    "width": self.width(),
                    "height": self.height(),
                    "is_folded": self._is_folded,
                },
            )

    def eventFilter(self, obj, event):
        if obj == self.drag_btn and event.type() == QEvent.MouseButtonPress:
            if event.button() == Qt.LeftButton:
                self._is_dragging = True
                self._drag_start_pos = event.globalPos()
                self._window_start_pos = self.pos()
                self.setCursor(Qt.ClosedHandCursor)
                self.drag_btn.setText("✨")
                self.grabMouse()
                return True
        return super().eventFilter(obj, event)

    def mousePressEvent(self, event):
        pass

    def mouseMoveEvent(self, event):
        if self._is_dragging:
            delta = event.globalPos() - self._drag_start_pos
            self.move(self._window_start_pos + delta)
            self.drag_btn.setText("✨")

    def mouseReleaseEvent(self, event):
        if self._is_dragging:
            self._is_dragging = False
            self.setCursor(Qt.ArrowCursor)
            self.drag_btn.setText("📌")
            self.releaseMouse()
            self._save()

    def set_save_callback(self, callback):
        self._on_save_callback = callback

    def set_todo_callback(self, callback):
        self._on_todo_callback = callback
