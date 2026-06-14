"""智能体 CRUD — 通过 Service 层"""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import Optional
from backend.di import get_agent_service
from backend.services.agent_service import AgentService

router = APIRouter(prefix="/api/agents", tags=["agents"])


class AgentCreate(BaseModel):
    name: str
    avatar: str = "🤖"
    description: str = ""
    model_id: str
    system_prompt: str = "你是一个有用的 AI 助手。"
    tools: list[str] = []
    search_enabled: bool = True
    temperature: int = 70
    max_tokens: int = 4096
    max_history: int = 20


class AgentUpdate(BaseModel):
    name: Optional[str] = None
    avatar: Optional[str] = None
    description: Optional[str] = None
    model_id: Optional[str] = None
    system_prompt: Optional[str] = None
    tools: Optional[list[str]] = None
    search_enabled: Optional[bool] = None
    temperature: Optional[int] = None
    max_tokens: Optional[int] = None
    max_history: Optional[int] = None


@router.get("")
async def list_agents(
    skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=200),
    svc: AgentService = Depends(get_agent_service),
):
    return svc.list_agents(skip, limit).to_dict()


@router.get("/{agent_id}")
async def get_agent(agent_id: int, svc: AgentService = Depends(get_agent_service)):
    result = svc.get_agent(agent_id)
    if not result:
        raise HTTPException(404, "智能体不存在")
    return result


@router.post("")
async def create_agent(config: AgentCreate, svc: AgentService = Depends(get_agent_service)):
    try:
        return svc.create_agent(config.model_dump())
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.put("/{agent_id}")
async def update_agent(agent_id: int, config: AgentUpdate,
                        svc: AgentService = Depends(get_agent_service)):
    try:
        return svc.update_agent(agent_id, config.model_dump(exclude_none=True))
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.delete("/{agent_id}")
async def delete_agent(agent_id: int, svc: AgentService = Depends(get_agent_service)):
    try:
        return svc.delete_agent(agent_id)
    except ValueError as e:
        raise HTTPException(404, str(e))


@router.post("/{agent_id}/clone")
async def clone_agent(agent_id: int, svc: AgentService = Depends(get_agent_service)):
    try:
        return svc.clone_agent(agent_id)
    except ValueError as e:
        raise HTTPException(404, str(e))