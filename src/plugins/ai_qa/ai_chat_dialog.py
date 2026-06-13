"""AI 聊天对话框 - 类似微信聊天界面"""

import json
import threading
import urllib.request

from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QFont, QTextCursor
from PyQt5.QtWidgets import (
    QApplication,
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


class ChatBubble(QTextEdit):
    """聊天气泡控件"""

    def __init__(self, text, is_user=True, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setPlainText(text)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        font = QFont("Microsoft YaHei", 12)
        self.setFont(font)

        self._is_user = is_user
        self._update_style()

    def _update_style(self):
        if self._is_user:
            bg = "#95EC69"  # 微信绿色
            align = "right"
        else:
            bg = "#FFFFFF"
            align = "left"

        self.setStyleSheet(f"""
            QTextEdit {{
                background: {bg};
                border: none;
                border-radius: 12px;
                padding: 10px 14px;
                color: #333;
                font-size: 13px;
            }}
        """)

    def adjust_height(self):
        doc = self.document()
        doc.setTextWidth(self.width() - 28)
        height = int(doc.size().height()) + 24
        self.setFixedHeight(min(height, 400))


class ChatMessageWidget(QWidget):
    """单条聊天消息（头像 + 气泡）"""

    def __init__(self, text, is_user=True, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 4, 10, 4)
        layout.setSpacing(8)

        # 头像标签
        avatar = QLabel()
        avatar.setFixedSize(36, 36)
        avatar.setAlignment(Qt.AlignCenter)
        avatar.setStyleSheet("""
            QLabel {
                border-radius: 18px;
                font-size: 18px;
                background: #f0f0f0;
            }
        """)
        if is_user:
            avatar.setText("👤")
        else:
            avatar.setText("🤖")

        # 气泡
        bubble = ChatBubble(text, is_user)
        bubble.setMinimumWidth(80)
        bubble.setMaximumWidth(460)

        if is_user:
            layout.addStretch()
            layout.addWidget(bubble)
            layout.addWidget(avatar)
        else:
            layout.addWidget(avatar)
            layout.addWidget(bubble)
            layout.addStretch()

        # 存引用以便后续调整
        self._bubble = bubble

    def adjust_bubble(self):
        self._bubble.adjust_height()


class AIChatDialog(QDialog):
    """AI 聊天对话框"""

    response_ready = pyqtSignal(str, str)  # (user_msg, ai_response)

    def __init__(self, config: dict, parent=None):
        super().__init__(parent)
        self.config = config
        self.messages_history = []  # OpenAI messages 格式
        self._pending_user_msg = ""

        self.setWindowTitle("AI 问答")
        self.setMinimumSize(560, 640)
        self.resize(560, 640)

        self.response_ready.connect(self._on_response)

        self._init_ui()
        self._apply_style()

        # 添加欢迎消息
        model_name = config.get("model", "AI")
        self._add_message(f"你好！我是 {model_name}，有什么可以帮你的？", is_user=False)

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

        model_name = self.config.get("model", "AI")
        title = QLabel(f"🤖 {model_name}")
        title.setStyleSheet("color: #eee; font-size: 15px; font-weight: bold;")
        header_layout.addWidget(title)
        header_layout.addStretch()

        clear_btn = QPushButton("清空对话")
        clear_btn.setStyleSheet("""
            QPushButton {
                background: #444; color: #ccc; border: none;
                border-radius: 4px; padding: 4px 12px; font-size: 12px;
            }
            QPushButton:hover { background: #555; }
        """)
        clear_btn.setAutoDefault(False)
        clear_btn.setDefault(False)
        clear_btn.clicked.connect(self._clear_chat)
        header_layout.addWidget(clear_btn)

        layout.addWidget(header)

        # 聊天内容区域
        self.chat_area = QWidget()
        self.chat_layout = QVBoxLayout(self.chat_area)
        self.chat_layout.setContentsMargins(0, 8, 0, 8)
        self.chat_layout.setSpacing(4)
        self.chat_layout.addStretch()

        from PyQt5.QtWidgets import QScrollArea, QFrame
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.NoFrame)
        self.scroll_area.setWidget(self.chat_area)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                background: #EDEDED;
                border: none;
            }
        """)
        layout.addWidget(self.scroll_area, 1)

        # 底部输入栏
        input_bar = QWidget()
        input_bar.setStyleSheet("""
            QWidget {
                background: #F5F5F5;
                border-top: 1px solid #ddd;
            }
        """)
        input_layout = QHBoxLayout(input_bar)
        input_layout.setContentsMargins(12, 10, 12, 10)
        input_layout.setSpacing(8)

        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("输入你的问题，按回车发送...")
        self.input_field.setMinimumHeight(40)
        self.input_field.setStyleSheet("""
            QLineEdit {
                background: white;
                border: 1px solid #ddd;
                border-radius: 20px;
                padding: 8px 16px;
                font-size: 14px;
                color: #333;
            }
            QLineEdit:focus {
                border-color: #07C160;
            }
        """)
        self.input_field.returnPressed.connect(self._send_message)
        input_layout.addWidget(self.input_field)

        self.send_btn = QPushButton("发送")
        self.send_btn.setFixedSize(64, 40)
        self.send_btn.setStyleSheet("""
            QPushButton {
                background: #07C160;
                color: white;
                border: none;
                border-radius: 20px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover { background: #06AD56; }
            QPushButton:pressed { background: #059B4C; }
            QPushButton:disabled { background: #aaa; }
        """)
        self.send_btn.setAutoDefault(False)
        self.send_btn.clicked.connect(self._send_message)
        input_layout.addWidget(self.send_btn)

        layout.addWidget(input_bar)

    def _apply_style(self):
        self.setStyleSheet("""
            QDialog {
                background: #EDEDED;
            }
        """)

    def keyPressEvent(self, event):
        """拦截回车键，防止触发任何按钮的默认行为"""
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            # 如果焦点在输入框，让输入框自己处理
            if self.input_field.hasFocus():
                self.input_field.returnPressed.emit()
            return  # 其他情况不处理，防止触发按钮
        super().keyPressEvent(event)

    def _add_message(self, text, is_user=True):
        """添加一条消息到聊天区域"""
        widget = ChatMessageWidget(text, is_user)
        # 插入到 stretch 之前
        count = self.chat_layout.count()
        self.chat_layout.insertWidget(count - 1, widget)

        # 调整气泡大小
        QTimer.singleShot(10, widget.adjust_bubble)

        # 滚动到底部
        QTimer.singleShot(20, self._scroll_to_bottom)

    def _scroll_to_bottom(self):
        sb = self.scroll_area.verticalScrollBar()
        sb.setValue(sb.maximum())

    def _send_message(self):
        """发送消息"""
        text = self.input_field.text().strip()
        if not text:
            return

        self.input_field.clear()
        self.send_btn.setEnabled(False)

        # 显示用户消息
        self._add_message(text, is_user=True)
        self._pending_user_msg = text

        # 添加到历史
        self.messages_history.append({"role": "user", "content": text})

        # 显示加载中
        self._loading_widget = ChatMessageWidget("正在思考...", is_user=False)
        count = self.chat_layout.count()
        self.chat_layout.insertWidget(count - 1, self._loading_widget)
        QTimer.singleShot(10, self._loading_widget.adjust_bubble)
        QTimer.singleShot(20, self._scroll_to_bottom)

        # 在后台线程调用 API
        thread = threading.Thread(target=self._call_api, daemon=True)
        thread.start()

    def _call_api(self):
        """后台调用 OpenAI 兼容 API"""
        try:
            base_url = self.config.get("base_url", "https://api.deepseek.com").rstrip("/")
            api_key = self.config.get("api_key", "")
            model = self.config.get("model", "deepseek-chat")
            system_prompt = self.config.get("system_prompt", "你是一个有用的AI助手。请简洁明了地回答问题。")

            url = f"{base_url}/v1/chat/completions"

            messages = [{"role": "system", "content": system_prompt}]
            messages.extend(self.messages_history)

            payload = json.dumps({
                "model": model,
                "messages": messages,
                "stream": False,
                "temperature": 0.7,
                "max_tokens": 2000,
            }).encode("utf-8")

            req = urllib.request.Request(
                url,
                data=payload,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key}",
                },
                method="POST",
            )

            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                reply = data["choices"][0]["message"]["content"].strip()

            self.response_ready.emit(self._pending_user_msg, reply)

        except Exception as e:
            error_msg = f"请求失败: {e}"
            self.response_ready.emit(self._pending_user_msg, error_msg)

    def _on_response(self, user_msg, ai_response):
        """主线程处理 AI 响应"""
        # 安全移除加载中控件
        if hasattr(self, '_loading_widget') and self._loading_widget is not None:
            try:
                self._loading_widget.hide()
                self._loading_widget.setParent(None)
                self._loading_widget.deleteLater()
            except RuntimeError:
                pass  # C++ 对象已被回收
            self._loading_widget = None

        # 显示 AI 回复
        self._add_message(ai_response, is_user=False)

        # 添加到历史
        self.messages_history.append({"role": "assistant", "content": ai_response})

        self.send_btn.setEnabled(True)
        self.input_field.setFocus()

    def _clear_chat(self):
        """清空聊天记录"""
        self.messages_history.clear()

        # 移除所有消息控件（保留 stretch）
        while self.chat_layout.count() > 1:
            item = self.chat_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        model_name = self.config.get("model", "AI")
        self._add_message(f"对话已清空。我是 {model_name}，请继续提问。", is_user=False)