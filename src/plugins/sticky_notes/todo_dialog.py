from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QCheckBox,
    QWidget,
    QLabel,
    QSizePolicy,
    QHeaderView,
)


class TodoDialog(QDialog):
    def __init__(self, todos=None, parent=None):
        super().__init__(parent)
        self._todos = todos if todos is not None else []
        self._on_save_callback = None

        self._init_ui()

    def _init_ui(self):
        self.setWindowTitle("待办事项")
        self.setFixedSize(400, 500)
        self.setWindowFlags(Qt.Tool | Qt.WindowStaysOnTopHint)

        self.setStyleSheet(
            """
            TodoDialog {
                background: white;
            }
            #title_label {
                background: transparent;
            }
            #count_label {
                background: transparent;
                color: #666;
            }
            QLineEdit {
                border: 1px solid #ddd;
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border-color: #4CAF50;
                outline: none;
            }
            QTableWidget {
                background: white;
                border: 1px solid #ddd;
                border-radius: 8px;
                gridline-color: #eee;
                outline: none;
            }
            QTableWidget::item {
                padding: 10px;
                border: none;
                outline: none;
            }
            QTableWidget::item:hover {
                background: #f5f5f5;
            }
            QTableWidget::item:selected {
                background: #E8F5E9;
                color: #333;
            }
            QHeaderView::section {
                background: #f8f8f8;
                border: none;
                border-bottom: 1px solid #ddd;
                padding: 8px;
                font-weight: bold;
                color: #666;
            }
            """
        )

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(10)

        title_label = QLabel("📝 待办事项")
        title_label.setObjectName("title_label")
        title_label.setFont(QFont("Microsoft YaHei", 16, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)

        self.todo_count_label = QLabel(f"共 {len(self._todos)} 项（完成 {self._get_completed_count()} 项）")
        self.todo_count_label.setObjectName("count_label")
        self.todo_count_label.setFont(QFont("Microsoft YaHei", 12))
        self.todo_count_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.todo_count_label)

        input_layout = QHBoxLayout()
        input_layout.setSpacing(8)

        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("输入新的待办事项...")
        self.input_field.setFont(QFont("Microsoft YaHei", 13))
        self.input_field.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.input_field.returnPressed.connect(self._add_todo)
        input_layout.addWidget(self.input_field)

        self.add_btn = QPushButton("添加")
        self.add_btn.setFont(QFont("Microsoft YaHei", 12))
        self.add_btn.setStyleSheet(
            """
            QPushButton {
                background: #4CAF50;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 20px;
                min-width: 80px;
            }
            QPushButton:hover {
                background: #45a049;
            }
            QPushButton:pressed {
                background: #388E3C;
            }
            """
        )
        self.add_btn.clicked.connect(self._add_todo)
        input_layout.addWidget(self.add_btn)

        main_layout.addLayout(input_layout)

        self.todo_table = QTableWidget()
        self.todo_table.setColumnCount(3)
        self.todo_table.setHorizontalHeaderLabels(["", "待办事项", ""])
        self.todo_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.todo_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.todo_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Fixed)
        self.todo_table.setColumnWidth(0, 40)
        self.todo_table.setColumnWidth(2, 40)
        self.todo_table.verticalHeader().setVisible(False)
        self.todo_table.setSelectionMode(QTableWidget.SingleSelection)
        self.todo_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.todo_table.setFont(QFont("Microsoft YaHei", 13))
        main_layout.addWidget(self.todo_table)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        self.clear_completed_btn = QPushButton("清除已完成")
        self.clear_completed_btn.setFont(QFont("Microsoft YaHei", 12))
        self.clear_completed_btn.setStyleSheet(
            """
            QPushButton {
                background: #ff9800;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background: #f57c00;
            }
            QPushButton:pressed {
                background: #E65100;
            }
            """
        )
        self.clear_completed_btn.clicked.connect(self._clear_completed)

        self.clear_all_btn = QPushButton("清空全部")
        self.clear_all_btn.setFont(QFont("Microsoft YaHei", 12))
        self.clear_all_btn.setStyleSheet(
            """
            QPushButton {
                background: #f44336;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background: #d32f2f;
            }
            QPushButton:pressed {
                background: #C62828;
            }
            """
        )
        self.clear_all_btn.clicked.connect(self._clear_all)

        btn_layout.addStretch()
        btn_layout.addWidget(self.clear_completed_btn)
        btn_layout.addWidget(self.clear_all_btn)
        btn_layout.addStretch()
        main_layout.addLayout(btn_layout)

        self._load_todos()

    def _get_completed_count(self):
        return sum(1 for t in self._todos if t.get("done", False))

    def _load_todos(self):
        self.todo_table.setRowCount(0)
        for row, todo in enumerate(self._todos):
            self.todo_table.insertRow(row)

            checkbox = QCheckBox()
            checkbox.setChecked(todo.get("done", False))
            checkbox.stateChanged.connect(
                lambda state, t=todo: self._toggle_todo(t, state == Qt.Checked)
            )
            checkbox_widget = QWidget()
            checkbox_layout = QHBoxLayout(checkbox_widget)
            checkbox_layout.setContentsMargins(0, 0, 0, 0)
            checkbox_layout.setAlignment(Qt.AlignCenter)
            checkbox_layout.addWidget(checkbox)
            self.todo_table.setCellWidget(row, 0, checkbox_widget)

            text_item = QTableWidgetItem(todo.get("text", ""))
            text_item.setFont(QFont("Microsoft YaHei", 13))
            if todo.get("done", False):
                text_item.setForeground(Qt.gray)
            else:
                text_item.setForeground(Qt.black)
            text_item.setFlags(text_item.flags() & ~Qt.ItemIsEditable)
            self.todo_table.setItem(row, 1, text_item)

            delete_btn = QPushButton("✕")
            delete_btn.setFixedSize(24, 24)
            delete_btn.setStyleSheet(
                """
                QPushButton {
                    background: transparent;
                    border: none;
                    color: #999;
                    font-size: 12px;
                }
                QPushButton:hover {
                    color: #f44336;
                }
                """
            )
            delete_btn.clicked.connect(lambda checked, t=todo: self._delete_todo(t))
            delete_widget = QWidget()
            delete_layout = QHBoxLayout(delete_widget)
            delete_layout.setContentsMargins(0, 0, 0, 0)
            delete_layout.setAlignment(Qt.AlignCenter)
            delete_layout.addWidget(delete_btn)
            self.todo_table.setCellWidget(row, 2, delete_widget)

            self.todo_table.setRowHeight(row, 40)

        self._update_count()

    def _add_todo(self):
        text = self.input_field.text().strip()
        if not text:
            return

        new_todo = {
            "id": str(len(self._todos) + 1),
            "text": text,
            "done": False,
        }
        self._todos.append(new_todo)
        self._load_todos()
        self.input_field.clear()
        self._save()

    def _toggle_todo(self, todo, done):
        todo["done"] = done
        self._load_todos()
        self._save()

    def _delete_todo(self, todo):
        self._todos = [t for t in self._todos if t["id"] != todo["id"]]
        self._load_todos()
        self._save()

    def _clear_completed(self):
        self._todos = [t for t in self._todos if not t.get("done", False)]
        self._load_todos()
        self._save()

    def _clear_all(self):
        self._todos = []
        self._load_todos()
        self._save()

    def _update_count(self):
        total = len(self._todos)
        completed = self._get_completed_count()
        self.todo_count_label.setText(f"共 {total} 项（完成 {completed} 项）")

    def _save(self):
        if self._on_save_callback:
            self._on_save_callback(self._todos)

    def set_save_callback(self, callback):
        self._on_save_callback = callback

    def get_todos(self):
        return self._todos