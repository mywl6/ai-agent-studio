"""集群相关模型：集群、工作流、步骤、钩子、任务"""
from datetime import datetime
from sqlalchemy import Column, String, Integer, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.types import JSON
from backend.database import Base


class AgentCluster(Base):
    """智能体集群"""
    __tablename__ = "agent_clusters"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, index=True)
    description = Column(Text, default="")
    icon = Column(String(10), default="🌐")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ClusterWorkflow(Base):
    """集群工作流定义"""
    __tablename__ = "cluster_workflows"
    id = Column(Integer, primary_key=True, autoincrement=True)
    cluster_id = Column(Integer, ForeignKey("agent_clusters.id"), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, default="")
    steps = Column(JSON, default=list)       # [{order, name, type, agent_id, config, hooks}]
    hooks = Column(JSON, default=list)       # [{trigger, type, config}]
    is_optimized = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ClusterAgentAssignment(Base):
    """集群-智能体关联"""
    __tablename__ = "cluster_agent_assignments"
    id = Column(Integer, primary_key=True, autoincrement=True)
    cluster_id = Column(Integer, ForeignKey("agent_clusters.id"), nullable=False, index=True)
    agent_id = Column(Integer, nullable=False, index=True)
    role = Column(String(50), default="member")           # leader / member / observer
    workspace_enabled = Column(Boolean, default=True)      # 是否启用独立工作空间
    config = Column(JSON, default=dict)                    # 角色配置
    created_at = Column(DateTime, default=datetime.utcnow)


class ClusterTask(Base):
    """集群任务"""
    __tablename__ = "cluster_tasks"
    id = Column(Integer, primary_key=True, autoincrement=True)
    cluster_id = Column(Integer, ForeignKey("agent_clusters.id"), nullable=False, index=True)
    workflow_id = Column(Integer, ForeignKey("cluster_workflows.id"), nullable=True)
    title = Column(String(200), nullable=False)
    status = Column(String(20), default="pending")         # pending/running/completed/failed
    current_step = Column(Integer, default=0)
    total_steps = Column(Integer, default=1)
    assigned_agent_id = Column(Integer, nullable=True)
    input_data = Column(JSON, default=dict)
    output_data = Column(JSON, default=dict)
    error = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)