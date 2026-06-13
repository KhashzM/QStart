import importlib
import os
import sys
from typing import Any, Dict, List, Optional

from plugin_base import PluginBase


class PluginManager:
    """插件管理器 - 负责发现、加载、管理和调度插件"""

    def __init__(self, plugins_dir: str = None):
        self._plugins: Dict[str, PluginBase] = {}       # name -> plugin instance
        self._enabled: Dict[str, bool] = {}              # name -> enabled
        self._keyword_map: Dict[str, str] = {}           # keyword -> plugin name
        self._plugins_dir = plugins_dir or os.path.join(os.path.dirname(__file__), "plugins")

    # ── 生命周期 ──────────────────────────────────────────────

    def load_plugins(self) -> List[str]:
        """扫描插件目录并加载所有插件

        Returns:
            已加载的插件名称列表
        """
        if not os.path.isdir(self._plugins_dir):
            os.makedirs(self._plugins_dir, exist_ok=True)
            return []

        # 将插件目录加入搜索路径，以便插件可以互相引用 src 下的模块
        parent_dir = os.path.dirname(self._plugins_dir)
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)

        # 确保通知中心优先加载
        priority_plugins = ["notification"]
        
        # 分离优先级插件和普通插件
        priority_entries = []
        normal_entries = []
        
        for entry in os.listdir(self._plugins_dir):
            entry_path = os.path.join(self._plugins_dir, entry)
            
            module_name = None
            if entry.endswith(".py") and not entry.startswith("_"):
                module_name = entry[:-3]
            elif os.path.isdir(entry_path) and not entry.startswith("_"):
                # 优先检查 plugin.json，其次检查 __init__.py
                plugin_json = os.path.join(entry_path, "plugin.json")
                init_file = os.path.join(entry_path, "__init__.py")
                if os.path.isfile(plugin_json):
                    module_name = entry
                elif os.path.isfile(init_file):
                    module_name = entry
            
            if module_name is None:
                continue
            
            if module_name in priority_plugins:
                priority_entries.append(entry)
            else:
                normal_entries.append(entry)
        
        # 优先加载优先级插件，然后加载普通插件（按名称排序）
        priority_entries.sort()
        normal_entries.sort()
        all_entries = priority_entries + normal_entries

        loaded = []
        for entry in all_entries:
            entry_path = os.path.join(self._plugins_dir, entry)

            module_name = None
            if entry.endswith(".py") and not entry.startswith("_"):
                module_name = entry[:-3]
            elif os.path.isdir(entry_path) and not entry.startswith("_"):
                # 优先检查 plugin.json，其次检查 __init__.py
                plugin_json = os.path.join(entry_path, "plugin.json")
                init_file = os.path.join(entry_path, "__init__.py")
                if os.path.isfile(plugin_json):
                    module_name = entry
                elif os.path.isfile(init_file):
                    module_name = entry

            if module_name is None:
                continue

            plugin = self._load_module(module_name)
            if plugin is not None:
                loaded.append(plugin.name)

        return loaded

    def _load_module(self, module_name: str) -> Optional[PluginBase]:
        """加载单个插件模块"""
        try:
            full_module = f"plugins.{module_name}"
            # 如果已加载过，先 reload
            if full_module in sys.modules:
                module = importlib.reload(sys.modules[full_module])
            else:
                module = importlib.import_module(full_module)

            # 在模块中寻找 PluginBase 的子类实例
            plugin_instance = None
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (
                    isinstance(attr, type)
                    and issubclass(attr, PluginBase)
                    and attr is not PluginBase
                ):
                    plugin_instance = attr()
                    break

            if plugin_instance is None:
                return None

            self.register(plugin_instance)
            return plugin_instance

        except Exception as e:
            print(f"[PluginManager] 加载插件 {module_name} 失败: {e}")
            return None

    def register(self, plugin: PluginBase) -> None:
        """手动注册一个插件实例"""
        name = plugin.name
        self._plugins[name] = plugin
        self._enabled[name] = True

        # 建立关键词 -> 插件名 的映射
        for kw in plugin.keywords:
            self._keyword_map[kw.lower()] = name
        
        # 将插件管理器引用传递给插件，以便插件之间可以互相调用
        plugin._plugin_manager = self

        try:
            plugin.on_load()
            plugin.on_enable()
        except Exception as e:
            print(f"[PluginManager] 插件 {name} 初始化失败: {e}")

    def unload_all(self) -> None:
        """卸载所有插件"""
        for name, plugin in self._plugins.items():
            try:
                if self._enabled.get(name):
                    plugin.on_disable()
                plugin.on_unload()
            except Exception as e:
                print(f"[PluginManager] 卸载插件 {name} 出错: {e}")

        self._plugins.clear()
        self._enabled.clear()
        self._keyword_map.clear()

    def reload_plugins(self) -> List[str]:
        """重新加载所有插件（卸载后重新扫描）"""
        self.unload_all()
        # 清除已加载的插件模块缓存，以便重新导入
        to_remove = [k for k in sys.modules if k.startswith("plugins.")]
        for k in to_remove:
            del sys.modules[k]
        return self.load_plugins()

    # ── 启用 / 禁用 ──────────────────────────────────────────

    def enable(self, name: str) -> None:
        if name in self._plugins:
            self._enabled[name] = True
            # 恢复该插件的关键词映射
            plugin = self._plugins[name]
            for kw in plugin.keywords:
                self._keyword_map[kw.lower()] = name
            plugin.on_enable()

    def disable(self, name: str) -> None:
        if name in self._plugins:
            self._enabled[name] = False
            self._plugins[name].on_disable()
            # 移除该插件的关键词映射
            to_remove = [kw for kw, pn in self._keyword_map.items() if pn == name]
            for kw in to_remove:
                del self._keyword_map[kw]

    def is_enabled(self, name: str) -> bool:
        return self._enabled.get(name, False)

    # ── 查询 ──────────────────────────────────────────────────

    def get_plugin(self, name: str) -> Optional[PluginBase]:
        return self._plugins.get(name)

    def get_all_plugins(self) -> List[PluginBase]:
        return list(self._plugins.values())

    def get_enabled_plugins(self) -> List[PluginBase]:
        return [p for n, p in self._plugins.items() if self._enabled.get(n)]

    # ── 路由 & 搜索 ──────────────────────────────────────────

    def route(self, query: str) -> Optional[PluginBase]:
        """根据用户输入匹配关键词，返回对应的插件

        Args:
            query: 用户原始输入

        Returns:
            匹配到的插件实例，或 None
        """
        q = query.strip().lower()
        if not q:
            return None

        # 尝试最长匹配：逐词拆分，从长到短匹配关键词
        parts = q.split(None, 1)
        if not parts:
            return None

        keyword = parts[0]
        if keyword in self._keyword_map:
            plugin_name = self._keyword_map[keyword]
            if self._enabled.get(plugin_name):
                return self._plugins[plugin_name]

        return None

    def extract_keyword_and_args(self, query: str):
        """从用户输入中提取关键词和参数

        Returns:
            (keyword, args_str) 元组，如果无匹配则 (None, query)
        """
        q = query.strip()
        parts = q.split(None, 1)
        if not parts:
            return None, ""

        keyword = parts[0].lower()
        if keyword in self._keyword_map:
            plugin_name = self._keyword_map[keyword]
            if self._enabled.get(plugin_name):
                args_str = parts[1] if len(parts) > 1 else ""
                return keyword, args_str

        return None, q

    def search_all(self, query: str) -> List[Dict[str, Any]]:
        """调用所有启用插件的 search 方法，收集搜索结果

        Args:
            query: 用户输入的搜索关键词

        Returns:
            合并后的结果列表
        """
        all_results = []
        for name, plugin in self._plugins.items():
            if not self._enabled.get(name):
                continue
            try:
                results = plugin.search(query)
                for r in results:
                    r.setdefault("source", f"plugin:{name}")
                    r.setdefault("extension", ".plugin")
                all_results.extend(results)
            except Exception as e:
                print(f"[PluginManager] 插件 {name} search 出错: {e}")

        return all_results

    def handle(self, plugin: PluginBase, query: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """调用指定插件的 handle 方法

        Args:
            plugin: 目标插件
            query: 去掉关键词后的参数
            context: 可选上下文

        Returns:
            插件返回的结果 dict
        """
        try:
            return plugin.handle(query, context)
        except Exception as e:
            return {
                "type": "display",
                "message": f"插件 {plugin.name} 执行出错: {e}",
                "data": None,
            }