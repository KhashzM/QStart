# 通知插件 API 调用说明

## 概述

通知插件为 QStart 提供统一的通知接口，其他插件可通过注册机制使用通知功能，并支持独立开关控制。

---

## 插件信息

| 属性 | 值 |
|------|-----|
| **插件名称** | 通知中心 |
| **插件类名** | `NotificationPlugin` |
| **文件路径** | `src/plugins/notification_plugin.py` |
| **版本** | 2.0.0 |

---

## 接口列表

### 1. register_sender

**功能**：注册为通知发送者

**签名**：
```python
def register_sender(
    sender_name: str,
    description: str = "",
    default_enabled: bool = True
) -> None
```

**参数**：
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `sender_name` | str | 是 | 发送者名称（建议使用插件名） |
| `description` | str | 否 | 描述此发送者的通知用途 |
| `default_enabled` | bool | 否 | 默认是否启用通知（默认 True） |

**调用时机**：建议在插件的 `on_load()` 方法中调用

---

### 2. send_notification_from

**功能**：通过指定发送者发送通知

**签名**：
```python
def send_notification_from(
    sender_name: str,
    title: str,
    message: str,
    duration: int = None
) -> None
```

**参数**：
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `sender_name` | str | 是 | 发送者名称（必须先注册） |
| `title` | str | 是 | 通知标题 |
| `message` | str | 是 | 通知内容 |
| `duration` | int | 否 | 显示时长（毫秒），None 则使用全局设置 |

**说明**：发送前会检查通知中心总开关和该发送者的独立开关

---

### 3. send_notification

**功能**：简化接口，直接发送通知

**签名**：
```python
def send_notification(
    title: str,
    message: str,
    duration: int = None
) -> None
```

**参数**：
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `title` | str | 是 | 通知标题 |
| `message` | str | 是 | 通知内容 |
| `duration` | int | 否 | 显示时长（毫秒） |

**说明**：相当于 `send_notification_from("通知中心", title, message)`

---

### 4. is_sender_enabled

**功能**：检查发送者通知是否启用

**签名**：
```python
def is_sender_enabled(sender_name: str) -> bool
```

**参数**：
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `sender_name` | str | 是 | 发送者名称 |

**返回值**：`bool` - True 表示启用，False 表示禁用

---

## 使用示例

### 完整示例（在插件中使用）

```python
from plugin_base import PluginBase
from typing import Any, Dict, List, Optional

class MyPlugin(PluginBase):
    """示例插件：演示如何使用通知功能"""
    
    @property
    def name(self) -> str:
        return "我的插件"
    
    @property
    def description(self) -> str:
        return "演示通知插件的使用方法"
    
    @property
    def keywords(self) -> list:
        return ["myplugin"]
    
    def on_load(self) -> None:
        """插件加载时注册通知发送者"""
        self._register_notification_sender()
    
    def _register_notification_sender(self) -> None:
        """注册为通知发送者"""
        try:
            if hasattr(self, "_plugin_manager"):
                notif_plugin = self._plugin_manager.get_plugin("通知中心")
                if notif_plugin:
                    notif_plugin.register_sender(
                        "我的插件",
                        "我的插件相关操作的通知",
                        True
                    )
        except Exception as e:
            print(f"[{self.name}] 注册通知发送者失败: {e}")
    
    def perform_action(self, data: str) -> None:
        """执行操作并发送通知"""
        try:
            # 模拟执行操作
            result = self._process_data(data)
            
            # 发送成功通知
            self._send_notification("✅ 操作成功", f"已处理: {result}")
            
        except Exception as e:
            # 发送错误通知
            self._send_notification("❌ 操作失败", str(e))
    
    def _send_notification(self, title: str, message: str) -> None:
        """封装的通知发送方法"""
        try:
            if hasattr(self, "_plugin_manager"):
                notif_plugin = self._plugin_manager.get_plugin("通知中心")
                if notif_plugin:
                    notif_plugin.send_notification_from(
                        "我的插件",
                        title,
                        message
                    )
        except Exception as e:
            print(f"[{self.name}] 发送通知失败: {e}")
```

---

## 通知显示效果

### 视觉样式
- **位置**：屏幕右上角
- **背景**：半透明深色（rgba 45, 45, 45, 0.92）
- **圆角**：12px
- **最大宽度**：320px（自动换行）
- **阴影**：20px 模糊阴影

### 动画效果
- **淡入**：300ms 渐显
- **淡出**：300ms 渐隐

### 默认时长
- 默认显示 3 秒
- 可在通知中心设置中调整（1-10 秒）

---

## 权限控制机制

### 开关层级

```
通知中心设置
├── 总开关（控制所有通知）
│   └── 各插件独立开关
│       ├── 自定义热键
│       ├── 剪贴板历史
│       ├── AI 问答
│       └── 网页搜索
```

### 优先级
1. **总开关**：关闭后所有通知都不会显示
2. **独立开关**：关闭后仅该插件的通知不显示

---

## 最佳实践

### 命名规范
- 使用插件名称作为 `sender_name`，便于用户识别

### 错误处理
- 对通知调用进行 `try-except` 包裹
- 避免通知失败影响主流程

### 通知频率
- 避免频繁发送通知
- 可提供配置项让用户控制通知开关

### 消息格式
- 标题简洁明了，使用 emoji 图标增强可读性
- 消息内容简明扼要，避免过长

---

## 已注册插件

| 插件名称 | 通知场景 | 默认状态 |
|----------|----------|----------|
| 通知中心 | 测试通知、系统状态 | ✅ 启用 |
| 自定义热键 | 热键触发启动程序 | ✅ 启用 |
| 剪贴板历史 | 监听状态变化、清空记录 | ✅ 启用 |
| AI 问答 | API 配置错误、调用失败 | ✅ 启用 |
| 网页搜索 | 打开浏览器搜索 | ❌ 关闭 |

---

## 常见问题

### Q: 注册失败怎么办？
**A**：检查 `_plugin_manager` 是否已注入，确保通知中心插件已加载。

### Q: 通知不显示怎么办？
**A**：检查通知中心设置：
1. 总开关是否启用
2. 该插件的独立开关是否启用
3. 通知显示时长是否设置合理

### Q: 多个插件可以重名吗？
**A**：不建议，`sender_name` 应保持唯一，建议使用插件名称。

---

## 更新日志

| 版本 | 更新内容 |
|------|----------|
| 2.0.0 | 添加插件注册机制和独立开关控制 |
| 1.0.0 | 基础通知功能，透明悬浮窗显示 |