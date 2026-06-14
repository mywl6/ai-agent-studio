"""集群对话引擎：多智能体协作 + 工作流路由"""
import json
import os
from typing import AsyncGenerator, Optional, Callable
from backend.services.model_pool import ModelPool
from backend.services.tool_registry import ToolRegistry
from backend.services.agent_engine import AgentEngine
from backend.workspace import get_conversation_workspace
from backend.models.cluster import AgentCluster, ClusterWorkflow, ClusterAgentAssignment


class ClusterChatEngine:
    """集群对话引擎：根据工作流将消息路由到不同的智能体"""

    def __init__(
        self,
        cluster: AgentCluster,
        workflow: Optional[ClusterWorkflow],
        members: list[ClusterAgentAssignment],
        conversation_id: int,
        db_session_factory: Optional[Callable] = None,
        model_pool: ModelPool = None,
        registry: ToolRegistry = None,
        uploaded_files: list[dict] = None,
        search_enabled: bool = False,
    ):
        self.cluster = cluster
        self.workflow = workflow
        self.members = {m.agent_id: m for m in members}
        self.conversation_id = conversation_id
        self.db_session_factory = db_session_factory
        self._model_pool = model_pool
        self._registry = registry
        self._uploaded_files = uploaded_files or []
        self._search_enabled = search_enabled
        self.history: list[dict] = []

        # 共享工作空间（集群下所有智能体共享）
        self.workspace = None
        if conversation_id:
            self.workspace = get_conversation_workspace(
                0, conversation_id, cluster_id=cluster.id
            )

        # 步骤索引
        self._step_index = 0
        self._steps = (workflow.steps or []) if workflow else []

    async def chat(self, user_message: str, from_agent_id: int = 0) -> AsyncGenerator[dict, None]:
        """集群对话入口，按工作流步骤路由"""
        self.history.append({"role": "user", "content": user_message, "agent_id": from_agent_id})

        yield {"type": "cluster_start", "cluster": self.cluster.name}
        yield {"type": "workspace", "path": str(self.workspace) if self.workspace else ""}

        if not self._steps:
            # 无工作流：路由给第一个成员
            if self.members:
                first = list(self.members.values())[0]
                async for event in self._route_to_agent(first.agent_id, user_message):
                    yield event
            else:
                yield {"type": "error", "message": "集群没有成员"}
            return

        # 按工作流步骤执行
        for i, step in enumerate(self._steps):
            self._step_index = i
            step_name = step.get("name", f"步骤{i + 1}")
            step_type = step.get("type", "agent_task")
            target_agent_id = step.get("agent_id", 0)
            step_config = step.get("config", {})

            yield {"type": "step_start", "step": i + 1, "name": step_name, "agent_id": target_agent_id}

            # 执行步骤前钩子
            for hook in (step.get("hooks", []) or []):
                if hook.get("trigger") == "before_step":
                    yield {"type": "hook", "trigger": "before_step", "hook": hook}

            if step_type == "agent_task" and target_agent_id:
                # 路由到指定智能体
                step_message = f"[{step_name}] {user_message}" if i == 0 else user_message
                async for event in self._route_to_agent(target_agent_id, step_message):
                    yield event

            elif step_type == "decision":
                # 决策步骤：让第一个可用智能体判断
                decision_text = f"请判断当前状态并决定下一步：{step_config.get('prompt', '')}"
                if self.members:
                    decider = list(self.members.values())[0]
                    async for event in self._route_to_agent(decider.agent_id, decision_text):
                        yield event

            elif step_type == "broadcast":
                # 广播：所有成员并行处理（串行简化版）
                for m in self.members.values():
                    if m.role != "observer":
                        async for event in self._route_to_agent(m.agent_id, user_message):
                            yield event

            # 执行步骤后钩子
            for hook in (step.get("hooks", []) or []):
                if hook.get("trigger") == "after_step":
                    yield {"type": "hook", "trigger": "after_step", "hook": hook}

        # 工作流完成钩子
        for hook in ((self.workflow.hooks or []) if self.workflow else []):
            if hook.get("trigger") == "on_complete":
                yield {"type": "hook", "trigger": "on_complete", "hook": hook}

        yield {"type": "cluster_done"}

    async def _route_to_agent(self, agent_id: int, message: str) -> AsyncGenerator[dict, None]:
        """路由到指定智能体执行"""
        # 从数据库获取智能体配置
        db = self.db_session_factory() if self.db_session_factory else None
        try:
            from backend.models.agent import Agent
            agent = db.query(Agent).filter(Agent.id == agent_id).first() if db else None
            if not agent:
                yield {"type": "error", "message": f"智能体 #{agent_id} 不存在"}
                return

            member = self.members.get(agent_id)
            role_label = f" [{member.role}]" if member else ""

            yield {"type": "agent_turn", "agent_id": agent_id, "agent_name": agent.name, "role": member.role if member else ""}

            # 创建子引擎（复用 AgentEngine）
            engine = AgentEngine(
                agent_config={
                    "model_id": agent.model_id,
                    "system_prompt": agent.system_prompt,
                    "tools": agent.tools or [],
                    "max_history": agent.max_history,
                    "temperature": agent.temperature,
                    "max_tokens": agent.max_tokens,
                },
                conversation_history=self.history,
                model_pool=self._model_pool,
                registry=self._registry,
                agent_id=agent_id,
                conversation_id=self.conversation_id,
                cluster_id=self.cluster.id,
                db_session_factory=self.db_session_factory,
                uploaded_files=self._uploaded_files,
                search_enabled=self._search_enabled or bool(agent.search_enabled),
            )

            async for event in engine.chat(message):
                yield event
        finally:
            if db:
                db.close()

    def _run_hooks(self, trigger: str, context: dict):
        """执行钩子（简化版，直接 yield）"""
        pass