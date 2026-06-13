# QStart 插件开发指南

> 本文档面向希望为 QStart 开发自定义插件的开发者。

---

## 目录

- [快速开始](#快速开始)
- [插件目录结构](#插件目录结构)
- [插件配置文件](#插件配置文件)
- [插件基类 PluginBase](#插件基类-pluginbase)
- [必填属性](#必填属性)
- [可选属性](#可选属性)
- [触发模式 trigger_mode](#触发模式-trigger_mode)
- [生命周期钩子](#生命周期钩子)
- [核心方法](#核心方法)
- [配置系统](#配置系统)
- [完整示例](#完整示例)
- [插件返回值格式](#插件返回值格式)
- [搜索结果数据格式](#搜索结果数据格式)
- [调试技巧](#调试技巧)
- [常见问题](#常见问题)

---

## 快速开始

### 1. 创建插件目录

在 `src/plugins/` 目录下创建一个以插件名称命名的文件夹，例如 `my_plugin/`。

### 2. 创建插件文件

在插件目录中创建以下文件：

```
src/plugins/my_plugin/
├── __init__.py           # 必须存在，导出插件类
├── my_plugin.py          # 插件主文件
├── plugin.json           # 插件配置文件（必须）
└── dialog.py             # 可选：对话框等附加模块
```

### 3. 最小模板

**my_plugin.py**:
```python
from plugin_base import PluginBase

class MyPlugin(PluginBase):
    @property
    def name(self) -> str:
        return "我的插件"

    @property
    def description(self) -> str:
        return "插件功能描述"

    @property
    def keywords(self) -> list:
        return ["my"]  # 用户输入 "my xxx" 时触发

    def handle(self, query: str, context=None) -> dict:
        return {
            "type": "display",
            "message": f"你输入了: {query}",
            "data": None,
        }
```

**__init__.py**:
```python
# 我的插件
from .my_plugin import *

__all__ = ['MyPlugin']
```

**plugin.json**:
```json
{
    "name": "我的插件",
    "version": "1.0.0",
    "description": "插件功能描述",
    "author": "YourName",
    "main_module": "my_plugin.py",
    "files": [
        "my_plugin.py"
    ],
    "keywords": ["my"]
}
```

### 4. 加载插件

- 启动 QStart 后自动加载
- 或在系统托盘右键 → **插件管理** → 点击 **重载全部**

---

## 插件目录结构

```
src/
├── plugins/                      # 插件目录（自动扫描）
│   ├── __init__.py               # 插件包初始化文件
│   │
│   ├── calc/                     # 计算器插件（单文件）
│   │   ├── __init__.py
│   │   ├── calc_plugin.py
│   │   └── plugin.json
│   │
│   ├── clipboard/                # 剪贴板插件（多文件）
│   │   ├── __init__.py
│   │   ├── clipboard_plugin.py   # 主插件文件
│   │   ├── clipboard_dialog.py   # 对话框文件
│   │   └── plugin.json
│   │
│   └── my_plugin/                # 你的插件
│       ├── __init__.py
│       ├── my_plugin.py
│       └── plugin.json
│
├── plugin_base.py                # 插件基类（继承此文件）
└── plugin_manager.py             # 插件管理器（自动发现和加载）
```

**加载规则：**
- 目录名以 `_` 开头的文件夹会被忽略
- 每个插件目录必须包含 `plugin.json` 和 `__init__.py`
- 每个插件中只需定义一个 `PluginBase` 子类，管理器会自动实例化

---

## 插件配置文件

每个插件目录必须包含 `plugin.json` 文件，用于描述插件信息和安装配置：

```json
{
    "name": "剪贴板历史",
    "version": "2.0.0",
    "description": "自动监听系统剪贴板，持久化存储记录，支持搜索和历史管理",
    "author": "QStart",
    "main_module": "clipboard_plugin.py",
    "files": [
        "clipboard_plugin.py",
        "clipboard_dialog.py"
    ],
    "data_files": [
        "clipboard_history.json"
    ],
    "keywords": ["clip", "剪贴板", "history"]
}
```

### 字段说明

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `name` | string | ✅ | 插件显示名称 |
| `version` | string | ✅ | 插件版本号 |
| `description` | string | ✅ | 插件功能描述 |
| `author` | string | ❌ | 插件作者 |
| `main_module` | string | ✅ | 主插件文件名 |
| `files` | array | ✅ | 插件包含的所有 Python 文件 |
| `data_files` | array | ❌ | 插件产生的数据文件（卸载时可删除） |
| `keywords` | array | ❌ | 触发关键词列表 |

---

## 插件基类 PluginBase

所有插件必须继承 `PluginBase`（位于 `src/plugin_base.py`）：

```python
from plugin_base import PluginBase

class MyPlugin(PluginBase):
    ...
```

---

## 必填属性

以下属性使用 `@property` 装饰器，**必须实现**：

### `name` → `str`

插件的唯一显示名称。用于在插件管理界面中标识插件。

```python
@property
def name(self) -> str:
    return "计算器"
```

### `description` → `str`

插件的功能描述，显示在插件管理界面中。

```python
@property
def description(self) -> str:
    return "数学表达式计算，支持基本运算和常用数学函数"
```

### `handle(query, context)` → `dict`

插件的核心处理方法。当用户输入匹配关键词后调用。

```python
def handle(self, query: str, context=None) -> dict:
    # query: 用户输入中去掉关键词后的部分
    # 例如用户输入 "calc 1+1"，则 query = "1+1"
    return {
        "type": "display",
        "message": f"结果: {query}",
        "data": None,
    }
```

---

## 可选属性

### `version` → `str`

插件版本号，默认 `"1.0.0"`。

```python
@property
def version(self) -> str:
    return "2.1.0"
```

### `author` → `str`

插件作者，默认 `""`。

```python
@property
def author(self) -> str:
    return "YourName"
```

### `keywords` → `list[str]`

触发此插件的关键词列表。当用户输入的第一个单词匹配关键词时，查询会被路由到此插件。

```python
@property
def keywords(self) -> list:
    return ["calc", "计算"]
```

- 用户输入 `calc 1+1` → 触发，`query = "1+1"`
- 用户输入 `计算 2*3` → 触发，`query = "2*3"`
- 空列表 `[]` → 不通过关键词触发，只参与全局搜索（通过 `search()` 方法）

---

## 触发模式 trigger_mode

```python
@property
def trigger_mode(self) -> str:
    return "live"  # 或 "action"
```

| 模式 | 值 | 输入时行为 | 按回车时行为 | 适用场景 |
|---|---|---|---|---|
| **实时模式** | `"live"` | 立即调用 `handle()` 并显示结果 | 执行默认选中项 | 无副作用的计算/展示类 |
| **动作模式** | `"action"` | 调用 `preview()` 显示提示文本 | 调用 `handle()` 执行操作 | 有副作用的操作类 |

### 实时模式示例（计算器）

```python
@property
def trigger_mode(self):
    return "live"  # 默认值，可省略

def handle(self, query, context=None):
    result = eval(query)
    return {"type": "display", "message": f"{query} = {result}", "data": result}
```

用户输入 `calc 1+1` 时，每输入一个字符都会实时更新结果。

### 动作模式示例（网页搜索）

```python
@property
def trigger_mode(self):
    return "action"

def preview(self, query: str) -> str:
    # 输入时显示的提示文本
    return f'搜索 "{query}"'

def handle(self, query, context=None):
    # 按回车后才执行
    subprocess.Popen(["start", f"https://google.com/search?q={query}"], shell=True)
    return {"type": "display", "message": "已打开搜索", "data": query, "hide_window": True}
```

用户输入 `search Python教程` 时，只显示提示「搜索 "Python教程"」，按回车才打开浏览器。

---

## 生命周期钩子

插件在不同阶段会收到回调，可重写这些方法来初始化或释放资源：

| 方法 | 调用时机 | 用途 |
|---|---|---|
| `on_load()` | 插件被加载时 | 初始化资源、启动后台任务 |
| `on_unload()` | 插件被卸载时 | 释放资源、停止后台任务 |
| `on_enable()` | 插件被启用时 | 恢复功能 |
| `on_disable()` | 插件被禁用时 | 暂停功能 |
| `on_settings_changed()` | 配置被修改后 | 响应配置变更 |

```python
class MyPlugin(PluginBase):
    def on_load(self):
        print(f"[{self.name}] 已加载")
        self._timer = QTimer()
        self._timer.start(5000)

    def on_unload(self):
        if self._timer:
            self._timer.stop()

    def on_disable(self):
        if self._timer:
            self._timer.stop()

    def on_enable(self):
        if self._timer:
            self._timer.start(5000)
```

---

## 核心方法

### `handle(query, context)` → `dict` （必须实现）

处理匹配到关键词后的查询。

**参数：**
- `query` (`str`): 去掉关键词后的用户输入（已去除前导空格）
- `context` (`dict`, 可选): 上下文信息，包含：
  - `keyword`: 触发的关键词（如 `"calc"`）

**返回值** 见 [插件返回值格式](#插件返回值格式)。

### `preview(query)` → `str` （可选）

仅在 `trigger_mode == "action"` 时被调用。返回输入时的预览提示文本。

```python
def preview(self, query: str) -> str:
    if not query:
        return "请输入问题"
    return f"将要搜索: {query}"
```

### `search(query)` → `list[dict]` （可选）

参与全局搜索。当用户输入不匹配任何插件关键词时，会调用所有启用插件的 `search()` 方法。

```python
def search(self, query: str) -> list:
    results = []
    if query.lower() in self._data:
        results.append({
            "name": f"📊 {query} 的数据",
            "path": f"mydata:{query}",
            "description": "点击查看详细数据",
            "icon": "📊",
            "action": lambda q=query: self._show_data(q),
        })
    return results
```

---

## 配置系统

插件可以通过声明式的 schema 自动生成设置界面。

### 定义配置项

重写 `get_settings_schema()` 方法，返回配置项列表：

```python
def get_settings_schema(self) -> list:
    return [
        {
            "key": "api_key",           # 配置键名（必填）
            "label": "API Key",          # 显示标签（必填）
            "type": "text",              # 控件类型（必填）
            "default": "",               # 默认值（必填）
            "description": "你的 API 密钥",  # 描述文字（可选）
        },
        {
            "key": "max_results",
            "label": "最大结果数",
            "type": "number",
            "default": 10,
            "min": 1,                    # number 类型最小值
            "max": 100,                  # number 类型最大值
        },
        {
            "key": "default_engine",
            "label": "默认搜索引擎",
            "type": "select",
            "default": "google",
            "options": [                 # select 类型的选项
                {"label": "Google", "value": "google"},
                {"label": "百度", "value": "baidu"},
                {"label": "Bing", "value": "bing"},
            ],
        },
        {
            "key": "auto_save",
            "label": "自动保存",
            "type": "checkbox",
            "default": True,
            "check_label": "启用自动保存功能",  # 复选框旁的文字
        },
    ]
```

### 控件类型

| type | 控件 | 适用数据 | 额外字段 |
|---|---|---|---|
| `"text"` | 文本输入框 | `str` | — |
| `"number"` | 数字输入框 | `int` | `min`, `max` |
| `"select"` | 下拉选择框 | `str` | `options` |
| `"checkbox"` | 复选框 | `bool` | `check_label` |

### 读取配置

```python
def handle(self, query, context=None):
    settings = self.get_settings()   # 返回 dict
    api_key = settings.get("api_key", "")
    max_results = settings.get("max_results", 10)
    ...
```

### 保存配置

配置通过 **插件管理 → 设置** 界面自动保存。如需程序化保存：

```python
self.save_settings({"api_key": "sk-xxx", "max_results": 20})
```

### 响应配置变更

```python
def on_settings_changed(self):
    # 配置被修改后调用
    settings = self.get_settings()
    self._api_key = settings.get("api_key")
    self._reset_cache()
```

配置基于 `QSettings` 持久化，存储在注册表/配置文件中，键名为 `Plugin_{插件名称}`。

---

## 完整示例

### 示例 1：天气查询插件（动作模式）

**目录结构：**
```
src/plugins/weather/
├── __init__.py
├── weather_plugin.py
└── plugin.json
```

**weather_plugin.py**:
```python
"""天气查询插件 - 查询城市天气"""

import subprocess
import urllib.parse
from plugin_base import PluginBase


class WeatherPlugin(PluginBase):

    @property
    def name(self) -> str:
        return "天气查询"

    @property
    def description(self) -> str:
        return "查询指定城市的天气信息"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def keywords(self) -> list:
        return ["weather", "天气"]

    @property
    def trigger_mode(self) -> str:
        return "action"

    def get_settings_schema(self) -> list:
        return [
            {
                "key": "provider",
                "label": "天气数据源",
                "type": "select",
                "default": "wttr",
                "options": [
                    {"label": "wttr.in", "value": "wttr"},
                    {"label": "中国天气网", "value": "weathercn"},
                ],
            },
        ]

    def preview(self, query: str) -> str:
        if not query:
            return "请输入城市名称"
        return f"查询 {query} 的天气"

    def handle(self, query: str, context=None) -> dict:
        query = query.strip()
        if not query:
            return {
                "type": "display",
                "message": "请输入城市名称，例如: weather 北京",
                "data": None,
            }

        settings = self.get_settings()
        provider = settings.get("provider", "wttr")

        if provider == "wttr":
            url = f"https://wttr.in/{urllib.parse.quote(query)}"
        else:
            url = f"https://weather.com/zh_CN/weather/today/l/{urllib.parse.quote(query)}"

        subprocess.Popen(["start", url], shell=True)

        return {
            "type": "display",
            "message": f"🌤️ 已打开 {query} 的天气页面",
            "data": query,
            "hide_window": True,
        }
```

**__init__.py**:
```python
# 天气查询插件
from .weather_plugin import *

__all__ = ['WeatherPlugin']
```

**plugin.json**:
```json
{
    "name": "天气查询",
    "version": "1.0.0",
    "description": "查询指定城市的天气信息",
    "author": "YourName",
    "main_module": "weather_plugin.py",
    "files": [
        "weather_plugin.py"
    ],
    "keywords": ["weather", "天气"]
}
```

### 示例 2：带对话框的插件

**目录结构：**
```
src/plugins/clipboard/
├── __init__.py
├── clipboard_plugin.py
├── clipboard_dialog.py
└── plugin.json
```

**clipboard_plugin.py**（部分）:
```python
from plugin_base import PluginBase
from plugins.clipboard_dialog import ClipboardDialog

class ClipboardPlugin(PluginBase):
    @property
    def name(self) -> str:
        return "剪贴板历史"

    def handle(self, query: str, context=None) -> dict:
        if query == "list":
            self._open_dialog()
            return {"type": "display", "message": "已打开剪贴板历史", "data": None}
        ...

    def _open_dialog(self):
        self.dialog = ClipboardDialog()
        self.dialog.exec_()
```

**plugin.json**:
```json
{
    "name": "剪贴板历史",
    "version": "2.0.0",
    "description": "自动监听系统剪贴板，持久化存储记录",
    "author": "QStart",
    "main_module": "clipboard_plugin.py",
    "files": [
        "clipboard_plugin.py",
        "clipboard_dialog.py"
    ],
    "data_files": [
        "clipboard_history.json"
    ],
    "keywords": ["clip", "剪贴板"]
}
```

---

## 插件返回值格式

`handle()` 方法必须返回一个 `dict`，包含以下字段：

```python
{
    "type": str,          # 结果类型（必填）
    "message": str,       # 显示消息（必填）
    "data": any,          # 附带数据（可选）
    "hide_window": bool,  # 执行后是否隐藏窗口（可选，默认 False）
}
```

### type 类型说明

| type | 说明 | UI 行为 |
|---|---|---|
| `"display"` | 显示文本消息 | 在状态栏显示 message 文本 |
| `"launch"` | 启动程序/打开链接 | （预留） |
| `"results"` | 返回一组可选结果 | 在列表中展示 data 中的条目 |
| `"none"` | 无结果 | 不显示任何内容 |

### type="display" 示例

```python
return {
    "type": "display",
    "message": "🧮 1+1 = 2",
    "data": 2,
}
```

### type="results" 示例

```python
return {
    "type": "results",
    "message": "找到 3 条结果",
    "data": [
        {"name": "结果1", "icon": "📄", "path": "..."},
        {"name": "结果2", "icon": "📄", "path": "..."},
    ],
}
```

### hide_window 示例

```python
return {
    "type": "display",
    "message": "已打开浏览器",
    "data": None,
    "hide_window": True,  # 执行后自动隐藏搜索窗口
}
```

---

## 搜索结果数据格式

`search()` 方法和 `type="results"` 返回的每个结果项应包含：

```python
{
    "name": str,              # 显示名称（必填）
    "path": str,              # 路径/标识（必填）
    "description": str,       # 描述（可选）
    "icon": str,              # emoji 图标（可选，默认 "📄"）
    "extension": str,         # 文件扩展名（可选，默认 ".plugin"）
    "icon_data": str,         # base64 图标数据（可选）
    "source": str,            # 来源标识（可选，自动设置）
    "action": callable,       # 点击回调函数（可选）
}
```

---

## 调试技巧

### 1. 命令行查看加载日志

```bash
cd src
python main.py
```

启动时会打印加载的插件列表和可能的错误信息。

### 2. 在插件中使用 print

```python
def handle(self, query, context=None):
    print(f"[{self.name}] 收到查询: {query}")
    ...
```

输出会显示在终端中。

### 3. 不重启重载插件

修改插件代码后，在系统托盘右键 → **重载插件**，无需重启程序。

### 4. 独立测试插件逻辑

```python
# test_my_plugin.py
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from plugins.my_plugin import MyPlugin

p = MyPlugin()
result = p.handle("test input")
print(result)
assert result["type"] == "display"
```

---

## 常见问题

### Q: 插件没有被加载？

1. 确认目录在 `src/plugins/` 下
2. 确认目录名不以 `_` 开头
3. 确认目录包含 `plugin.json` 和 `__init__.py`
4. 确认类继承了 `PluginBase`
5. 确认 `name` 和 `description` 属性已实现
6. 查看终端输出是否有错误信息

### Q: 如何创建纯搜索插件（不通过关键词触发）？

将 `keywords` 返回空列表 `[]`，只实现 `search()` 方法。`handle()` 仍需实现但不会被调用。

### Q: 如何让插件在后台持续运行？

在 `on_load()` 中启动定时器或后台线程，在 `on_unload()` 中停止：

```python
from PyQt5.QtCore import QTimer

def on_load(self):
    self._timer = QTimer()
    self._timer.timeout.connect(self._poll)
    self._timer.start(5000)  # 每5秒执行一次

def _poll(self):
    # 后台任务
    pass

def on_unload(self):
    self._timer.stop()
```

### Q: 插件可以使用 PyQt5 控件吗？

可以。在 `handle()` 中创建对话框是完全支持的。确保对话框对象被引用，避免被垃圾回收。

### Q: 如何处理异步操作？

使用 `threading.Thread` 在后台线程执行，通过 `pyqtSignal` 将结果传回主线程更新 UI。

### Q: 两个插件的关键词冲突怎么办？

后加载的插件会覆盖先前插件的关键词映射。建议确保关键词唯一，或在 `keywords` 中使用更具辨识度的词。

### Q: 如何分发插件？

将整个插件目录打包，用户在插件管理页面选择 `plugin.json` 文件即可安装。

---

## 文件清单

| 文件 | 说明 |
|---|---|
| `src/plugin_base.py` | 插件基类，所有插件继承此类 |
| `src/plugin_manager.py` | 插件管理器，负责加载、路由、调度 |
| `src/plugin_manager_dialog.py` | 插件管理对话框 UI |
| `src/plugin_settings_dialog.py` | 插件设置对话框（自动生成表单） |
| `src/plugins/` | 插件安装目录 |
| `docs/PLUGIN_DEVELOPMENT.md` | 本文档 |
