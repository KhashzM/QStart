"""AI 问答插件 - 使用 OpenAI 兼容 API 的对话式 AI 助手"""

from typing import Any, Dict, List, Optional

from plugin_base import PluginBase


class AIQAPlugin(PluginBase):
    """AI 问答插件：在搜索结果中嵌入 AI 问答入口，点击后打开聊天对话框"""

    @property
    def name(self) -> str:
        return "AI 问答"

    @property
    def description(self) -> str:
        return "使用 OpenAI 兼容 API 进行 AI 对话问答，支持自定义服务地址、模型和 API Key"

    @property
    def version(self) -> str:
        return "2.1.0"

    @property
    def author(self) -> str:
        return "QStart"

    @property
    def keywords(self) -> List[str]:
        return ["ai", "ask"]

    @property
    def trigger_mode(self) -> str:
        return "action"

    def get_settings_schema(self) -> list:
        return [
            {
                "key": "base_url",
                "label": "API 地址 (Base URL)",
                "type": "text",
                "default": "https://api.deepseek.com",
                "description": "OpenAI 兼容 API 的基础地址，不需要包含 /v1",
            },
            {
                "key": "api_key",
                "label": "API Key",
                "type": "text",
                "default": "",
                "description": "你的 API Key（sk-...）",
            },
            {
                "key": "model",
                "label": "模型名称",
                "type": "text",
                "default": "deepseek-chat",
                "description": "使用的模型标识，如 deepseek-chat、gpt-4o、qwen-turbo 等",
            },
            {
                "key": "system_prompt",
                "label": "系统提示词",
                "type": "text",
                "default": "你是一个有用的AI助手。请简洁明了地回答问题。",
                "description": "AI 的系统角色设定",
            },
            {
                "key": "show_in_search",
                "label": "搜索结果中显示",
                "type": "checkbox",
                "default": True,
                "check_label": "在普通搜索结果中自动插入 AI 问答入口",
                "description": "关闭后只能通过 ai/ask 关键词触发",
            },
            {
                "key": "custom_prefix",
                "label": "搜索词前缀",
                "type": "text",
                "default": "",
                "description": "从搜索结果进入 AI 时，在搜索词前加的提示语（如「请简要介绍」），留空则直接发送",
            },
        ]

    def preview(self, query: str) -> str:
        q = query.strip()
        if not q:
            return "请输入你的问题"
        settings = self.get_settings()
        model = settings.get("model", "AI")
        return f"向 {model} 提问: \"{q}\""

    # ── 命令处理 ──────────────────────────────────────────────

    def handle(self, query: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        q = query.strip()
        settings = self.get_settings()

        # 检查 API Key 是否配置
        if not settings.get("api_key", "").strip():
            msg = "API Key 未配置，请在插件设置中配置你的 API Key"
            return {
                "type": "display",
                "message": f"🤖 {msg}",
                "data": None,
            }

        # 构造初始消息
        if q:
            prefix = settings.get("custom_prefix", "")
            initial_msg = f"{prefix} {q}".strip() if prefix else q
        else:
            initial_msg = None

        try:
            self._open_chat(settings, initial_msg)

            if q:
                return {
                    "type": "display",
                    "message": f"🤖 已打开 AI 对话（问题: {q}）",
                    "data": q,
                    "hide_window": True,
                }
            else:
                return {
                    "type": "display",
                    "message": "🤖 已打开 AI 对话",
                    "data": None,
                    "hide_window": True,
                }
        except Exception as e:
            msg = f"打开对话失败: {str(e)}"
            return {
                "type": "display",
                "message": f"🤖 {msg}",
                "data": None,
            }

    def get_ai_search_results(self, query: str) -> List[Dict[str, Any]]:
        """生成 AI 问答搜索结果项，供搜索结果列表使用"""
        settings = self.get_settings()
        if not settings.get("show_in_search", True):
            return []

        model = settings.get("model", "AI")

        return [{
            "name": f"🤖 AI 问问 {model}: {query}",
            "path": f"ai:{query}",
            "description": f"向 {model} 提问「{query}」",
            "extension": ".ai",
            "icon_data": None,
            "source": "ai_qa",
            "action": lambda q=query: self._open_chat_with_query(q),
        }]

    def _open_chat_with_query(self, query: str):
        """从搜索结果点击时调用"""
        settings = self.get_settings()
        if not settings.get("api_key", "").strip():
            print(f"[{self.name}] API Key 未配置")
            return

        prefix = settings.get("custom_prefix", "")
        initial_msg = f"{prefix} {query}".strip() if prefix else query
        try:
            self._open_chat(settings, initial_msg)
        except Exception as e:
            print(f"[{self.name}] 打开对话失败: {str(e)}")

    def _open_chat(self, settings: dict, initial_msg: str = None):
        """打开聊天对话框"""
        from plugins.ai_chat_dialog import AIChatDialog

        config = {
            "base_url": settings.get("base_url", "https://api.deepseek.com"),
            "api_key": settings.get("api_key", ""),
            "model": settings.get("model", "deepseek-chat"),
            "system_prompt": settings.get("system_prompt", "你是一个有用的AI助手。请简洁明了地回答问题。"),
        }

        dialog = AIChatDialog(config)

        # 如果有初始问题，预填充到输入框
        if initial_msg:
            dialog.input_field.setText(initial_msg)

        dialog.show()
        dialog.raise_()
        dialog.activateWindow()
        dialog.input_field.setFocus()

        # 保存引用防止被垃圾回收
        if not hasattr(self, '_open_dialogs'):
            self._open_dialogs = []
        self._open_dialogs = [d for d in self._open_dialogs if d.isVisible()]
        self._open_dialogs.append(dialog)
