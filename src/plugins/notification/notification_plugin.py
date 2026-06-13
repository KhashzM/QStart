"""通知插件 - 提供统一的通知接口"""

from typing import Any, Dict, List, Optional

from PyQt5.QtCore import pyqtSlot
from plugin_base import PluginBase


class NotificationPlugin(PluginBase):
    """通知插件：提供统一的通知接口"""

    def __init__(self):
        super().__init__()
        self._window = None
        self._registered_senders: Dict[str, Dict[str, Any]] = {}
        self._init_window()

    def _init_window(self):
        """初始化通知窗口（在主线程中）"""
        from PyQt5.QtCore import Qt, QTimer
        from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout

        self._container = QWidget()
        self._container.setObjectName("notification-container")
        self._container.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool
        )
        self._container.setAttribute(Qt.WA_TranslucentBackground)
        self._container.setAttribute(Qt.WA_ShowWithoutActivating)
        self._container.setAutoFillBackground(False)

        layout = QVBoxLayout(self._container)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(4)

        self._title_label = QLabel()
        self._title_label.setStyleSheet("color: #ffffff; font-size: 14px; font-weight: bold;")
        layout.addWidget(self._title_label)

        self._message_label = QLabel()
        self._message_label.setStyleSheet("color: #e0e0e0; font-size: 13px;")
        self._message_label.setWordWrap(True)
        layout.addWidget(self._message_label)

        self._container.setStyleSheet("""
            QWidget#notification-container {
                background-color: rgba(35, 35, 35, 230);
                border-radius: 10px;
                border: 1px solid rgba(80, 80, 80, 150);
            }
        """)

        self._hide_timer = QTimer()
        self._hide_timer.setSingleShot(True)
        self._hide_timer.timeout.connect(self._hide)

        self._container.hide()

    def _hide(self):
        """隐藏通知窗口"""
        self._container.hide()

    @property
    def name(self) -> str:
        return "通知中心"

    @property
    def description(self) -> str:
        return "提供统一的通知接口，支持位置和时长设置"

    @property
    def version(self) -> str:
        return "3.0.0"

    @property
    def author(self) -> str:
        return "QStart"

    @property
    def keywords(self) -> list:
        return ["notify", "通知"]

    @property
    def trigger_mode(self) -> str:
        return "action"

    def _convert_position_value(self, value) -> int:
        """兼容性处理：转换旧值为新的整数值"""
        if isinstance(value, int):
            return value
        value = str(value).lower()
        if value in ("left", "最左侧"):
            return 0
        elif value in ("center", "居中"):
            return 2
        elif value in ("right", "最右侧"):
            return 4
        elif value == "1":
            return 1
        elif value == "3":
            return 3
        try:
            return int(value)
        except:
            return 3

    def _get_display_settings(self) -> dict:
        """获取显示设置（带兼容性处理）"""
        settings = self.get_settings()
        
        position_x = self._convert_position_value(settings.get("position_x", "3"))
        position_y = self._convert_position_value(settings.get("position_y", "0"))
        
        try:
            duration = int(settings.get("duration", "2000"))
        except:
            duration = 2000

        return {
            "position_x": position_x,
            "position_y": position_y,
            "duration": duration,
        }

    def get_settings_schema(self) -> list:
        """动态生成设置 schema"""
        schema = [
            {
                "key": "enabled",
                "label": "启用通知系统",
                "type": "checkbox",
                "default": True,
                "description": "总开关，关闭后所有通知都不会显示",
            },
            {
                "key": "_section_display",
                "label": "显示设置",
                "type": "_section_header",
                "description": "配置通知窗口的显示效果",
            },
            {
                "key": "position_x",
                "label": "水平位置",
                "type": "select",
                "options": [
                    {"value": "0", "label": "最左侧"},
                    {"value": "1", "label": "左侧"},
                    {"value": "2", "label": "居中"},
                    {"value": "3", "label": "右侧"},
                    {"value": "4", "label": "最右侧"},
                ],
                "default": "3",
                "description": "通知在屏幕水平方向的位置（共5档）",
            },
            {
                "key": "position_y",
                "label": "垂直位置",
                "type": "select",
                "options": [
                    {"value": "0", "label": "最顶部"},
                    {"value": "1", "label": "顶部"},
                    {"value": "2", "label": "中部"},
                    {"value": "3", "label": "底部"},
                    {"value": "4", "label": "最底部"},
                ],
                "default": "0",
                "description": "通知在屏幕垂直方向的位置（共5档）",
            },
            {
                "key": "duration",
                "label": "显示时长",
                "type": "select",
                "options": [
                    {"value": "500", "label": "0.5秒"},
                    {"value": "1000", "label": "1秒"},
                    {"value": "1500", "label": "1.5秒"},
                    {"value": "2000", "label": "2秒"},
                    {"value": "3000", "label": "3秒"},
                ],
                "default": "2000",
                "description": "通知自动消失的时间",
            },
        ]

        if self._registered_senders:
            schema.append({
                "key": "_section_senders",
                "label": "插件通知开关",
                "type": "_section_header",
                "description": "以下是已向通知中心注册的插件",
            })

            for sender_name in sorted(self._registered_senders.keys()):
                info = self._registered_senders[sender_name]
                schema.append({
                    "key": f"sender_{sender_name}",
                    "label": f"📢 {sender_name}",
                    "type": "checkbox",
                    "default": info.get("default_enabled", True),
                    "check_label": info.get("description", "允许此插件发送通知"),
                })

        schema.append({
            "key": "_section_test",
            "label": "测试功能",
            "type": "_section_header",
            "description": "使用下方按钮验证通知功能",
        })

        schema.append({
            "key": "test_button",
            "label": "测试通知",
            "type": "button",
            "text": "🧪 发送测试通知",
            "callback_key": "on_test_notification",
            "description": "点击此按钮发送一条测试通知",
        })

        return schema

    def register_sender(self, sender_name: str, description: str = "", default_enabled: bool = True) -> None:
        """注册一个通知发送者"""
        if sender_name not in self._registered_senders:
            self._registered_senders[sender_name] = {
                "description": description,
                "default_enabled": default_enabled,
            }
            print(f"[通知中心] 插件「{sender_name}」已注册通知功能")

    def is_sender_enabled(self, sender_name: str) -> bool:
        """检查某个发送者的通知是否被启用"""
        settings = self.get_settings()
        if not settings.get("enabled", True):
            return False
        key = f"sender_{sender_name}"
        if key in settings:
            return bool(settings[key])
        sender_info = self._registered_senders.get(sender_name, {})
        return sender_info.get("default_enabled", True)

    @pyqtSlot(str, str, int, int, int)
    def _show_notification(self, title: str, message: str, duration: int, position_x: int, position_y: int):
        """在主线程中显示通知"""
        self._title_label.setText(title)
        self._message_label.setText(message)

        self._container.adjustSize()
        self._container.resize(min(self._container.width(), 320), self._container.height())

        from PyQt5.QtWidgets import QApplication
        screen_geo = QApplication.desktop().screenGeometry()
        window_geo = self._container.frameGeometry()

        margin = 20
        spacing = 150

        x_positions = [
            margin,
            margin + spacing,
            (screen_geo.width() - window_geo.width()) // 2,
            screen_geo.width() - window_geo.width() - spacing,
            screen_geo.width() - window_geo.width() - margin
        ]
        y_positions = [
            80,
            80 + spacing,
            (screen_geo.height() - window_geo.height()) // 2,
            screen_geo.height() - window_geo.height() - spacing,
            screen_geo.height() - window_geo.height() - margin
        ]

        x = x_positions[min(max(position_x, 0), 4)]
        y = y_positions[min(max(position_y, 0), 4)]

        self._container.move(x, y)
        self._container.show()
        self._container.update()

        if self._hide_timer.isActive():
            self._hide_timer.stop()
        
        if duration > 0:
            self._hide_timer.start(duration)

    def send_notification_from(self, sender_name: str, title: str, message: str,
                                 duration: int = None) -> None:
        """其他插件通过此接口发送通知"""
        settings = self.get_settings()
        if not settings.get("enabled", True):
            return
        if not self.is_sender_enabled(sender_name):
            return

        display = self._get_display_settings()
        final_duration = duration if duration is not None else display["duration"]

        from PyQt5.QtCore import QMetaObject, Qt, Q_ARG
        QMetaObject.invokeMethod(
            self, "_show_notification", Qt.QueuedConnection,
            Q_ARG(str, title),
            Q_ARG(str, message),
            Q_ARG(int, final_duration),
            Q_ARG(int, display["position_x"]),
            Q_ARG(int, display["position_y"])
        )

    def send_notification(self, title: str, message: str, duration: int = None) -> None:
        """简化接口"""
        self.send_notification_from("通知中心", title, message, duration)

    def show_message(self, message: str, title: str = "通知", duration: int = None):
        """简化的通知接口"""
        self.send_notification_from("通知中心", title, message, duration)

    def on_test_notification(self):
        """测试通知按钮的回调"""
        self.send_notification("✅ 测试通知", "通知功能正常工作！")
        print("[通知中心] 已发送测试通知")

    def on_load(self) -> None:
        print(f"[{self.name}] 通知系统已就绪")

    def on_unload(self) -> None:
        self._container.hide()
        print(f"[{self.name}] 通知系统已卸载")

    def on_enable(self) -> None:
        print(f"[{self.name}] 通知系统已启用")

    def on_disable(self) -> None:
        self._container.hide()
        print(f"[{self.name}] 通知系统已禁用")

    def search(self, query: str) -> List[Dict[str, Any]]:
        return []

    def preview(self, query: str) -> str:
        q = query.strip().lower()
        if q == "":
            return "测试通知功能（输入 notify test 发送测试通知）"
        if q == "test":
            return "发送测试通知"
        return f"发送通知: {q}"

    def handle(self, query: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        q = query.strip()

        if not q or q.lower() == "test":
            self.send_notification("测试通知", "这是一条测试通知消息，通知功能正常工作！")
            return {
                "type": "display",
                "message": "📢 已发送测试通知",
                "data": None,
                "hide_window": True,
            }

        parts = q.split("|", 1)
        if len(parts) == 2:
            title = parts[0].strip()
            message = parts[1].strip()
        else:
            title = "通知"
            message = q

        self.send_notification(title, message)
        return {
            "type": "display",
            "message": f"📢 已发送通知: {title}",
            "data": None,
            "hide_window": True,
        }
