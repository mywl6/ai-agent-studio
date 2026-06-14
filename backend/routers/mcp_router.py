"""MCP 服务器路由"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from backend.di import get_mcp_service
from backend.services.mcp_manager import MCPService

router = APIRouter(prefix="/api/mcp", tags=["mcp"])


class MCPServerCreate(BaseModel):
    name: str
    description: str = ""
    server_type: str = "stdio"
    command: str = ""
    url: str = ""
    args: list = []
    env: dict = {}
    tools_auto_discover: bool = True


class MCPServerUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    server_type: Optional[str] = None
    command: Optional[str] = None
    url: Optional[str] = None
    args: Optional[list] = None
    env: Optional[dict] = None
    tools_auto_discover: Optional[bool] = None
    enabled: Optional[bool] = None


@router.get("")
async def list_servers(svc: MCPService = Depends(get_mcp_service)):
    return svc.list_servers()


@router.post("")
async def create_server(config: MCPServerCreate, svc: MCPService = Depends(get_mcp_service)):
    try:
        return svc.create_server(config.model_dump())
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.put("/{server_id}")
async def update_server(server_id: int, config: MCPServerUpdate,
                         svc: MCPService = Depends(get_mcp_service)):
    return svc.update_server(server_id, config.model_dump(exclude_none=True))


@router.delete("/{server_id}")
async def delete_server(server_id: int, svc: MCPService = Depends(get_mcp_service)):
    return svc.delete_server(server_id)


@router.post("/{server_id}/discover")
async def discover_tools(server_id: int, svc: MCPService = Depends(get_mcp_service)):
    try:
        return {"tools": svc.discover_tools(server_id)}
    except ValueError as e:
        raise HTTPException(400, str(e))