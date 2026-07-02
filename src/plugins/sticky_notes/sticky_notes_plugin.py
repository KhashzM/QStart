import json
import os
import time
from typing import Any, Dict, List, Optional

from plugin_base import PluginBase


class StickyNotesPlugin(PluginBase):
    def __init__(self):
        super().__init__()
        self._notes: List[Dict[str, Any]] = []
        self._todos: List[Dict[str, Any]] = []
        self._open_notes: Dict[str, Any] = {}
        self._todo_dialog = None
        self._note_offset = 0

    @property
    def name(self) -> str:
        return "便签待办"

    @property
    def description(self) -> str:
        return "桌面便签和待办事项管理插件，支持便签编辑、透明度设置和待办列表管理"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def author(self) -> str:
        return "QStart"

    @property
    def keywords(self) -> List[str]:
        return ["note", "便签", "todo", "待办"]

    @property
    def trigger_mode(self) -> str:
        return "action"

    def get_settings_schema(self) -> list:
        return [
            {
                "key": "_section_appearance",
                "label": "外观设置",
                "type": "_section_header",
                "description": "调整便签的颜色、透明度和按钮位置",
            },
            {
                "key": "note_color",
                "label": "便签颜色",
                "type": "select",
                "options": [
                    {"value": "#FFEB3B", "label": "黄色"},
                    {"value": "#FF9800", "label": "橙色"},
                    {"value": "#F44336", "label": "红色"},
                    {"value": "#E91E63", "label": "粉色"},
                    {"value": "#9C27B0", "label": "紫色"},
                    {"value": "#673AB7", "label": "深紫"},
                    {"value": "#3F51B5", "label": "靛蓝"},
                    {"value": "#2196F3", "label": "蓝色"},
                    {"value": "#03A9F4", "label": "天蓝"},
                    {"value": "#00BCD4", "label": "青色"},
                    {"value": "#009688", "label": "翠绿"},
                    {"value": "#4CAF50", "label": "绿色"},
                    {"value": "#9E9E9E", "label": "灰色"},
                    {"value": "#FFFFFF", "label": "白色"},
                    {"value": "#333333", "label": "黑色"},
                ],
                "default": "#FFEB3B",
                "description": "选择便签的背景颜色",
            },
            {
                "key": "note_opacity",
                "label": "透明度",
                "type": "slider",
                "min": 50,
                "max": 255,
                "default": 180,
                "tick_interval": 30,
                "description": "便签的透明程度（50-255，值越大越不透明）",
            },
            {
                "key": "button_position",
                "label": "按钮位置",
                "type": "select",
                "options": [
                    {"value": "top", "label": "顶部"},
                    {"value": "bottom", "label": "底部"},
                    {"value": "left", "label": "左侧"},
                    {"value": "right", "label": "右侧"},
                ],
                "default": "top",
                "description": "选择便签按钮的位置",
            },
        ]

    def on_settings_changed(self):
        settings = self.get_settings()
        color = settings.get("note_color", "#FFEB3B")
        opacity_val = settings.get("note_opacity", 180)
        opacity = int(opacity_val) if opacity_val else 180
        button_position = settings.get("button_position", "top")
        print(f"[{self.name}] 设置已变更 - 颜色: {color}, 透明度: {opacity}, 按钮位置: {button_position}")
        self.update_note_color(color)
        self.update_note_opacity(opacity)
        self.update_button_position(button_position)

    def preview(self, query: str) -> str:
        q = query.strip().lower()
        note_count = len(self._notes)
        todo_count = len(self._todos)
        todo_done = sum(1 for t in self._todos if t.get("done", False))

        if q == "":
            return f"便签({note_count}个) | 待办({todo_count}项, 完成{todo_done}项) | 使用设置调整颜色和透明度"

        parts = q.split(None, 1)
        if len(parts) > 0:
            sub_cmd = parts[0]
            args = parts[1] if len(parts) > 1 else ""

            if sub_cmd in ("add", "new", "创建"):
                if args:
                    return f"创建新便签: {args[:30]}..."
                return "创建新便签"
            if sub_cmd in ("list", "show", "显示"):
                return f"显示所有便签（共 {note_count} 个）"
            if sub_cmd in ("clear", "清空"):
                return f"清空所有便签（共 {note_count} 个）"
            if sub_cmd in ("todo", "待办"):
                if args.startswith("add"):
                    todo_text = args[3:].strip()
                    return f"添加待办: {todo_text}" if todo_text else "添加待办事项"
                return f"打开待办管理（共 {todo_count} 项）"

        return f"便签待办命令: {q}"

    def on_load(self) -> None:
        self._load_data()
        if not self._notes:
            self._create_new_note()
        self._restore_notes()

    def on_unload(self) -> None:
        self._save_data()

    def on_enable(self) -> None:
        self._restore_notes()

    def on_disable(self) -> None:
        self._save_data()
        self._close_all_notes()

    def _load_data(self):
        try:
            path = self._get_storage_path()
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._notes = data.get("notes", [])
                    self._todos = data.get("todos", [])
                    for note in self._notes:
                        note.setdefault("color", "#FFEB3B")
                        note.setdefault("opacity", 180)
                        note.setdefault("x", 100 + self._note_offset * 30)
                        note.setdefault("y", 100 + self._note_offset * 30)
                        note.setdefault("width", 300)
                        note.setdefault("height", 250)
                        note.setdefault("is_folded", False)
                    print(f"[{self.name}] 已加载 {len(self._notes)} 个便签, {len(self._todos)} 个待办")
            else:
                print(f"[{self.name}] 数据文件不存在，将创建新便签")
                self._notes = []
                self._todos = []
        except Exception as e:
            print(f"[{self.name}] 加载数据失败: {e}")
            self._notes = []
            self._todos = []

    def _save_data(self):
        try:
            path = self._get_storage_path()
            data = {
                "notes": self._notes,
                "todos": self._todos,
            }
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"[{self.name}] 已保存 {len(self._notes)} 个便签, {len(self._todos)} 个待办")
        except Exception as e:
            print(f"[{self.name}] 保存数据失败: {e}")

    def _get_storage_path(self) -> str:
        data_dir = os.path.join(os.path.dirname(__file__), "..", "..", "data")
        os.makedirs(data_dir, exist_ok=True)
        return os.path.join(data_dir, "sticky_notes.json")

    def _restore_notes(self):
        for note in self._notes:
            self._create_note_widget(note)

    def _create_note_widget(self, note_data):
        try:
            from plugins.sticky_notes.sticky_note_widget import StickyNoteWidget
            from PyQt5.QtCore import QPoint

            note_id = note_data.get("id", "")
            if note_id in self._open_notes:
                return

            position = QPoint(note_data.get("x", 100), note_data.get("y", 100))
            size = (note_data.get("width", 300), note_data.get("height", 250))

            widget = StickyNoteWidget(
                note_id=note_id,
                content=note_data.get("content", ""),
                color=note_data.get("color", "#FFEB3B"),
                opacity=note_data.get("opacity", 180),
                position=position,
                size=size,
            )

            if note_data.get("is_folded", False):
                widget._is_folded = True
                widget.fold_btn.setText("+")
                widget.text_edit.hide()
                widget.setFixedHeight(38)

            widget.set_save_callback(self._on_note_save)
            widget.set_todo_callback(self._open_todo_dialog)

            self._open_notes[note_id] = widget

        except Exception as e:
            print(f"[{self.name}] 创建便签窗口失败: {e}")

    def _on_note_save(self, note_id, data, delete=False):
        if delete:
            self._notes = [n for n in self._notes if n["id"] != note_id]
            if note_id in self._open_notes:
                del self._open_notes[note_id]
        elif data:
            for note in self._notes:
                if note["id"] == note_id:
                    note.update(data)
                    break
        self._save_data()

    def _close_all_notes(self):
        for note_id, widget in self._open_notes.items():
            try:
                widget.close()
            except Exception:
                pass
        self._open_notes.clear()

    def _create_new_note(self, content=""):
        from PyQt5.QtCore import QPoint

        note_id = str(int(time.time() * 1000))
        offset = len(self._notes) * 30

        new_note = {
            "id": note_id,
            "content": content,
            "color": "#FFEB3B",
            "opacity": 180,
            "x": 100 + offset,
            "y": 100 + offset,
            "width": 300,
            "height": 250,
            "is_folded": False,
        }

        self._notes.append(new_note)
        self._create_note_widget(new_note)
        self._save_data()

        return note_id

    def _open_todo_dialog(self):
        try:
            from PyQt5.QtWidgets import QApplication
            if QApplication.instance() is None:
                print(f"[{self.name}] 无法打开对话框：QApplication 未创建")
                return

            from plugins.sticky_notes.todo_dialog import TodoDialog

            if self._todo_dialog is None or not self._todo_dialog.isVisible():
                self._todo_dialog = TodoDialog(self._todos)
                self._todo_dialog.set_save_callback(self._on_todo_save)

            self._todo_dialog.show()
            self._todo_dialog.raise_()
            self._todo_dialog.activateWindow()
            self._todo_dialog.input_field.setFocus()

        except Exception as e:
            print(f"[{self.name}] 打开待办对话框失败: {e}")

    def _on_todo_save(self, todos):
        self._todos = todos
        self._save_data()

    def update_note_color(self, color):
        for note in self._notes:
            note["color"] = color
        print(f"[{self.name}] update_note_color - 便签数据: {len(self._notes)} 个, 打开的窗口: {len(self._open_notes)} 个")
        for note_id, widget in self._open_notes.items():
            print(f"[{self.name}]   正在更新便签 {note_id} 的颜色")
            widget.set_color(color)
        self._save_data()

    def update_note_opacity(self, opacity):
        for note in self._notes:
            note["opacity"] = opacity
        print(f"[{self.name}] update_note_opacity - 便签数据: {len(self._notes)} 个, 打开的窗口: {len(self._open_notes)} 个")
        for note_id, widget in self._open_notes.items():
            print(f"[{self.name}]   正在更新便签 {note_id} 的透明度")
            widget.set_opacity(opacity)
        self._save_data()

    def update_button_position(self, position):
        print(f"[{self.name}] update_button_position - 位置: {position}, 打开的窗口: {len(self._open_notes)} 个")
        for note_id, widget in self._open_notes.items():
            print(f"[{self.name}]   正在更新便签 {note_id} 的按钮位置")
            widget.set_button_position(position)

    def get_current_color(self):
        if self._notes:
            return self._notes[0].get("color", "#FFEB3B")
        return "#FFEB3B"

    def get_current_opacity(self):
        if self._notes:
            return self._notes[0].get("opacity", 180)
        return 180

    def search(self, query: str) -> List[Dict[str, Any]]:
        q = query.strip().lower()
        if not q or len(q) < 2:
            return []

        results = []

        for note in self._notes:
            content = note.get("content", "")
            if q in content.lower():
                preview = content.replace("\n", " ").strip()[:50]
                if len(content) > 50:
                    preview += "..."
                results.append({
                    "name": f"📝 {preview}",
                    "path": f"note:{note.get('id', '')}",
                    "description": f"便签",
                    "icon": "📝",
                    "action": lambda n=note: self._create_note_widget(n),
                })

        for todo in self._todos:
            text = todo.get("text", "")
            if q in text.lower():
                status = "✓" if todo.get("done", False) else "○"
                results.append({
                    "name": f"{'✓' if todo.get('done') else '○'} {text}",
                    "path": f"todo:{todo.get('id', '')}",
                    "description": f"待办{'(已完成)' if todo.get('done') else ''}",
                    "icon": "📋",
                    "action": lambda: self._open_todo_dialog(),
                })

        return results[:8]

    def handle(self, query: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        q = query.strip().lower()

        if q == "":
            return self._build_summary()

        parts = q.split(None, 2)
        if len(parts) == 0:
            return self._build_summary()

        sub_cmd = parts[0]
        args = parts[1] if len(parts) > 1 else ""

        if sub_cmd in ("add", "new", "创建"):
            content = args.strip()
            self._create_new_note(content)
            return {
                "type": "display",
                "message": f"📝 已创建新便签{'：' + content[:30] if content else ''}",
                "data": None,
                "hide_window": True,
            }

        if sub_cmd in ("list", "show", "显示"):
            self._restore_notes()
            return {
                "type": "display",
                "message": f"📝 已显示所有便签（共 {len(self._notes)} 个）",
                "data": None,
                "hide_window": True,
            }

        if sub_cmd in ("clear", "清空"):
            count = len(self._notes)
            self._close_all_notes()
            self._notes = []
            self._save_data()
            return {
                "type": "display",
                "message": f"📝 已清空 {count} 个便签",
                "data": None,
            }

        if sub_cmd in ("todo", "待办"):
            todo_args = args.strip()
            if todo_args.startswith("add") or todo_args.startswith("创建"):
                todo_text = todo_args[3:].strip() if todo_args.startswith("add") else todo_args[2:].strip()
                if todo_text:
                    new_todo = {
                        "id": str(int(time.time() * 1000)),
                        "text": todo_text,
                        "done": False,
                    }
                    self._todos.append(new_todo)
                    self._save_data()
                    return {
                        "type": "display",
                        "message": f"✅ 已添加待办: {todo_text}",
                        "data": None,
                    }
                else:
                    return {
                        "type": "display",
                        "message": "⚠️ 请输入待办内容，如: todo add 买牛奶",
                        "data": None,
                    }
            else:
                self._open_todo_dialog()
                todo_done = sum(1 for t in self._todos if t.get("done", False))
                return {
                    "type": "display",
                    "message": f"📋 已打开待办管理（共 {len(self._todos)} 项，完成 {todo_done} 项）",
                    "data": None,
                    "hide_window": True,
                }

        return {
            "type": "display",
            "message": f"📝 未知命令: {q}，可用命令: add/list/clear/todo",
            "data": None,
        }

    def _build_summary(self) -> Dict[str, Any]:
        note_count = len(self._notes)
        todo_count = len(self._todos)
        todo_done = sum(1 for t in self._todos if t.get("done", False))

        items = []

        if self._notes:
            for note in self._notes[:5]:
                content = note.get("content", "").replace("\n", " ").strip()[:30]
                if not content:
                    content = "(空便签)"
                items.append({
                    "name": f"📝 {content}",
                    "path": f"note:{note.get('id', '')}",
                    "description": "便签",
                    "icon": "📝",
                    "action": lambda n=note: self._create_note_widget(n),
                })

        if self._todos:
            for todo in self._todos[:5]:
                status = "✓" if todo.get("done", False) else "○"
                items.append({
                    "name": f"{status} {todo.get('text', '')}",
                    "path": f"todo:{todo.get('id', '')}",
                    "description": "待办",
                    "icon": "📋",
                    "action": lambda: self._open_todo_dialog(),
                })

        if items:
            return {
                "type": "results",
                "message": f"📝 便签({note_count}个) | 📋 待办({todo_count}项, 完成{todo_done}项)（点击查看/编辑）",
                "data": items,
            }
        else:
            return {
                "type": "display",
                "message": f"📝 便签({note_count}个) | 📋 待办({todo_count}项) | 使用设置调整颜色和透明度",
                "data": None,
            }