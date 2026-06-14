"""集群 Service：集群管理、工作流、任务调度"""
from typing import Optional
from sqlalchemy.orm import Session
from backend.models.cluster import AgentCluster, ClusterWorkflow, ClusterAgentAssignment, ClusterTask
from backend.services.base import BaseRepository, BaseService, PaginatedResult
from backend.services.agent_service import AgentRepository
from backend.services.tool_registry import registry
from backend.workspace import get_cluster_shared_dir, get_agent_cluster_workspace


class ClusterRepository(BaseRepository[AgentCluster]):
    def __init__(self, db: Session):
        super().__init__(db, AgentCluster)

    def list_with_count(self, skip: int = 0, limit: int = 100) -> PaginatedResult:
        query = self.db.query(AgentCluster).filter(AgentCluster.is_active == True)
        total = query.count()
        items = query.order_by(AgentCluster.created_at.desc()).offset(skip).limit(limit).all()
        return PaginatedResult([self._to_dict(c) for c in items], total, skip, limit)

    def _to_dict(self, c: AgentCluster) -> dict:
        member_count = self.db.query(ClusterAgentAssignment).filter(
            ClusterAgentAssignment.cluster_id == c.id).count()
        return {
            "id": c.id, "name": c.name, "description": c.description,
            "icon": c.icon, "is_active": c.is_active,
            "member_count": member_count,
            "created_at": str(c.created_at),
        }


class WorkflowRepository(BaseRepository[ClusterWorkflow]):
    def __init__(self, db: Session):
        super().__init__(db, ClusterWorkflow)

    def list_by_cluster(self, cluster_id: int, skip: int = 0, limit: int = 100) -> PaginatedResult:
        query = self.db.query(ClusterWorkflow).filter(
            ClusterWorkflow.cluster_id == cluster_id)
        total = query.count()
        items = query.order_by(ClusterWorkflow.created_at.desc()).offset(skip).limit(limit).all()
        return PaginatedResult([self._to_dict(w) for w in items], total, skip, limit)

    def _to_dict(self, w: ClusterWorkflow) -> dict:
        return {
            "id": w.id, "cluster_id": w.cluster_id, "name": w.name,
            "description": w.description, "steps": w.steps or [],
            "hooks": w.hooks or [], "is_optimized": w.is_optimized,
            "is_active": w.is_active,
            "step_count": len(w.steps or []),
            "created_at": str(w.created_at),
        }


class AssignmentRepository(BaseRepository[ClusterAgentAssignment]):
    def __init__(self, db: Session):
        super().__init__(db, ClusterAgentAssignment)


class TaskRepository(BaseRepository[ClusterTask]):
    def __init__(self, db: Session):
        super().__init__(db, ClusterTask)

    def list_by_cluster(self, cluster_id: int, status: str = "",
                        skip: int = 0, limit: int = 50) -> PaginatedResult:
        query = self.db.query(ClusterTask).filter(ClusterTask.cluster_id == cluster_id)
        if status:
            query = query.filter(ClusterTask.status == status)
        total = query.count()
        items = query.order_by(ClusterTask.created_at.desc()).offset(skip).limit(limit).all()
        return PaginatedResult([self._to_dict(t) for t in items], total, skip, limit)

    def _to_dict(self, t: ClusterTask) -> dict:
        return {
            "id": t.id, "cluster_id": t.cluster_id, "workflow_id": t.workflow_id,
            "title": t.title, "status": t.status,
            "current_step": t.current_step, "total_steps": t.total_steps,
            "assigned_agent_id": t.assigned_agent_id,
            "input_data": t.input_data, "output_data": t.output_data,
            "error": t.error,
            "created_at": str(t.created_at),
        }


