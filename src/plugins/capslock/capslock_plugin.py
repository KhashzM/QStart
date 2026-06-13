"""大小写状态监测插件 - 监测 Caps Lock 和 Num Lock 状态变化"""

import ctypes
import time
from typing import Any, Dict, List, Optional

from plugin_base import PluginBase


class CapsLockPlugin(PluginBase):
    """大小写状态监测插件：实时监测 Caps Lock 和 Num Lock 状态变化并发送通知"""

    def __init__(self):
        super().__init__()
        self._caps_lock_state = False
        self._num_lock_state = False
        self._monitoring = False
        self._monitor_thread = None
        self._last_caps_notify_time = 0
        self._last_num_notify_time = 0
        self._notify_cooldown = 300  # 通知冷却时间（毫秒）

    @property
    def name(self) -> str:
        return "大小写监测"

    @property
    def description(self) -> str:
        return "实时监测 Caps Lock 和 Num Lock 状态变化，状态切换时发送通知提醒"

    @property
    def version(self) -> str:
        return "1.2.0"

    @property
    def author(self) -> str:
        return "QStart"

    @property
    def keywords(self) -> list:
        return ["caps", "lock", "大小写", "capslock"]

    @property
    def trigger_mode(self) -> str:
        return "background"

    def _get_caps_lock_state(self) -> bool:
        """获取 Caps Lock 状态"""
        try:
            return bool(ctypes.windll.user32.GetKeyState(0x14) & 1)
        except:
            return False

    def _get_num_lock_state(self) -> bool:
        """获取 Num Lock 状态"""
        try:
            return bool(ctypes.windll.user32.GetKeyState(0x90) & 1)
        except:
            return False

    def _can_notify_caps(self) -> bool:
        """检查是否可以发送 Caps Lock 通知"""
        current_time = time.time() * 1000
        if current_time - self._last_caps_notify_time >= self._notify_cooldown:
            self._last_caps_notify_time = current_time
            return True
        return False

    def _can_notify_num(self) -> bool:
        """检查是否可以发送 Num Lock 通知"""
        current_time = time.time() * 1000
        if current_time - self._last_num_notify_time >= self._notify_cooldown:
            self._last_num_notify_time = current_time
            return True
        return False

    def _send_notification(self, title: str, message: str):
        """发送通知"""
        try:
            settings = self.get_settings()
            duration = int(settings.get("notify_duration", 1500))

            if hasattr(self, "_plugin_manager"):
                notif_plugin = self._plugin_manager.get_plugin("通知中心")
                if notif_plugin:
                    notif_plugin.send_notification_from("大小写监测", title, message, duration)
                    print(f"[{self.name}] 已发送通知: {title} - {message}")
        except Exception as e:
            print(f"[{self.name}] 发送通知失败: {e}")

    def _monitor_loop(self):
        """监测循环"""
        while self._monitoring:
            try:
                settings = self.get_settings()
                caps_enabled = settings.get("notify_caps", True)
                num_enabled = settings.get("notify_num", True)

                if caps_enabled:
                    new_caps = self._get_caps_lock_state()
                    if new_caps != self._caps_lock_state:
                        print(f"[{self.name}] Caps Lock 状态变化: {self._caps_lock_state} -> {new_caps}")
                        self._caps_lock_state = new_caps
                        if self._can_notify_caps():
                            if new_caps:
                                self._send_notification("🟢A 大写锁定", "已开启")
                            else:
                                self._send_notification("🔴a 小写模式", "已关闭")

                if num_enabled:
                    new_num = self._get_num_lock_state()
                    if new_num != self._num_lock_state:
                        print(f"[{self.name}] Num Lock 状态变化: {self._num_lock_state} -> {new_num}")
                        self._num_lock_state = new_num
                        if self._can_notify_num():
                            if new_num:
                                self._send_notification("🔢 数字锁定", "已开启")
                            else:
                                self._send_notification("🔢 数字锁定", "已关闭")

                time.sleep(0.1)
            except Exception as e:
                print(f"[{self.name}] 监测异常: {e}")
                time.sleep(0.5)

    def get_settings_schema(self) -> list:
        """设置 schema"""
        return [
            {
                "key": "notify_caps",
                "label": "Caps Lock 通知",
                "type": "checkbox",
                "default": True,
                "description": "当 Caps Lock 状态变化时发送通知",
            },
            {
                "key": "notify_num",
                "label": "Num Lock 通知",
                "type": "checkbox",
                "default": True,
                "description": "当 Num Lock 状态变化时发送通知",
            },
            {
                "key": "notify_duration",
                "label": "通知显示时长",
                "type": "select",
                "options": [
                    {"value": "500", "label": "0.5秒"},
                    {"value": "1000", "label": "1秒"},
                    {"value": "1500", "label": "1.5秒"},
                    {"value": "2000", "label": "2秒"},
                    {"value": "3000", "label": "3秒"},
                ],
                "default": "1500",
                "description": "通知显示的时间长度",
            },
        ]

    def on_load(self) -> None:
        """加载时初始化状态"""
        self._caps_lock_state = self._get_caps_lock_state()
        self._num_lock_state = self._get_num_lock_state()
        print(f"[{self.name}] 已加载，当前状态: Caps={self._caps_lock_state}, Num={self._num_lock_state}")

    def on_enable(self) -> None:
        """启用时开始监测"""
        if self._monitoring:
            return

        try:
            if hasattr(self, "_plugin_manager"):
                notif_plugin = self._plugin_manager.get_plugin("通知中心")
                if notif_plugin:
                    notif_plugin.register_sender(
                        "大小写监测",
                        "监测 Caps Lock 和 Num Lock 状态变化",
                        True
                    )
        except Exception as e:
            print(f"[{self.name}] 注册通知发送者失败: {e}")

        self._monitoring = True
        import threading
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()
        print(f"[{self.name}] 监测已启动")

    def on_disable(self) -> None:
        """禁用时停止监测"""
        self._monitoring = False
        print(f"[{self.name}] 监测已停止")

    def on_unload(self) -> None:
        """卸载时清理"""
        self._monitoring = False
        print(f"[{self.name}] 已卸载")

    def search(self, query: str) -> List[Dict[str, Any]]:
        return []

    def preview(self, query: str) -> str:
        return "大小写状态监测插件"

    def handle(self, query: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        return {
            "type": "display",
            "message": f"🔠 Caps Lock: {'开启' if self._caps_lock_state else '关闭'}\n🔢 Num Lock: {'开启' if self._num_lock_state else '关闭'}",
            "data": None,
            "hide_window": True,
        }
