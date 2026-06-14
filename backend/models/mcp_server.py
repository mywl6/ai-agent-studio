"""MCP 服务器注册模型"""
from datetime import datetime
from sqlalchemy import Column, String, Integer, Text, Boolean, DateTime
from sqlalchemy.types import JSON
from backend.database import Base


class MCPServer(Base):
    """MCP 服务器注册"""
    __tablename__ = "mcp_servers"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text, default="")
    server_type = Column(String(20), default="stdio")      # stdio / sse
    command = Column(String(500), default="")               # stdio 启动命令
    url = Column(String(500), default="")                   # SSE URL
    args = Column(JSON, default=list)
    env = Column(JSON, default=dict)
    tools_auto_discover = Column(Boolean, default=True)     # 自动发现工具
    tools = Column(JSON, default=list)                      # 手动声明工具
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)