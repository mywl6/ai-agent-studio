"""工具 Service"""
import ast
import sys
from pathlib import Path
from typing import Optional
from sqlalchemy.orm import Session
from backend.models.tool import Tool
from backend.models.tool_category import ToolCategory
from backend.services.base import BaseRepository, BaseService, PaginatedResult
from backend.services.tool_registry import registry
from backend.services.tool_loader import load_single_tool, _load_module
from backend.services.tool_factory import generate_tool_code
from backend.config import TOOLS_CUSTOM_DIR
from backend.security import sandbox_check_code


class ToolRepository(BaseRepository[Tool]):
    def __init__(self, db: Session):
        super().__init__(db, Tool)

    def get_by_name(self, name: str) -> Optional[Tool]:
        return self.db.query(Tool).filter(Tool.name == name).first()

    def list_filtered(self, source: str = "all", category: str = "",
                      skip: int = 0, limit: int = 200) -> PaginatedResult:
        query = self.db.query(Tool)
        if source != "all":
            query = query.filter(Tool.source == source)
        if category:
            query = query.filter(Tool.category == category)

        db_tools = query.all()
        db_names = {t.name for t in db_tools}

        # 合并 registry 中的内置工具
        items = []
        for t in db_tools:
            items.append(self._to_dict(t))
        for meta in registry.get_all_meta():
            if meta["name"] not in db_names:
                items.append({
                    "id": 0, "name": meta["name"],
                    "display_name": meta.get("display_name", meta["name"]),
                    "description": meta["description"],
                    "icon": meta["icon"], "category": meta["category"],
                    "source": "builtin", "code": "", "enabled": True,
                    "params_schema": meta["params_schema"],
                })

        total = len(items)
        paginated = items[skip:skip + limit]
        return PaginatedResult(paginated, total, skip, limit)

    def _to_dict(self, t: Tool) -> dict:
        return {
            "id": t.id, "name": t.name,
            "display_name": t.display_name or t.name,
            "description": t.description, "icon": t.icon,
            "category": t.category, "source": t.source,
            "code": t.code or "", "enabled": t.enabled,
            "params_schema": t.params_schema or {},
        }


class ToolService(BaseService):
    def __init__(self, db: Session):
        self.repo = ToolRepository(db)
        self.db = db

    def list_tools(self, source: str = "all", category: str = "",
                   skip: int = 0, limit: int = 200):
        return self.repo.list_filtered(source, category, skip, limit)

    def save_tool(self, data: dict) -> dict:
        if not data.get("description"):
            raise ValueError("请填写工具描述，AI 需要通过描述来理解工具的用途")
        if not data.get("code"):
            raise ValueError("请填写工具代码")

        try:
            ast.parse(data["code"])
        except SyntaxError as e:
            raise ValueError(f"代码语法错误：{e}")

        existing = self.repo.get_by_name(data["name"])
        if existing:
            for k in ("code", "display_name", "description", "icon", "category"):
                if k in data and data[k]:
                    setattr(existing, k, data[k])
        else:
            tool = Tool(
                name=data["name"],
                display_name=data.get("display_name", data["name"]),
                description=data.get("description", ""),
                icon=data.get("icon", "🔧"),
                category=data.get("category", "通用"),
                source="custom",
                code=data["code"],
            )
            self.db.add(tool)
        self.db.commit()

        filepath = TOOLS_CUSTOM_DIR / f"{data['name']}.py"
        filepath.write_text(data["code"], encoding="utf-8")

        registry.unregister(data["name"])

        try:
            load_single_tool(str(filepath))
        except Exception as e:
            raise ValueError(f"工具代码已保存，但注册到工具中心失败：{e}")

        if registry.has(data["name"]):
            return {"ok": True, "name": data["name"]}

        new_names = [t["name"] for t in registry.get_all_meta()
                     if t["name"] not in self._get_builtin_names()]
        if not new_names:
            raise ValueError(
                f"工具代码已保存，但未检测到 @registry.register 装饰器。"
                f"请确保代码中包含 from backend.services.tool_registry import registry，"
                f"并使用 @registry.register(name=\"{data['name']}\", ...)"
            )

        actual_name = new_names[0]
        self._rename_tool(data["name"], actual_name)
        old_path = TOOLS_CUSTOM_DIR / f"{data['name']}.py"
        new_path = TOOLS_CUSTOM_DIR / f"{actual_name}.py"
        if old_path.exists():
            old_path.rename(new_path)
        return {"ok": True, "name": actual_name}

    def update_tool(self, tool_id: int, data: dict) -> dict:
        tool = self.repo.get_by_id(tool_id)
        if not tool:
            raise ValueError("工具不存在")
        if tool.source == "builtin":
            raise ValueError("不能修改内置工具")

        for key in ("code", "display_name", "description", "icon", "category"):
            if key in data and data[key] is not None:
                if key == "code":
                    try:
                        ast.parse(data["code"])
                    except SyntaxError as e:
                        raise ValueError(f"代码语法错误：{e}")
                setattr(tool, key, data[key])

        if not tool.description:
            raise ValueError("工具描述不能为空")
        self.db.commit()

        filepath = TOOLS_CUSTOM_DIR / f"{tool.name}.py"
        if tool.code:
            filepath.write_text(tool.code, encoding="utf-8")
            load_single_tool(str(filepath))
        return {"ok": True}

    def delete_tool(self, tool_id: int) -> dict:
        tool = self.repo.get_by_id(tool_id)
        if not tool:
            raise ValueError("工具不存在")
        if tool.source == "builtin":
            raise ValueError("不能删除内置工具")
        self.repo.delete(tool)
        filepath = TOOLS_CUSTOM_DIR / f"{tool.name}.py"
        if filepath.exists():
            filepath.unlink()
        registry.unregister(tool.name)
        return {"ok": True}

    def toggle_tool(self, tool_id: int) -> dict:
        tool = self.repo.get_by_id(tool_id)
        if not tool:
            raise ValueError("工具不存在")
        tool.enabled = not tool.enabled
        self.db.commit()
        return {"ok": True, "enabled": tool.enabled}

    def _get_builtin_names(self) -> set:
        return {"calculator", "run_command", "list_directory", "read_file",
                "write_file", "http_request", "web_search"}

    def _rename_tool(self, old_name: str, new_name: str):
        tool = self.repo.get_by_name(old_name)
        if tool:
            tool.name = new_name
            self.db.commit()

    async def generate_from_api(self, input_type: str, content: str, model_id: str) -> dict:
        return await generate_tool_code(input_type, content, model_id)