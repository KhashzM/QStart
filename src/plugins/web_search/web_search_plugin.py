"""网页搜索插件 - 使用系统默认浏览器进行网页搜索"""

from typing import Any, Dict, List, Optional

from plugin_base import PluginBase


class WebSearchPlugin(PluginBase):
    """网页搜索插件：在搜索结果中嵌入网页搜索入口，支持多种搜索引擎

    通过通知中心发送操作状态通知
    """

    @property
    def name(self) -> str:
        return "网页搜索"

    @property
    def description(self) -> str:
        return "在搜索结果中嵌入网页搜索入口，支持百度、必应、谷歌等搜索引擎"

    @property
    def version(self) -> str:
        return "2.0.0"

    @property
    def author(self) -> str:
        return "QStart"

    @property
    def keywords(self) -> List[str]:
        return ["web", "search", "搜索"]

    @property
    def trigger_mode(self) -> str:
        return "action"

    def get_settings_schema(self) -> list:
        return [
            {
                "key": "engine",
                "label": "默认搜索引擎",
                "type": "select",
                "options": [
                    {"value": "baidu", "label": "百度"},
                    {"value": "bing", "label": "必应"},
                    {"value": "google", "label": "谷歌"},
                    {"value": "bing-cn", "label": "必应中国"},
                ],
                "default": "baidu",
                "description": "选择默认使用的搜索引擎",
            },
            {
                "key": "show_in_search",
                "label": "搜索结果中显示",
                "type": "checkbox",
                "default": True,
                "check_label": "在普通搜索结果中自动插入网页搜索入口",
                "description": "关闭后只能通过 web/search 关键词触发",
            },
            {
                "key": "notify_on_search",
                "label": "搜索时通知",
                "type": "checkbox",
                "default": False,
                "check_label": "打开浏览器搜索时显示通知",
                "description": "每次使用网页搜索时通过通知中心提示（建议关闭，避免频繁通知）",
            },
        ]

    def preview(self, query: str) -> str:
        q = query.strip()
        if not q:
            return "输入搜索词进行网页搜索"
        settings = self.get_settings()
        engines = {"baidu": "百度", "bing": "必应", "google": "谷歌", "bing-cn": "必应中国"}
        engine_name = engines.get(settings.get("engine", "baidu"), "百度")
        return f"在 {engine_name} 搜索: \"{q}\""

    # ── 生命周期 ──────────────────────────────────────────────

    def on_load(self) -> None:
        """插件加载时注册通知发送者"""
        try:
            if hasattr(self, "_plugin_manager"):
                notif_plugin = self._plugin_manager.get_plugin("通知中心")
                if notif_plugin:
                    notif_plugin.register_sender(
                        "网页搜索",
                        "网页搜索操作相关的通知",
                        True
                    )
        except Exception as e:
            print(f"[{self.name}] 注册通知发送者失败: {e}")

    # ── 通知发送 ──────────────────────────────────────────────

    def _send_search_notification(self, title: str, message: str):
        """发送搜索通知（受 notify_on_search 开关控制）"""
        try:
            settings = self.get_settings()
            if not settings.get("notify_on_search", False):
                return
        except Exception:
            pass

        try:
            if hasattr(self, "_plugin_manager"):
                notif_plugin = self._plugin_manager.get_plugin("通知中心")
                if notif_plugin:
                    notif_plugin.send_notification_from("网页搜索", title, message)
        except Exception as e:
            print(f"[{self.name}] 发送通知失败: {e}")

    # ── 搜索引擎配置 ──────────────────────────────────────────

    def _get_engine_url(self, engine: str) -> str:
        """获取搜索引擎的搜索 URL"""
        engines = {
            "baidu": "https://www.baidu.com/s?wd={}",
            "bing": "https://www.bing.com/search?q={}",
            "google": "https://www.google.com/search?q={}",
            "bing-cn": "https://cn.bing.com/search?q={}",
        }
        return engines.get(engine, engines["baidu"])

    def _get_engine_name(self, engine: str) -> str:
        """获取搜索引擎显示名称"""
        engines = {
            "baidu": "百度",
            "bing": "必应",
            "google": "谷歌",
            "bing-cn": "必应中国",
        }
        return engines.get(engine, "百度")

    # ── 全局搜索 ──────────────────────────────────────────────

    def search(self, query: str) -> List[Dict[str, Any]]:
        q = query.strip().lower()
        if not q or len(q) < 1:
            return []

        settings = self.get_settings()
        if not settings.get("show_in_search", True):
            return []

        return self.get_web_search_results(query)

    def get_web_search_results(self, query: str) -> List[Dict[str, Any]]:
        """生成网页搜索结果项"""
        settings = self.get_settings()
        engine = settings.get("engine", "baidu")
        engine_name = self._get_engine_name(engine)

        return [{
            "name": f"🔍 {engine_name}: {query}",
            "path": f"web:{query}",
            "description": f"在 {engine_name} 搜索「{query}」",
            "extension": ".web",
            "icon_data": None,
            "source": "web_search",
            "action": lambda q=query: self._open_search(q),
        }]

    # ── 命令处理 ──────────────────────────────────────────────

    def handle(self, query: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        q = query.strip()

        if not q:
            return {
                "type": "display",
                "message": "🔍 请输入搜索词，如: web 天气",
                "data": None,
            }

        self._open_search(q)
        return {
            "type": "display",
            "message": f"🔍 正在浏览器中搜索: {q}",
            "data": q,
            "hide_window": True,
        }

    def _open_search(self, query: str):
        """打开浏览器进行搜索"""
        import webbrowser

        settings = self.get_settings()
        engine = settings.get("engine", "baidu")
        url = self._get_engine_url(engine)

        try:
            encoded_query = query.replace(" ", "+")
            full_url = url.format(encoded_query)
            webbrowser.open(full_url)

            # 发送通知
            engine_name = self._get_engine_name(engine)
            print(f"[WebSearch] 当前搜索引擎设置: {engine} -> {engine_name}")
            self._send_search_notification(f"🔍 {engine_name} 搜索", query)

            print(f"[WebSearch] 已打开搜索: {full_url}")
        except Exception as e:
            print(f"[WebSearch] 打开搜索失败: {e}")
