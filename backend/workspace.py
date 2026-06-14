"""会话工作空间管理（支持单智能体和集群模式）"""
import os
import mimetypes
from pathlib import Path
from typing import Optional
from backend.config import DATA_DIR, CLUSTERS_DIR

WORKSPACE_ROOT = DATA_DIR / "workspaces"
WORKSPACE_ROOT.mkdir(parents=True, exist_ok=True)


# ── 路径解析 ──

def _agent_dir(agent_id: int) -> Path:
    p = WORKSPACE_ROOT / "agents" / str(agent_id)
    p.mkdir(parents=True, exist_ok=True)
    return p


def _cluster_shared_dir(cluster_id: int) -> Path:
    """集群共享对话空间"""
    p = WORKSPACE_ROOT / "clusters" / str(cluster_id) / "shared"
    p.mkdir(parents=True, exist_ok=True)
    return p


def _cluster_agent_dir(cluster_id: int, agent_id: int) -> Path:
    """集群内智能体私有空间"""
    p = WORKSPACE_ROOT / "clusters" / str(cluster_id) / "agents" / str(agent_id)
    p.mkdir(parents=True, exist_ok=True)
    return p


# ── 对外 API ──

def get_conversation_workspace(agent_id: int, conversation_id: int,
                                 cluster_id: Optional[int] = None) -> Path:
    """获取会话工作空间"""
    if cluster_id:
        # 集群模式：所有成员共享同一会话目录
        p = _cluster_shared_dir(cluster_id) / str(conversation_id)
    else:
        # 单智能体模式
        p = _agent_dir(agent_id) / str(conversation_id)
    p.mkdir(parents=True, exist_ok=True)
    return p


def get_conversation_files_dir(agent_id: int, conversation_id: int,
                                 cluster_id: Optional[int] = None) -> Path:
    """会话文件存放目录"""
    p = get_conversation_workspace(agent_id, conversation_id, cluster_id) / "files"
    p.mkdir(parents=True, exist_ok=True)
    return p


def get_cluster_shared_dir(cluster_id: int) -> Path:
    """集群共享目录（非会话级别）"""
    return _cluster_shared_dir(cluster_id)


def get_agent_cluster_workspace(cluster_id: int, agent_id: int) -> Path:
    """集群中智能体的私有工作空间"""
    return _cluster_agent_dir(cluster_id, agent_id)


def guess_mime(filename: str) -> str:
    mime, _ = mimetypes.guess_type(filename)
    return mime or "application/octet-stream"


def list_workspace_files(agent_id: int, conversation_id: int,
                          cluster_id: Optional[int] = None) -> list[dict]:
    """扫描会话工作空间目录返回文件列表"""
    ws = get_conversation_workspace(agent_id, conversation_id, cluster_id)
    files_dir = ws / "files"
    if not files_dir.exists():
        return []
    result = []
    for f in sorted(files_dir.iterdir()):
        if f.is_file():
            stat = f.stat()
            result.append({
                "filename": f.name,
                "filepath": str(f.relative_to(ws)),
                "size": stat.st_size,
                "mime_type": guess_mime(f.name),
                "created_at": stat.st_mtime,
            })
    return result