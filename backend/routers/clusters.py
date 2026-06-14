"""集群路由：集群管理 + 工作流 + 任务调度"""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import Optional
from backend.di import get_cluster_service
from backend.services.cluster_service import ClusterService

router = APIRouter(prefix="/api/clusters", tags=["clusters"])


class ClusterCreate(BaseModel):
    name: str
    description: str = ""
    icon: str = "🌐"


class ClusterUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None


class WorkflowCreate(BaseModel):
    cluster_id: int
    name: str
    description: str = ""
    steps: list = []
    hooks: list = []


class WorkflowUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    steps: Optional[list] = None
    hooks: Optional[list] = None


class MemberAdd(BaseModel):
    cluster_id: int
    agent_id: int
    role: str = "member"


class TaskCreate(BaseModel):
    cluster_id: int
    workflow_id: Optional[int] = None
    title: str
    input_data: dict = {}


def _ok(data=None):
    return data if data else {"ok": True}


# ── 集群 CRUD ──

@router.get("")
async def list_clusters(
    skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=200),
    svc: ClusterService = Depends(get_cluster_service),
):
    return svc.list_clusters(skip, limit).to_dict()


@router.post("")
async def create_cluster(config: ClusterCreate, svc: ClusterService = Depends(get_cluster_service)):
    return svc.create_cluster(config.model_dump())


@router.get("/{cluster_id}")
async def get_cluster(cluster_id: int, svc: ClusterService = Depends(get_cluster_service)):
    try:
        return svc.get_cluster(cluster_id)
    except ValueError as e:
        raise HTTPException(404, str(e))


@router.put("/{cluster_id}")
async def update_cluster(cluster_id: int, config: ClusterUpdate,
                          svc: ClusterService = Depends(get_cluster_service)):
    return svc.update_cluster(cluster_id, config.model_dump(exclude_none=True))


@router.delete("/{cluster_id}")
async def delete_cluster(cluster_id: int, svc: ClusterService = Depends(get_cluster_service)):
    return svc.delete_cluster(cluster_id)


# ── 成员管理 ──

@router.post("/members")
async def add_member(config: MemberAdd, svc: ClusterService = Depends(get_cluster_service)):
    try:
        return svc.add_member(config.cluster_id, config.agent_id, config.role)
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.delete("/members/{assignment_id}")
async def remove_member(assignment_id: int, svc: ClusterService = Depends(get_cluster_service)):
    return svc.remove_member(assignment_id)


@router.get("/{cluster_id}/agents/{agent_id}/workspace")
async def get_workspace(cluster_id: int, agent_id: int,
                         svc: ClusterService = Depends(get_cluster_service)):
    return {"workspace": svc.get_agent_workspace(cluster_id, agent_id)}


# ── 工作流 ──

@router.get("/{cluster_id}/workflows")
async def list_workflows(
    cluster_id: int,
    skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=200),
    svc: ClusterService = Depends(get_cluster_service),
):
    return svc.list_workflows(cluster_id, skip, limit).to_dict()


@router.post("/workflows")
async def create_workflow(config: WorkflowCreate, svc: ClusterService = Depends(get_cluster_service)):
    return svc.create_workflow(config.model_dump())


@router.get("/workflows/{workflow_id}")
async def get_workflow(workflow_id: int, svc: ClusterService = Depends(get_cluster_service)):
    from backend.models.cluster import ClusterWorkflow
    wf = svc.workflow_repo.get_by_id(workflow_id)
    if not wf:
        raise HTTPException(404, "工作流不存在")
    return svc.workflow_repo._to_dict(wf)


@router.put("/workflows/{workflow_id}")
async def update_workflow(workflow_id: int, config: WorkflowUpdate,
                           svc: ClusterService = Depends(get_cluster_service)):
    return svc.update_workflow(workflow_id, config.model_dump(exclude_none=True))


@router.post("/workflows/{workflow_id}/optimize")
async def optimize_workflow(workflow_id: int, svc: ClusterService = Depends(get_cluster_service)):
    try:
        return svc.optimize_workflow(workflow_id)
    except ValueError as e:
        raise HTTPException(400, str(e))


# ── 任务 ──

@router.get("/{cluster_id}/tasks")
async def list_tasks(
    cluster_id: int, status: str = "",
    skip: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=200),
    svc: ClusterService = Depends(get_cluster_service),
):
    return svc.list_tasks(cluster_id, status, skip, limit).to_dict()


@router.post("/tasks")
async def create_task(config: TaskCreate, svc: ClusterService = Depends(get_cluster_service)):
    return svc.create_task(config.model_dump())


@router.post("/tasks/{task_id}/execute")
async def execute_task(task_id: int, svc: ClusterService = Depends(get_cluster_service)):
    try:
        return svc.execute_task(task_id)
    except ValueError as e:
        raise HTTPException(400, str(e))