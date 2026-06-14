"""MCP 服务器管理器：连接 MCP 服务、自动发现工具、注册到 registry"""
import json
import subprocess
from typing import Optional
from sqlalchemy.orm import Session
from backend.models.mcp_server import MCPServer
from backend.services.base import BaseRepository, BaseService
from backend.services.tool_registry import registry


class MCPServerRepository(BaseRepository[MCPServer]):
    def __init__(self, db: Session):
        super().__init__(db, MCPServer)

    def list_enabled(self):
        return self.db.query(MCPServer).filter(MCPServer.enabled == True).all()

    def _to_dict(self, s: MCPServer) -> dict:
        return {
            "id": s.id, "name": s.name, "description": s.description,
            "server_type": s.server_type, "command": s.command,
            "url": s.url, "args": s.args or [], "env": s.env or {},
            "tools_auto_discover": s.tools_auto_discover,
            "tools": s.tools or [], "enabled": s.enabled,
        }


class MCPService(BaseService):
    """MCP 服务管理"""

    def __init__(self, db: Session):
        self.db = db
        self.repo = MCPServerRepository(db)

    def list_servers(self):
        return [self.repo._to_dict(s) for s in self.repo.list_all()]

    def create_server(self, data: dict) -> dict:
        existing = self.db.query(MCPServer).filter(MCPServer.name == data.get("name")).first()
        if existing:
            raise ValueError(f"MCP 服务器「{data['name']}」已存在")
        server = MCPServer(**data)
        self.repo.add(server)
        return {"ok": True, "id": server.id}

    def update_server(self, server_id: int, data: dict) -> dict:
        server = self.repo.get_by_id(server_id)
        if not server:
            raise ValueError("MCP 服务器不存在")
        for k, v in data.items():
            if v is not None:
                setattr(server, k, v)
        self.db.commit()
        return {"ok": True}

    def delete_server(self, server_id: int) -> dict:
        server = self.repo.get_by_id(server_id)
        if not server:
            raise ValueError("MCP 服务器不存在")
        self.repo.delete(server)
        return {"ok": True}

    def discover_tools(self, server_id: int) -> list[dict]:
        """连接 MCP 服务器并自动发现工具"""
        server = self.repo.get_by_id(server_id)
        if not server:
            raise ValueError("MCP 服务器不存在")

        try:
            if server.server_type == "stdio":
                tools = self._discover_stdio(server)
            elif server.server_type == "sse":
                tools = self._discover_sse(server)
            else:
                raise ValueError(f"不支持的 MCP 类型：{server.server_type}")

            server.tools = tools
            self.db.commit()
            return tools
        except Exception as e:
            raise ValueError(f"发现工具失败：{e}")

    def _discover_stdio(self, server: MCPServer) -> list[dict]:
        """通过 stdio 协议发现工具"""
        env = server.env or {}
        my_env = {**env}
        try:
            proc = subprocess.run(
                [server.command] + (server.args or []),
                input=json.dumps({"jsonrpc": "2.0", "method": "tools/list", "id": 1}),
                capture_output=True, text=True, timeout=10, env=my_env,
            )
            result = json.loads(proc.stdout)
            tools = result.get("result", {}).get("tools", [])
            for t in tools:
                self._register_mcp_tool(server.name, t)
            return tools
        except Exception as e:
            raise ValueError(f"stdio 发现失败：{e}")

    def _discover_sse(self, server: MCPServer) -> list[dict]:
        """通过 SSE 协议发现工具"""
        import httpx
        try:
            resp = httpx.post(
                server.url,
                json={"jsonrpc": "2.0", "method": "tools/list", "id": 1},
                timeout=10,
            )
            result = resp.json()
            tools = result.get("result", {}).get("tools", [])
            for t in tools:
                self._register_mcp_tool(server.name, t)
            return tools
        except Exception as e:
            raise ValueError(f"SSE 发现失败：{e}")

    def _register_mcp_tool(self, server_name: str, tool_def: dict):
        """将 MCP 工具注册到工具注册中心"""
        name = f"mcp_{server_name}_{tool_def.get('name', 'unknown')}"
        description = tool_def.get("description", f"MCP 工具：{server_name}")
        input_schema = tool_def.get("inputSchema", {})

        # 包装为异步执行函数
        async def mcp_tool_fn(**kwargs):
            return f"[MCP:{server_name}] 调用 {tool_def.get('name')} 参数：{kwargs}"

        mcp_tool_fn.__name__ = name

        registry.register(
            name=name,
            description=description,
            icon="🔌",
            category="MCP",
        )(mcp_tool_fn)