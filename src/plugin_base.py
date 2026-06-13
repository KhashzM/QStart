from abc import ABC, ABCMeta, abstractmethod
from typing import Any, Dict, List, Optional
from PyQt5.QtCore import QSettings, QObject, QMetaObject


class QABCMeta(type(QObject), ABCMeta):
    """组合元类：解决 QObject 和 ABC 的元类冲突"""
    pass


class PluginBase(QObject, ABC, metaclass=QABCMeta):
    """插件基类 - 所有插件必须继承此类"""

    def __init__(self):
        super().__init__()
        self._settings = None
        self._plugin_manager = None

    def set_plugin_manager(self, manager):
        """设置插件管理器引用"""
        self._plugin_manager = manager

    @property
    @abstractmethod
    def name(self) -> str:
        """插件名称"""
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        """插件描述"""
        ...

    @property
    def version(self) -> str:
        """插件版本"""
        return "1.0.0"

    @property
    def author(self) -> str:
        """插件作者"""
        return ""

    @property
    def keywords(self) -> list:
        """关键词列表，用于搜索匹配"""
        return []

    @property
    def trigger_mode(self) -> str:
        """触发模式: 'keyword', 'action', 'global'"""
        return "keyword"

    def get_settings(self) -> dict:
        """获取插件设置"""
        if self._settings is None:
            self._settings = {}
            try:
                qsettings = QSettings("QStart", self.name)
                for key in qsettings.allKeys():
                    value = qsettings.value(key)
                    if value == "true":
                        self._settings[key] = True
                    elif value == "false":
                        self._settings[key] = False
                    else:
                        self._settings[key] = value
            except Exception as e:
                print(f"[{self.name}] 加载设置失败: {e}")
        return self._settings

    def save_settings(self, settings: dict) -> None:
        """保存插件设置"""
        try:
            qsettings = QSettings("QStart", self.name)
            for key, value in settings.items():
                qsettings.setValue(key, value)
            qsettings.sync()
            self._settings = settings
        except Exception as e:
            print(f"[{self.name}] 保存设置失败: {e}")

    def get_settings_schema(self) -> list:
        """获取设置项定义"""
        return []

    def on_load(self) -> None:
        """插件加载时调用"""
        pass

    def on_unload(self) -> None:
        """插件卸载时调用"""
        pass

    def on_enable(self) -> None:
        """插件启用时调用"""
        pass

    def on_disable(self) -> None:
        """插件禁用时调用"""
        pass

    def on_settings_changed(self) -> None:
        """设置更改后调用"""
        pass

    def search(self, query: str) -> List[Dict[str, Any]]:
        """搜索方法"""
        return []

    def preview(self, query: str) -> str:
        """预览内容"""
        return ""

    def handle(self, query: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """处理用户输入"""
        return {"type": "display", "message": "", "data": None}
