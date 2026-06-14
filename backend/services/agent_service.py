"""智能体 Service"""
from typing import Optional
from sqlalchemy.orm import Session
from backend.models.agent import Agent
from backend.models.model_provider import ModelProvider
from backend.models.tool import Tool
from backend.services.base import BaseRepository, BaseService, PaginatedResult
from backend.services.tool_registry import registry


class AgentRepository(BaseRepository[Agent]):
    def __init__(self, db: Session):
        super().__init__(db, Agent)

    def list_with_count(self, skip: int = 0, limit: int = 100) -> PaginatedResult:
        query = self.db.query(Agent).order_by(Agent.created_at.desc())
        total = query.count()
        agents = query.offset(skip).limit(limit).all()
        items = [self._to_dict(a) for a in agents]
        return PaginatedResult(items, total, skip, limit)

    def get_detail(self, agent_id: int) -> Optional[dict]:
        agent = self.get_by_id(agent_id)
        return self._to_dict(agent) if agent else None

    def _to_dict(self, a: Agent) -> dict:
        return {
            "id": a.id, "name": a.name, "avatar": a.avatar,
            "description": a.description, "model_id": a.model_id,
            "system_prompt": a.system_prompt, "tools": a.tools or [],
            "search_enabled": bool(a.search_enabled),
            "temperature": a.temperature, "max_tokens": a.max_tokens,
            "max_history": a.max_history,
            "tool_count": len(a.tools or []),
        }

    def validate_model(self, model_id: str) -> bool:
        return self.db.query(ModelProvider).filter(ModelProvider.id == model_id).count() > 0

    def validate_tools(self, tool_names: list[str]) -> list[str]:
        if not tool_names:
            return []
        registered = {t["name"] for t in registry.get_all_meta()}
        db_names = {t.name for t in self.db.query(Tool).all()}
        return [t for t in tool_names if t not in registered and t not in db_names]


class AgentService(BaseService):
    def __init__(self, db: Session):
        self.repo = AgentRepository(db)
        self.db = db

    def list_agents(self, skip: int = 0, limit: int = 100):
        return self.repo.list_with_count(skip, limit)

    def get_agent(self, agent_id: int):
        return self.repo.get_detail(agent_id)

    def create_agent(self, data: dict) -> dict:
        if not self.repo.validate_model(data.get("model_id", "")):
            raise ValueError(f"模型「{data['model_id']}」不存在")
        missing = self.repo.validate_tools(data.get("tools", []))
        if missing:
            raise ValueError(f"以下工具不存在：{', '.join(missing)}")
        agent = Agent(**data)
        self.repo.add(agent)
        return {"ok": True, "id": agent.id}

    def update_agent(self, agent_id: int, data: dict) -> dict:
        agent = self.repo.get_by_id(agent_id)
        if not agent:
            raise ValueError("智能体不存在")
        if "model_id" in data and data["model_id"]:
            if not self.repo.validate_model(data["model_id"]):
                raise ValueError(f"模型「{data['model_id']}」不存在")
        if "tools" in data:
            missing = self.repo.validate_tools(data["tools"])
            if missing:
                raise ValueError(f"以下工具不存在：{', '.join(missing)}")
        for key, value in data.items():
            if value is not None:
                setattr(agent, key, value)
        self.db.commit()
        return {"ok": True}

    def delete_agent(self, agent_id: int) -> dict:
        agent = self.repo.get_by_id(agent_id)
        if not agent:
            raise ValueError("智能体不存在")
        self.repo.delete(agent)
        return {"ok": True}

    def clone_agent(self, agent_id: int) -> dict:
        agent = self.repo.get_by_id(agent_id)
        if not agent:
            raise ValueError("智能体不存在")
        new = Agent(
            name=f"{agent.name} (副本)", avatar=agent.avatar,
            description=agent.description, model_id=agent.model_id,
            system_prompt=agent.system_prompt, tools=list(agent.tools or []),
            temperature=agent.temperature, max_history=agent.max_history,
        )
        self.repo.add(new)
        return {"ok": True, "id": new.id}