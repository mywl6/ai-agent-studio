"""工具路由 — 通过 Service 层 + MCP 支持"""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import Optional
from backend.di import get_tool_service, get_model_pool, get_tool_registry
from backend.services.tool_service import ToolService
from backend.services.model_pool import ModelPool
from backend.services.tool_registry import ToolRegistry
from backend.security import execute_sandboxed

router = APIRouter(prefix="/api/tools", tags=["tools"])


class ToolCreate(BaseModel):
    name: str
    code: str
    display_name: str = ""
    description: str = ""
    icon: str = "🔧"
    category: str = "通用"


class ToolUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    display_name: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    category: Optional[str] = None


class ToolGenerate(BaseModel):
    type: str
    content: str


class ToolTest(BaseModel):
    code: str
    test_params: dict = {}


class ToolExecute(BaseModel):
    name: str
    params: dict = {}


@router.get("")
async def list_tools(
    source: str = "all", category: str = "",
    skip: int = Query(0, ge=0), limit: int = Query(200, ge=1, le=500),
    svc: ToolService = Depends(get_tool_service),
):
    return svc.list_tools(source, category, skip, limit).to_dict()


@router.post("/generate")
async def generate_tool(config: ToolGenerate, svc: ToolService = Depends(get_tool_service),
                         mp: ModelPool = Depends(get_model_pool)):
    from backend.database import SessionLocal
    from backend.models.model_provider import ModelProvider
    db = SessionLocal()
    try:
        model = db.query(ModelProvider).filter(ModelProvider.enabled == True).first()
        if not model:
            raise HTTPException(400, "无可用模型")
        result = await svc.generate_from_api(config.type, config.content, model.id)
        return result
    except Exception as e:
        raise HTTPException(400, str(e))
    finally:
        db.close()


@router.post("/test")
async def test_tool(config: ToolTest, registry: ToolRegistry = Depends(get_tool_registry)):
    """在沙箱中测试工具代码"""
    result = execute_sandboxed(config.code, {"registry": registry})
    if not result["ok"]:
        raise HTTPException(400, result["error"])
    return {"result": "代码语法检查通过"}


@router.post("")
async def save_tool(config: ToolCreate, svc: ToolService = Depends(get_tool_service)):
    try:
        return svc.save_tool(config.model_dump())
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.put("/{tool_id}")
async def update_tool(tool_id: int, config: ToolUpdate,
                       svc: ToolService = Depends(get_tool_service)):
    try:
        return svc.update_tool(tool_id, config.model_dump(exclude_none=True))
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.delete("/{tool_id}")
async def delete_tool(tool_id: int, svc: ToolService = Depends(get_tool_service)):
    try:
        return svc.delete_tool(tool_id)
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.post("/{tool_id}/toggle")
async def toggle_tool(tool_id: int, svc: ToolService = Depends(get_tool_service)):
    try:
        return svc.toggle_tool(tool_id)
    except ValueError as e:
        raise HTTPException(404, str(e))


@router.post("/reload")
async def reload_tools(svc: ToolService = Depends(get_tool_service)):
    from backend.services.tool_loader import load_custom_tools
    load_custom_tools()
    return {"loaded": True}


@router.post("/execute")
async def execute_tool(config: ToolExecute,
                        registry: ToolRegistry = Depends(get_tool_registry)):
    result = await registry.execute(config.name, config.params)
    return {"result": result}