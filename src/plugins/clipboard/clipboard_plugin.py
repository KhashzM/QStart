"""剪贴板历史插件 - 自动监听、持久化存储、可视化管理"""

import json
import os
import time
from typing import Any, Dict, List, Optional

from plugin_base import PluginBase


class ClipboardPlugin(PluginBase):
    """剪贴板历史插件：自动监听系统剪贴板，持久化记录，支持搜索和历史管理"""

    def __init__(self):
        super().__init__()
        self._history: List[Dict[str, Any]] = []
        self._max_history = 200
        self._last_content = ""
        self._timer = None
        self._monitoring = False
        self._dialog = None

    @property
    def name(self) -> str:
        return "剪贴板历史"

    @property
    def description(self) -> str:
        return "自动监听系统剪贴板，持久化存储记录，支持搜索和历史管理"

    @property
    def version(self) -> str:
        return "2.0.0"

    @property
    def author(self) -> str:
        return "QStart"

    @property
    def keywords(self) -> list:
        return ["clip", "剪贴板"]

    @property
    def trigger_mode(self) -> str:
        return "action"

    def get_settings_schema(self) -> list:
        return [
            {
                "key": "max_records",
                "label": "最大记录数",
                "type": "number",
                "default": 200,
                "min": 50,
                "max": 2000,
                "description": "最多保存多少条剪贴板记录",
            },
            {
                "key": "poll_interval",
                "label": "检测间隔（毫秒）",
                "type": "number",
                "default": 1000,
                "min": 500,
                "max": 10000,
                "description": "检查剪贴板变化的时间间隔",
            },
        ]

    def preview(self, query: str) -> str:
        q = query.strip().lower()
        count = len(self._history)
        if q == "":
            return f"显示剪贴板历史（共 {count} 条），输入 'clip list' 打开完整窗口"
        if q in ("list", "列表", "history"):
            return f"打开剪贴板历史窗口（共 {count} 条记录）"
        if q in ("clear", "清空"):
            return f"清空全部 {count} 条历史记录"
        if q in ("stop", "停止"):
            return "停止自动监听剪贴板"
        if q in ("start", "启动"):
            return "启动自动监听剪贴板"
        return f"在历史中搜索: {q}"

    # ── 生命周期 ──────────────────────────────────────────────

    def on_load(self) -> None:
        """插件加载：读取配置、启动监听"""
        self._load_history_from_file()
        self._start_monitoring()

    def on_unload(self) -> None:
        self._stop_monitoring()
        self._save_history_to_file()

    def on_enable(self) -> None:
        self._start_monitoring()

    def on_disable(self) -> None:
        self._stop_monitoring()
        self._save_history_to_file()

    def on_settings_changed(self) -> None:
        settings = self.get_settings()
        self._max_history = settings.get("max_records", 200)
        # 重启监听以应用新的轮询间隔
        if self._monitoring:
            self._stop_monitoring()
            self._start_monitoring()

    # ── 监听 ──────────────────────────────────────────────────

    def _start_monitoring(self):
        if self._monitoring:
            return
        try:
            from PyQt5.QtCore import QTimer
            from PyQt5.QtWidgets import QApplication
            app = QApplication.instance()
            if app is None:
                return

            settings = self.get_settings()
            interval = settings.get("poll_interval", 1000)
            self._max_history = settings.get("max_records", 200)

            self._timer = QTimer()
            self._timer.timeout.connect(self._check_clipboard)
            self._timer.start(interval)
            self._monitoring = True
            self._read_current_clipboard()
            print(f"[{self.name}] 剪贴板监听已启动（间隔 {interval}ms，共 {len(self._history)} 条记录）")
        except Exception as e:
            print(f"[{self.name}] 启动监听失败: {e}")

    def _stop_monitoring(self):
        if self._timer:
            self._timer.stop()
            self._timer = None
        self._monitoring = False
        print(f"[{self.name}] 剪贴板监听已停止")

    def _read_current_clipboard(self):
        try:
            from PyQt5.QtWidgets import QApplication
            clipboard = QApplication.clipboard()
            if clipboard:
                content = clipboard.text()
                if content:
                    self._last_content = content
        except Exception:
            pass

    def _check_clipboard(self):
        try:
            from PyQt5.QtWidgets import QApplication
            clipboard = QApplication.clipboard()
            if not clipboard:
                return
            content = clipboard.text()
            if not content:
                return
            if content != self._last_content:
                self._last_content = content
                self._add_record(content)
        except Exception:
            pass

    # ── 记录管理 ──────────────────────────────────────────────

    def _add_record(self, content: str):
        if not content.strip():
            return
        # 去重：如果和第一条相同则忽略
        if self._history and self._history[0]["content"] == content:
            return

        record = {
            "id": str(int(time.time() * 1000)),
            "content": content,
            "time_str": time.strftime("%Y-%m-%d %H:%M:%S"),
            "timestamp": int(time.time()),
            "length": len(content),
        }
        self._history.insert(0, record)

        if len(self._history) > self._max_history:
            self._history = self._history[:self._max_history]

        if len(self._history) % 10 == 0:
            self._save_history_to_file()

    def get_history(self) -> List[Dict[str, Any]]:
        """获取全部历史记录（供对话框使用）"""
        return self._history

    def clear_history(self):
        """清空全部历史记录"""
        count = len(self._history)
        self._history.clear()
        self._save_history_to_file()
        print(f"[{self.name}] 已清空 {count} 条历史记录")

    # ── 持久化存储 ────────────────────────────────────────────

    def _get_storage_path(self) -> str:
        data_dir = os.path.join(os.path.dirname(__file__), "..", "..", "data")
        os.makedirs(data_dir, exist_ok=True)
        return os.path.join(data_dir, "clipboard_history.json")

    def _save_history_to_file(self):
        try:
            path = self._get_storage_path()
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self._history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[{self.name}] 保存历史失败: {e}")

    def _load_history_from_file(self):
        try:
            path = self._get_storage_path()
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    self._history = json.load(f)
                for record in self._history:
                    record.setdefault("time_str", "")
                    record.setdefault("timestamp", 0)
                    record.setdefault("length", len(record.get("content", "")))
                print(f"[{self.name}] 已加载 {len(self._history)} 条历史记录")
        except Exception as e:
            print(f"[{self.name}] 加载历史失败: {e}")
            self._history = []

    # ── 全局搜索 ──────────────────────────────────────────────

    def search(self, query: str) -> List[Dict[str, Any]]:
        q = query.strip().lower()
        if not q or len(q) < 1:
            return []

        results = []
        for item in self._history:
            content = item.get("content", "")
            if q in content.lower():
                preview = content[:80].replace("\n", " ")
                if len(content) > 80:
                    preview += "..."
                results.append({
                    "name": f"📋 {preview}",
                    "path": f"clip:{item.get('id', '')}",
                    "description": f"剪贴板记录 ({item.get('time_str', '')}, {item.get('length', 0)}字符)",
                    "icon": "📋",
                    "action": lambda c=content: self._copy_to_clipboard(c),
                })
        return results[:5]

    # ── 命令处理 ──────────────────────────────────────────────

    def handle(self, query: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        q = query.strip().lower()

        if q == "":
            return self._build_inline_results()

        if q in ("list", "列表", "history"):
            self._open_dialog()
            return {
                "type": "display",
                "message": f"📋 已打开剪贴板历史（共 {len(self._history)} 条）",
                "data": None,
                "hide_window": True,
            }

        if q in ("clear", "清空"):
            count = len(self._history)
            self.clear_history()
            return {
                "type": "display",
                "message": f"📋 已清空 {count} 条剪贴板记录",
                "data": None,
            }

        if q in ("stop", "停止"):
            self._stop_monitoring()
            return {
                "type": "display",
                "message": "📋 剪贴板监听已停止",
                "data": None,
            }

        if q in ("start", "启动"):
            self._start_monitoring()
            return {
                "type": "display",
                "message": f"📋 剪贴板监听已启动（{'运行中' if self._monitoring else '启动失败'}）",
                "data": None,
            }

        return self._build_inline_results(filter_text=q)

    def _build_inline_results(self, filter_text="") -> Dict[str, Any]:
        """构建主窗口内联显示的结果列表"""
        history = self._history
        if filter_text:
            history = [h for h in history if filter_text in h["content"].lower()]

        items = []
        for record in history[:20]:
            content = record["content"]
            preview = content.replace("\n", " ").strip()
            if len(preview) > 50:
                preview = preview[:50] + "..."

            items.append({
                "name": f"📋 {preview}",
                "path": f"clip:{record.get('id', '')}",
                "description": f"{record.get('time_str', '')} | {record.get('length', 0)}字符",
                "extension": ".clip",
                "icon_data": None,
                "source": "clipboard",
                "action": lambda c=content: self._copy_to_clipboard(c),
            })

        if not items:
            return {
                "type": "display",
                "message": f"📋 {'没有匹配的记录' if filter_text else '剪贴板历史为空'}（共 {len(self._history)} 条）",
                "data": None,
            }

        label = f"搜索 \"{filter_text}\"" if filter_text else "最近记录"
        return {
            "type": "results",
            "message": f"📋 {label} - {len(items)}/{len(self._history)} 条（点击复制，'clip list' 打开完整窗口）",
            "data": items,
        }

    def _open_dialog(self):
        """打开剪贴板历史对话框"""
        try:
            from PyQt5.QtWidgets import QApplication
            if QApplication.instance() is None:
                print(f"[{self.name}] 无法打开对话框：QApplication 未创建")
                return

            from plugins.clipboard.clipboard_dialog import ClipboardDialog

            if self._dialog is None or not self._dialog.isVisible():
                self._dialog = ClipboardDialog(self)

            self._dialog.show()
            self._dialog.raise_()
            self._dialog.activateWindow()
        except Exception as e:
            print(f"[{self.name}] 打开对话框失败: {e}")

    def _copy_to_clipboard(self, text: str):
        try:
            from PyQt5.QtWidgets import QApplication
            clipboard = QApplication.clipboard()
            if clipboard:
                clipboard.setText(text)
        except Exception:
            pass
