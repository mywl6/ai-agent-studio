"""工具注册中心：装饰器 + 元数据管理"""
import inspect
from typing import Callable, Any


class ToolRegistry:
    """工具注册中心，使用装饰器注册工具"""

    def __init__(self):
        self._tools: dict[str, dict] = {}

    def register(
        self,
        name: str = "",
        description: str = "",
        icon: str = "🔧",
        category: str = "通用",
    ):
        """装饰器：注册工具"""
        def decorator(func: Callable):
            tool_name = name or func.__name__
            schema = self._extract_schema(func)
            self._tools[tool_name] = {
                "name": tool_name,
                "description": description or func.__doc__ or "",
                "icon": icon,
                "category": category,
                "func": func,
                "params_schema": schema,
            }
            return func
        return decorator

    def _extract_schema(self, func: Callable) -> dict:
        """通过 inspect 自动提取参数 JSON Schema"""
        sig = inspect.signature(func)
        properties = {}
        required = []
        type_map = {
            str: "string", int: "integer", float: "number",
            bool: "boolean", list: "array", dict: "object",
        }
        for pname, param in sig.parameters.items():
            prop = {}
            if param.annotation != inspect.Parameter.empty:
                prop["type"] = type_map.get(param.annotation, "string")
            else:
                prop["type"] = "string"
            if param.default != inspect.Parameter.empty:
                prop["default"] = param.default
            else:
                required.append(pname)
            properties[pname] = prop
        return {"type": "object", "properties": properties, "required": required}

    async def execute(self, name: str, params: dict) -> str:
        """执行工具，返回结果字符串"""
        if name not in self._tools:
            return f"错误：工具 {name} 不存在"
        try:
            func = self._tools[name]["func"]
            result = func(**params)
            if inspect.isawaitable(result):
                result = await result
            return str(result)
        except Exception as e:
            return f"工具执行错误：{e}"

    def get_all_meta(self) -> list[dict]:
        """返回所有工具元数据"""
        return [
            {
                "name": t["name"],
                "description": t["description"],
                "icon": t["icon"],
                "category": t["category"],
                "params_schema": t["params_schema"],
            }
            for t in self._tools.values()
        ]

    def get_tool(self, name: str) -> dict | None:
        return self._tools.get(name)

    def get_tools_for_llm(self, tool_names: list[str]) -> list[dict]:
        """生成 OpenAI function calling 格式的工具描述"""
        result = []
        for name in tool_names:
            if name in self._tools:
                t = self._tools[name]
                result.append({
                    "type": "function",
                    "function": {
                        "name": t["name"],
                        "description": t["description"],
                        "parameters": t["params_schema"],
                    },
                })
        return result

    def unregister(self, name: str):
        self._tools.pop(name, None)

    def has(self, name: str) -> bool:
        return name in self._tools


registry = ToolRegistry()
