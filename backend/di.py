"""依赖注入工厂 — FastAPI Depends 链式解析"""
from fastapi import Depends
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.services.model_pool import ModelPool
from backend.services.tool_registry import ToolRegistry

_model_pool_instance = None
_registry_instance = None


def get_model_pool() -> ModelPool:
    global _model_pool_instance
    if _model_pool_instance is None:
        from backend.services.model_pool import model_pool
        _model_pool_instance = model_pool
    return _model_pool_instance


def get_tool_registry() -> ToolRegistry:
    global _registry_instance
    if _registry_instance is None:
        from backend.services.tool_registry import registry
        _registry_instance = registry
    return _registry_instance


def get_agent_service(db: Session = Depends(get_db)):
    from backend.services.agent_service import AgentService
    return AgentService(db)


def get_tool_service(db: Session = Depends(get_db)):
    from backend.services.tool_service import ToolService
    return ToolService(db)


def get_cluster_service(db: Session = Depends(get_db)):
    from backend.services.cluster_service import ClusterService
    return ClusterService(db)


def get_mcp_service(db: Session = Depends(get_db)):
    from backend.services.mcp_manager import MCPService
    return MCPService(db)