class ClusterService(BaseService):
    """集群服务"""

    def __init__(self, db: Session):
        self.db = db
        self.cluster_repo = ClusterRepository(db)
        self.workflow_repo = WorkflowRepository(db)
        self.assignment_repo = AssignmentRepository(db)
        self.task_repo = TaskRepository(db)
        self.agent_repo = AgentRepository(db)

    # ── 集群 CRUD ──

    def list_clusters(self, skip: int = 0, limit: int = 100):
        return self.cluster_repo.list_with_count(skip, limit)

    def get_cluster(self, cluster_id: int):
        c = self.cluster_repo.get_by_id(cluster_id)
        if not c:
            raise ValueError("集群不存在")
        members = self.db.query(ClusterAgentAssignment).filter(
            ClusterAgentAssignment.cluster_id == cluster_id).all()
        workflows = self.workflow_repo.list_by_cluster(cluster_id)
        return {
            "id": c.id, "name": c.name, "description": c.description,
            "icon": c.icon, "is_active": c.is_active,
            "created_at": str(c.created_at),
            "members": [
                {
                    "id": m.id, "agent_id": m.agent_id,
                    "role": m.role, "workspace_enabled": m.workspace_enabled,
                    "config": m.config,
                }
                for m in members
            ],
            "workflows": workflows.to_dict()["items"],
            "shared_dir": str(get_cluster_shared_dir(cluster_id)),
        }

    def create_cluster(self, data: dict) -> dict:
        cluster = AgentCluster(**data)
        self.cluster_repo.add(cluster)
        get_cluster_shared_dir(cluster.id)
        return {"ok": True, "id": cluster.id}

    def update_cluster(self, cluster_id: int, data: dict) -> dict:
        cluster = self.cluster_repo.get_by_id(cluster_id)
        if not cluster:
            raise ValueError("集群不存在")
        for k, v in data.items():
            if v is not None:
                setattr(cluster, k, v)
        self.db.commit()
        return {"ok": True}

    def delete_cluster(self, cluster_id: int) -> dict:
        cluster = self.cluster_repo.get_by_id(cluster_id)
        if not cluster:
            raise ValueError("集群不存在")
        cluster.is_active = False
        self.db.commit()
        return {"ok": True}

    # ── 成员管理 ──

    def add_member(self, cluster_id: int, agent_id: int, role: str = "member") -> dict:
        existing = self.db.query(ClusterAgentAssignment).filter(
            ClusterAgentAssignment.cluster_id == cluster_id,
            ClusterAgentAssignment.agent_id == agent_id,
        ).first()
        if existing:
            raise ValueError("该智能体已在集群中")
        agent = self.agent_repo.get_by_id(agent_id)
        if not agent:
            raise ValueError("智能体不存在")
        assignment = ClusterAgentAssignment(
            cluster_id=cluster_id, agent_id=agent_id, role=role,
        )
        self.assignment_repo.add(assignment)
        return {"ok": True, "id": assignment.id}

    def remove_member(self, assignment_id: int) -> dict:
        a = self.assignment_repo.get_by_id(assignment_id)
        if not a:
            raise ValueError("关联不存在")
        self.assignment_repo.delete(a)
        return {"ok": True}

    def get_agent_workspace(self, cluster_id: int, agent_id: int) -> str:
        return str(get_agent_cluster_workspace(cluster_id, agent_id))

    # ── 工作流 ──

    def list_workflows(self, cluster_id: int, skip: int = 0, limit: int = 100):
        return self.workflow_repo.list_by_cluster(cluster_id, skip, limit)

    def create_workflow(self, data: dict) -> dict:
        wf = ClusterWorkflow(**data)
        self.workflow_repo.add(wf)
        return {"ok": True, "id": wf.id}

    def update_workflow(self, workflow_id: int, data: dict) -> dict:
        wf = self.workflow_repo.get_by_id(workflow_id)
        if not wf:
            raise ValueError("工作流不存在")
        for k, v in data.items():
            if v is not None:
                setattr(wf, k, v)
        self.db.commit()
        return {"ok": True}

    def optimize_workflow(self, workflow_id: int) -> dict:
        """AI 优化工作流：重新排序步骤、合并、补充钩子"""
        wf = self.workflow_repo.get_by_id(workflow_id)
        if not wf:
            raise ValueError("工作流不存在")
        steps = wf.steps or []
        if not steps:
            return {"ok": True, "message": "没有步骤需要优化"}

        # 基础优化：按依赖排序，自动添加钩子
        ordered = sorted(steps, key=lambda s: s.get("order", 0))
        for i, step in enumerate(ordered):
            step["order"] = i + 1
            if "hooks" not in step:
                step["hooks"] = []

        wf.steps = ordered
        wf.is_optimized = True

        # 自动添加钩子
        hooks = wf.hooks or []
        if not any(h.get("trigger") == "on_complete" for h in hooks):
            hooks.append({
                "trigger": "on_complete",
                "type": "notification",
                "config": {"message": "工作流 {{workflow.name}} 已完成"},
            })
        wf.hooks = hooks
        self.db.commit()
        return {"ok": True, "steps": ordered, "hooks": hooks}

    # ── 任务 ──

    def list_tasks(self, cluster_id: int, status: str = "",
                   skip: int = 0, limit: int = 50):
        return self.task_repo.list_by_cluster(cluster_id, status, skip, limit)

    def create_task(self, data: dict) -> dict:
        task = ClusterTask(**data)
        self.task_repo.add(task)
        return {"ok": True, "id": task.id}

    def execute_task(self, task_id: int) -> dict:
        """执行任务（按工作流步骤调度）"""
        task = self.task_repo.get_by_id(task_id)
        if not task:
            raise ValueError("任务不存在")
        if task.status == "running":
            raise ValueError("任务正在运行中")

        task.status = "running"
        self.db.commit()

        try:
            wf = self.workflow_repo.get_by_id(task.workflow_id) if task.workflow_id else None
            steps = wf.steps if wf else []
            task.total_steps = len(steps)

            for i, step in enumerate(steps):
                task.current_step = i + 1
                # 执行步骤前钩子
                self._run_hooks(wf, "before_step", step)
                # 分配智能体
                if step.get("agent_id") and not task.assigned_agent_id:
                    task.assigned_agent_id = step["agent_id"]
                # 更新状态
                self.db.commit()
                # 执行步骤后钩子
                self._run_hooks(wf, "after_step", step)

            task.status = "completed"
            self._run_hooks(wf, "on_complete", task)
        except Exception as e:
            task.status = "failed"
            task.error = str(e)
            self._run_hooks(wf, "on_error", {"error": str(e)})

        self.db.commit()
        return {"ok": True, "status": task.status}

    def _run_hooks(self, wf: Optional[ClusterWorkflow], trigger: str, context: dict):
        """执行指定 trigger 的钩子"""
        hooks = (wf.hooks or []) if wf else []
        for step in (wf.steps or []) if wf else []:
            for hook in (step.get("hooks", []) or []):
                if hook.get("trigger") == trigger:
                    hooks.append(hook)
        for hook in hooks:
            if hook.get("trigger") == trigger:
                hook_type = hook.get("type", "")
                config = hook.get("config", {})
                if hook_type == "log":
                    import logging
                    logging.info(f"[Hook:{trigger}] {config.get('message', '')}")
                elif hook_type == "webhook":
                    pass  # TODO: HTTP 回调