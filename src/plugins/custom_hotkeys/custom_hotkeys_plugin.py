"""自定义热键插件 - 注册任意快捷键打开不同软件"""

import json
import os
import subprocess
from typing import Any, Dict, List, Optional

from plugin_base import PluginBase


class CustomHotkeysPlugin(PluginBase):
    """自定义热键插件：允许用户配置任意快捷键打开指定程序

    通过 notify senders 命令查看已注册的通知发送者
    通过通知中心设置页面可以管理每个插件的通知开关
    """

    def __init__(self):
        super().__init__()
        self._hotkeys: List[Dict[str, Any]] = []
        self._registered_handles = []
        self._keyboard_available = False
        self._dialog = None

        try:
            import keyboard
            self._keyboard_available = True
            self._keyboard_module = keyboard
        except ImportError:
            self._keyboard_module = None

    @property
    def name(self) -> str:
        return "自定义热键"

    @property
    def description(self) -> str:
        return "配置任意快捷键打开指定程序，热键触发时通过通知中心提示"

    @property
    def version(self) -> str:
        return "2.0.0"

    @property
    def author(self) -> str:
        return "QStart"

    @property
    def keywords(self) -> list:
        return ["hk", "hotkey", "热键", "快捷键"]

    @property
    def trigger_mode(self) -> str:
        return "action"

    def get_settings_schema(self) -> list:
        # 返回一个虚拟配置项，让设置按钮保持可用
        # 实际的热键管理通过独立对话框进行
        return [
            {
                "key": "open_manager",
                "label": "热键管理",
                "type": "button",
                "text": "⚡ 打开热键管理",
                "description": "点击下方按钮打开热键管理对话框，添加或编辑热键",
                "callback_key": "open_manager_dialog",
            },
            {
                "key": "notify_on_trigger",
                "label": "热键触发时通知",
                "type": "checkbox",
                "default": True,
                "check_label": "按下热键启动程序时显示通知",
                "description": "启用后，每次按下热键都会在屏幕右上角显示通知（需通知中心启用）",
            },
            {
                "key": "notify_duration",
                "label": "通知显示时长",
                "type": "number",
                "default": 2000,
                "min": 500,
                "max": 10000,
                "description": "热键通知显示的时间长度（毫秒），建议设置为 1500-3000",
            },
        ]

    def open_manager_dialog(self):
        """打开热键管理对话框的回调"""
        try:
            from PyQt5.QtWidgets import QApplication
            if QApplication.instance() is None:
                print(f"[{self.name}] 无法打开对话框：QApplication 未创建")
                return

            from plugins.custom_hotkeys_dialog import CustomHotkeysDialog

            if self._dialog is None or not self._dialog.isVisible():
                self._dialog = CustomHotkeysDialog(self)

            self._dialog.show()
            self._dialog.raise_()
            self._dialog.activateWindow()
        except Exception as e:
            print(f"[{self.name}] 打开对话框失败: {e}")

    def preview(self, query: str) -> str:
        q = query.strip().lower()
        count = len(self._hotkeys)
        if q == "":
            return f"管理自定义热键（当前 {count} 个），输入 'hk list' 打开管理窗口"
        if q in ("list", "列表"):
            return f"打开热键管理窗口（当前 {count} 个热键）"
        if q in ("add", "添加"):
            return "添加新的热键映射"
        return f"搜索热键: {q}"

    # ── 生命周期 ──────────────────────────────────────────────

    def on_load(self) -> None:
        """插件加载：读取配置"""
        self._load_hotkeys_from_file()

    def on_enable(self) -> None:
        """插件启用：注册热键和通知发送者"""
        self._register_all_hotkeys()

        # 向通知中心注册自己作为通知发送者
        print(f"[{self.name}] 尝试向通知中心注册")
        try:
            if hasattr(self, "_plugin_manager"):
                print(f"[{self.name}] _plugin_manager 属性存在")
                print(f"[{self.name}] 所有已加载插件: {list(self._plugin_manager._plugins.keys())}")
                
                notif_plugin = self._plugin_manager.get_plugin("通知中心")
                if notif_plugin:
                    print(f"[{self.name}] 找到通知中心插件")
                    notif_plugin.register_sender(
                        "自定义热键",
                        "热键触发程序启动时发送通知",
                        True
                    )
                    print(f"[{self.name}] 已成功向通知中心注册")
                else:
                    print(f"[{self.name}] 通知中心插件未找到")
            else:
                print(f"[{self.name}] 插件管理器未注入")
        except Exception as e:
            print(f"[{self.name}] 注册通知发送者失败: {e}")
            import traceback
            traceback.print_exc()

    def on_unload(self) -> None:
        self._unregister_all_hotkeys()
        self._save_hotkeys_to_file()

    def on_disable(self) -> None:
        self._unregister_all_hotkeys()

    # ── 热键管理 ──────────────────────────────────────────────

    def add_hotkey(self, hotkey: str, app_path: str, app_name: str = "") -> bool:
        """添加一个热键映射"""
        if not self._keyboard_available:
            raise RuntimeError("keyboard 模块未安装，请先安装 keyboard 包")

        # 检查热键是否已存在
        for hk in self._hotkeys:
            if hk["hotkey"].lower() == hotkey.lower():
                return False

        hotkey_entry = {
            "hotkey": hotkey,
            "path": app_path,
            "name": app_name or os.path.basename(app_path),
            "enabled": True
        }
        self._hotkeys.append(hotkey_entry)
        self._save_hotkeys_to_file()

        # 注册新热键
        self._register_hotkey(hotkey_entry)
        return True

    def remove_hotkey(self, hotkey: str) -> bool:
        """移除一个热键映射"""
        hotkey_lower = hotkey.lower()
        for i, hk in enumerate(self._hotkeys):
            if hk["hotkey"].lower() == hotkey_lower:
                # 先注销
                self._unregister_hotkey(hk)
                # 再移除
                del self._hotkeys[i]
                self._save_hotkeys_to_file()
                return True
        return False

    def update_hotkey(self, old_hotkey: str, new_hotkey: str, app_path: str, app_name: str) -> bool:
        """更新热键映射"""
        old_hotkey_lower = old_hotkey.lower()
        for hk in self._hotkeys:
            if hk["hotkey"].lower() == old_hotkey_lower:
                # 注销旧热键
                self._unregister_hotkey(hk)
                # 更新
                hk["hotkey"] = new_hotkey
                hk["path"] = app_path
                hk["name"] = app_name or os.path.basename(app_path)
                # 注册新热键
                self._register_hotkey(hk)
                self._save_hotkeys_to_file()
                return True
        return False

    def get_hotkeys(self) -> List[Dict[str, Any]]:
        """获取所有热键配置"""
        return self._hotkeys.copy()

    def _register_hotkey(self, hotkey_entry: Dict[str, Any]) -> None:
        """注册单个热键"""
        if not self._keyboard_available or not hotkey_entry.get("enabled", True):
            return

        try:
            hotkey = hotkey_entry["hotkey"]
            app_path = hotkey_entry["path"]
            app_name = hotkey_entry.get("name", os.path.basename(app_path))

            # 创建回调
            def callback(path=app_path, name=app_name, key=hotkey):
                self._launch_app(path, name, key)

            handle = self._keyboard_module.add_hotkey(
                hotkey,
                callback,
                suppress=False,
                trigger_on_release=False
            )
            self._registered_handles.append((hotkey_entry, handle))
            print(f"[CustomHotkeys] 已注册热键: {hotkey} -> {app_path}")
        except Exception as e:
            print(f"[CustomHotkeys] 注册热键失败 {hotkey_entry['hotkey']}: {e}")

    def _unregister_hotkey(self, hotkey_entry: Dict[str, Any]) -> None:
        """注销单个热键"""
        if not self._keyboard_available:
            return

        to_remove = []
        for entry, handle in self._registered_handles:
            if entry == hotkey_entry:
                try:
                    self._keyboard_module.remove_hotkey(handle)
                except Exception as e:
                    print(f"[CustomHotkeys] 注销热键失败: {e}")
                to_remove.append((entry, handle))

        for item in to_remove:
            self._registered_handles.remove(item)

    def _register_all_hotkeys(self) -> None:
        """注册所有热键"""
        if not self._keyboard_available:
            print("[CustomHotkeys] keyboard 模块不可用")
            return

        for hk in self._hotkeys:
            self._register_hotkey(hk)

    def _unregister_all_hotkeys(self) -> None:
        """注销所有热键"""
        if not self._keyboard_available:
            return

        for _, handle in self._registered_handles:
            try:
                self._keyboard_module.remove_hotkey(handle)
            except Exception as e:
                print(f"[CustomHotkeys] 注销热键失败: {e}")

        self._registered_handles.clear()

    def _launch_app(self, app_path: str, app_name: str = "", hotkey: str = "") -> None:
        """启动指定程序"""
        if not app_name:
            app_name = os.path.basename(app_path)
        if app_name.lower().endswith(('.exe', '.lnk', '.bat', '.cmd')):
            app_name = os.path.splitext(app_name)[0]

        try:
            if os.path.isdir(app_path):
                subprocess.Popen(f'explorer "{app_path}"', shell=True)
            else:
                subprocess.Popen([app_path], shell=True)

            # 发送通知（如果配置允许）
            self._send_notification(
                f"⌨️ {app_name}",
                f"正在通过热键 [{hotkey}] 启动..." if hotkey else "正在启动..."
            )
            print(f"[CustomHotkeys] 已启动: {app_path}")
        except Exception as e:
            self._send_notification(f"❌ {app_name}", f"启动失败: {str(e)}", error=True)
            print(f"[CustomHotkeys] 启动失败 {app_path}: {e}")

    def _send_notification(self, title: str, message: str, error: bool = False):
        """通过通知插件发送通知"""
        print(f"[CustomHotkeys] 尝试发送通知: {title} - {message}")
        
        # 检查自身设置是否允许通知
        try:
            settings = self.get_settings()
            notify_enabled = settings.get("notify_on_trigger", True)
            duration = settings.get("notify_duration", 2000)
            print(f"[CustomHotkeys] 设置检查: notify_on_trigger={notify_enabled}, duration={duration}")
            if not notify_enabled:
                print(f"[CustomHotkeys] 通知被设置禁用")
                return
        except Exception as e:
            duration = 2000
            print(f"[CustomHotkeys] 获取设置失败: {e}")
            return

        try:
            # 获取通知插件并发送
            if hasattr(self, "_plugin_manager"):
                print(f"[CustomHotkeys] 插件管理器存在")
                notif_plugin = self._plugin_manager.get_plugin("通知中心")
                if notif_plugin:
                    print(f"[CustomHotkeys] 通知插件存在，发送通知")
                    notif_plugin.send_notification_from("自定义热键", title, message, duration)
                else:
                    print(f"[CustomHotkeys] 通知插件未找到")
            else:
                print(f"[CustomHotkeys] 插件管理器未注入")
        except Exception as e:
            print(f"[CustomHotkeys] 发送通知失败: {e}")

    # ── 持久化 ──────────────────────────────────────────────

    def _get_storage_path(self) -> str:
        data_dir = os.path.join(os.path.dirname(__file__), "..", "..", "data")
        os.makedirs(data_dir, exist_ok=True)
        return os.path.join(data_dir, "custom_hotkeys.json")

    def _save_hotkeys_to_file(self) -> None:
        try:
            path = self._get_storage_path()
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self._hotkeys, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[CustomHotkeys] 保存热键配置失败: {e}")

    def _load_hotkeys_from_file(self) -> None:
        try:
            path = self._get_storage_path()
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    self._hotkeys = json.load(f)
                print(f"[CustomHotkeys] 已加载 {len(self._hotkeys)} 个热键配置")
        except Exception as e:
            print(f"[CustomHotkeys] 加载热键配置失败: {e}")
            self._hotkeys = []

    # ── 搜索 ──────────────────────────────────────────────

    def search(self, query: str) -> List[Dict[str, Any]]:
        q = query.strip().lower()
        if not q or len(q) < 1:
            return []

        results = []
        for hk in self._hotkeys:
            name = hk.get("name", "")
            hotkey = hk.get("hotkey", "")
            if q in name.lower() or q in hotkey.lower():
                results.append({
                    "name": f"⌨️ {name}",
                    "path": f"hk:{hotkey}",
                    "description": f"热键: {hotkey}",
                    "icon": "⌨️",
                    "action": lambda p=hk["path"], n=name, h=hotkey: self._launch_app(p, n, h),
                })
        return results[:10]

    # ── 命令处理 ──────────────────────────────────────────────

    def handle(self, query: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        q = query.strip().lower()

        if q in ("list", "列表", ""):
            self.open_manager_dialog()
            return {
                "type": "display",
                "message": f"⌨️ 已打开热键管理窗口（共 {len(self._hotkeys)} 个热键）",
                "data": None,
                "hide_window": True,
            }

        return self._build_results_list()

    def _build_results_list(self) -> Dict[str, Any]:
        items = []
        for hk in self._hotkeys:
            items.append({
                "name": f"⌨️ {hk['name']}",
                "path": f"hk:{hk['hotkey']}",
                "description": f"热键: {hk['hotkey']}",
                "extension": ".hk",
                "icon_data": None,
                "source": "custom_hotkeys",
                "action": lambda p=hk["path"], n=hk["name"], h=hk["hotkey"]: self._launch_app(p, n, h),
            })

        if not items:
            return {
                "type": "display",
                "message": "⌨️ 暂无自定义热键，使用 'hk list' 打开管理窗口添加",
                "data": None,
            }

        return {
            "type": "results",
            "message": f"⌨️ 自定义热键列表（{len(items)} 个）",
            "data": items,
        }
