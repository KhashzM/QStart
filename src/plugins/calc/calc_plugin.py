"""计算器插件 - 支持数学表达式计算"""

import math
from typing import Any, Dict, List, Optional

from plugin_base import PluginBase


class CalculatorPlugin(PluginBase):
    """计算器插件：输入 calc 表达式 进行数学计算"""

    @property
    def name(self) -> str:
        return "计算器"

    @property
    def description(self) -> str:
        return "数学表达式计算，支持基本运算和常用数学函数"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def author(self) -> str:
        return "QStart"

    @property
    def keywords(self) -> List[str]:
        return ["calc", "计算"]

    def get_settings_schema(self) -> list:
        return [
            {
                "key": "precision",
                "label": "小数精度",
                "type": "number",
                "default": 6,
                "min": 0,
                "max": 15,
                "description": "计算结果保留的小数位数（0 表示不限制）",
            },
            {
                "key": "show_expression",
                "label": "显示表达式",
                "type": "checkbox",
                "default": True,
                "check_label": "在结果中显示原始表达式",
                "description": "关闭后只显示结果数值",
            },
        ]

    def on_settings_changed(self) -> None:
        """配置变更后重置缓存的设置"""
        self._cached_settings = None

    def _get_config(self):
        if not hasattr(self, '_cached_settings') or self._cached_settings is None:
            self._cached_settings = self.get_settings()
        return self._cached_settings

    def handle(self, query: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        query = query.strip()
        if not query:
            return {
                "type": "display",
                "message": "请输入数学表达式，例如: calc 1+1",
                "data": None,
            }

        try:
            # 构建安全的数学环境
            safe_env = {
                "abs": abs, "round": round, "min": min, "max": max,
                "int": int, "float": float,
                "sin": math.sin, "cos": math.cos, "tan": math.tan,
                "sqrt": math.sqrt, "log": math.log, "log10": math.log10,
                "pi": math.pi, "e": math.e, "pow": pow,
                "ceil": math.ceil, "floor": math.floor,
            }

            # 简单的安全检查
            forbidden = ["import", "exec", "eval", "open", "__", "os.", "sys."]
            for word in forbidden:
                if word in query:
                    return {
                        "type": "display",
                        "message": "⚠️ 不允许的表达式",
                        "data": None,
                    }

            result = eval(query, {"__builtins__": {}}, safe_env)

            # 应用精度设置
            settings = self._get_config()
            precision = settings.get("precision", 6)
            if precision > 0 and isinstance(result, float):
                result = round(result, precision)
                # 去除尾部多余的零
                result_str = f"{result:.{precision}f}".rstrip('0').rstrip('.')
            else:
                result_str = str(result)

            show_expr = settings.get("show_expression", True)
            if show_expr:
                message = f"🧮 {query} = {result_str}"
            else:
                message = f"🧮 {result_str}"

            return {
                "type": "display",
                "message": message,
                "data": result,
            }
        except ZeroDivisionError:
            return {
                "type": "display",
                "message": "⚠️ 除零错误",
                "data": None,
            }
        except Exception as e:
            return {
                "type": "display",
                "message": f"⚠️ 计算错误: {e}",
                "data": None,
            }
