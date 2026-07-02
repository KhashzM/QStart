# QStart - AI 驱动的效率工具平台

> 一个基于 PyQt5 的 Windows 效率工具平台
> 从「手动选工具」升级为「AI自动完成任务」

---

## ✨ 项目简介

QStart 是一个 Windows 效率工具平台。主要特性：

- 🔍 **统一入口** - 全局热键 `Ctrl+Space` 快速唤起
- ⚙️ **插件系统** - 可扩展的插件架构
- 🔌 **热插拔** - 无需重新打包主程序即可安装插件

---

## 🚀 核心特性

### 快捷启动
- 全局热键 `Ctrl+Space` 唤起搜索窗口
- 搜索本地应用程序
- 固定常用应用到快捷面板
- 支持明/暗主题切换

### 插件系统
- **通知中心** - 系统通知管理
- **AI 问答** - 智能问答和对话
- **计算器** - 数学表达式计算
- **剪贴板历史** - 剪贴板记录管理
- **自定义热键** - 配置快捷键打开程序
- **大小写监测** - Caps Lock 状态提示
- **网页搜索** - 快速搜索引擎
- **便签待办** - 桌面便签和待办事项管理

### 插件架构
- 每个插件独立目录，包含 `plugin.json` 配置文件
- 支持多文件插件（对话框、工具模块等）
- 插件可声明数据文件，卸载时自动清理
- 无需重新打包主程序即可安装新插件

---

## 🏗️ 项目结构

```
QStart_v2.0/
├── src/                        # 源代码
│   ├── main.py                # 应用入口
│   ├── main_window.py         # 主窗口 UI
│   ├── plugin_manager.py      # 插件管理器
│   ├── plugin_base.py         # 插件基类
│   ├── plugins/               # 插件目录
│   │   ├── ai_qa/             # AI 问答插件
│   │   ├── calc/              # 计算器插件
│   │   ├── capslock/          # 大小写监测插件
│   │   ├── clipboard/         # 剪贴板历史插件
│   │   ├── custom_hotkeys/    # 自定义热键插件
│   │   ├── notification/      # 通知中心插件
│   │   ├── sticky_notes/      # 便签待办插件
│   │   └── web_search/        # 网页搜索插件
│   └── ...
├── data/                       # 数据存储
├── docs/                       # 文档
│   ├── PLUGIN_DEVELOPMENT.md  # 插件开发指南
│   └── notification_api.md    # 通知 API 文档
├── requirements.txt            # 依赖列表
└── README.md                   # 本文件
```

---

## 📦 安装与运行

### 环境要求
- Python 3.12+
- Windows 系统

### 下载预编译版本

直接下载打包好的 EXE 程序：

- 📦 [QStart.exe](https://github.com/yourusername/QStart/releases) - 最新稳定版

下载后直接双击运行，无需安装 Python 环境。

### 源码运行

```bash
# 安装依赖
pip install -r requirements.txt

# 运行程序
cd src
python main.py
```

### 打包为 EXE

```bash
cd src
pyinstaller QStart.spec
```

打包后的程序位于 `dist/QStart/` 目录。

---

## 🔌 插件开发

### 快速开始

1. 在 `src/plugins/` 下创建插件目录：
```
src/plugins/my_plugin/
├── __init__.py
├── my_plugin.py
└── plugin.json
```

2. 创建插件类：
```python
# my_plugin.py
from plugin_base import PluginBase

class MyPlugin(PluginBase):
    @property
    def name(self) -> str:
        return "我的插件"

    @property
    def description(self) -> str:
        return "插件描述"

    @property
    def keywords(self) -> list:
        return ["my"]

    def handle(self, query: str, context=None) -> dict:
        return {"type": "display", "message": f"结果: {query}", "data": None}
```

3. 创建配置文件：
```json
{
    "name": "我的插件",
    "version": "1.0.0",
    "description": "插件描述",
    "author": "YourName",
    "main_module": "my_plugin.py",
    "files": ["my_plugin.py"],
    "keywords": ["my"]
}
```

详细文档请参阅 [插件开发指南](docs/PLUGIN_DEVELOPMENT.md)。

---

## 📖 使用说明

### 基本操作

| 操作 | 说明 |
|------|------|
| `Ctrl+Space` | 打开搜索窗口 |
| 输入关键词 | 搜索应用或触发插件 |
| `Enter` | 执行选中项 |
| `Esc` | 隐藏窗口 |

### 插件命令

| 命令 | 插件 | 说明 |
|------|------|------|
| `calc 1+1` | 计算器 | 计算数学表达式 |
| `clip list` | 剪贴板历史 | 打开剪贴板历史窗口 |
| `search 关键词` | 网页搜索 | 打开搜索引擎 |
| `ai 问题` | AI 问答 | AI 智能问答 |
| `note` | 便签待办 | 打开便签或待办管理 |
| `todo add 事项` | 便签待办 | 添加待办事项 |

### 系统托盘

- 右键托盘图标可访问：
  - 插件管理
  - 设置
  - 重载插件
  - 退出程序

---

## 📈 后续规划

- [ ] 插件市场
- [ ] 本地模型支持
- [ ] 多模态输入
- [ ] 工作流可视化
- [ ] 跨平台支持

---

## 📄 License

MIT
