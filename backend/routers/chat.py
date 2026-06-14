"""对话接口 — DI + 真实流式 + 工作空间 + 附件/搜索"""
import json
import os
from pathlib import Path
from fastapi import APIRouter, Depends, Query, HTTPException, UploadFile, File, Form
from fastapi.responses import StreamingResponse, FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from backend.database import get_db, SessionLocal
from backend.models.agent import Agent
from backend.models.conversation import Conversation
from backend.models.conversation_file import ConversationFile
from backend.models.message import Message
from backend.services.agent_engine import AgentEngine
from backend.services.cluster_engine import ClusterChatEngine
from backend.di import get_model_pool, get_tool_registry
from backend.services.model_pool import ModelPool
from backend.services.tool_registry import ToolRegistry
from backend.workspace import get_conversation_workspace, get_conversation_files_dir, guess_mime, list_workspace_files
from backend.file_processor import validate_file, extract_text

router = APIRouter(tags=["chat"])


class ChatRequest(BaseModel):
    agent_id: int
    message: str
    conversation_id: Optional[int] = None
    cluster_id: Optional[int] = None
    files: list[dict] = []
    search_enabled: bool = False


@router.post("/api/chat")
async def chat(
    req: ChatRequest,
    db: Session = Depends(get_db),
    mp: ModelPool = Depends(get_model_pool),
    registry: ToolRegistry = Depends(get_tool_registry),
):
    conv_id = req.conversation_id
    if not conv_id:
        conv = Conversation(
            agent_id=req.agent_id, cluster_id=req.cluster_id,
            title=req.message[:50],
        )
        db.add(conv)
        db.commit()
        db.refresh(conv)
        conv_id = conv.id

    if req.cluster_id:
        return await _handle_cluster_chat(req, conv_id, db, mp, registry)

    agent = db.query(Agent).filter(Agent.id == req.agent_id).first()
    if not agent:
        raise HTTPException(404, "智能体不存在")

    history = _load_history(db, conv_id)
    engine = AgentEngine(
        _agent_config(agent, db), history,
        model_pool=mp, registry=registry,
        agent_id=agent.id, conversation_id=conv_id,
        db_session_factory=SessionLocal,
        uploaded_files=req.files,
        search_enabled=req.search_enabled or bool(agent.search_enabled),
    )

    user_msg = Message(
        conversation_id=conv_id, role="user", content=req.message,
        model_id=agent.model_id,
        files=req.files if req.files else None,
    )
    db.add(user_msg)
    db.commit()

    full_response = ""
    async for event in engine.chat(req.message):
        if event["type"] == "text":
            full_response += event["content"]
        elif event["type"] == "error":
            raise HTTPException(500, event["message"])

    db.add(Message(
        conversation_id=conv_id, role="assistant",
        content=full_response, model_id=agent.model_id,
    ))
    db.commit()
    return {"reply": full_response, "conversation_id": conv_id}


async def _handle_cluster_chat(req, conv_id, db, mp, registry):
    from backend.models.cluster import AgentCluster, ClusterWorkflow, ClusterAgentAssignment
    cluster = db.query(AgentCluster).filter(AgentCluster.id == req.cluster_id).first()
    if not cluster:
        raise HTTPException(404, "集群不存在")
    members = db.query(ClusterAgentAssignment).filter(
        ClusterAgentAssignment.cluster_id == req.cluster_id
    ).all()
    workflows = db.query(ClusterWorkflow).filter(
        ClusterWorkflow.cluster_id == req.cluster_id,
        ClusterWorkflow.is_active == True,
    ).order_by(ClusterWorkflow.created_at.desc()).all()
    workflow = workflows[0] if workflows else None

    user_msg = Message(
        conversation_id=conv_id, role="user", content=req.message,
        model_id="cluster",
        files=req.files if req.files else None,
    )
    db.add(user_msg)
    db.commit()

    engine = ClusterChatEngine(
        cluster=cluster, workflow=workflow, members=members,
        conversation_id=conv_id,
        db_session_factory=SessionLocal,
        model_pool=mp, registry=registry,
        uploaded_files=req.files,
        search_enabled=req.search_enabled,
    )

    full_response = ""
    async for event in engine.chat(req.message, from_agent_id=req.agent_id):
        if event["type"] == "text":
            full_response += event["content"]
        elif event["type"] == "error":
            raise HTTPException(500, event["message"])

    if full_response:
        db.add(Message(
            conversation_id=conv_id, role="assistant",
            content=full_response, model_id="cluster",
        ))
        db.commit()

    return {"reply": full_response, "conversation_id": conv_id, "cluster_id": req.cluster_id}


@router.get("/api/chat/stream")
async def chat_stream(
    agent_id: int = Query(...),
    message: str = Query(...),
    conversation_id: Optional[int] = Query(None),
    cluster_id: Optional[int] = Query(None),
    search_enabled: Optional[bool] = Query(False),
    files: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    mp: ModelPool = Depends(get_model_pool),
    registry: ToolRegistry = Depends(get_tool_registry),
):
    conv_id = conversation_id
    if not conv_id:
        conv = Conversation(
            agent_id=agent_id, cluster_id=cluster_id,
            title=message[:50],
        )
        db.add(conv)
        db.commit()
        db.refresh(conv)
        conv_id = conv.id

    parsed_files = []
    if files:
        try:
            parsed_files = json.loads(files)
        except json.JSONDecodeError:
            pass

    user_msg = Message(
        conversation_id=conv_id, role="user", content=message,
        model_id=str(cluster_id or agent_id),
        files=parsed_files if parsed_files else None,
    )
    db.add(user_msg)
    db.commit()

    async def event_generator():
        full_response = ""

        if cluster_id:
            from backend.models.cluster import AgentCluster, ClusterWorkflow, ClusterAgentAssignment
            cluster = db.query(AgentCluster).filter(AgentCluster.id == cluster_id).first()
            if not cluster:
                yield f"data: {json.dumps({'type': 'error', 'message': '集群不存在'})}\n\n"
                return
            members = db.query(ClusterAgentAssignment).filter(
                ClusterAgentAssignment.cluster_id == cluster_id
            ).all()
            workflows = db.query(ClusterWorkflow).filter(
                ClusterWorkflow.cluster_id == cluster_id,
                ClusterWorkflow.is_active == True,
            ).order_by(ClusterWorkflow.created_at.desc()).all()

            engine = ClusterChatEngine(
                cluster=cluster, workflow=workflows[0] if workflows else None,
                members=members, conversation_id=conv_id,
                db_session_factory=SessionLocal,
                model_pool=mp, registry=registry,
                search_enabled=search_enabled,
            )
            async for event in engine.chat(message, from_agent_id=agent_id):
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
                if event["type"] == "text":
                    full_response += event["content"]
        else:
            agent = db.query(Agent).filter(Agent.id == agent_id).first()
            if not agent:
                yield f"data: {json.dumps({'type': 'error', 'message': '智能体不存在'})}\n\n"
                return
            history = _load_history(db, conv_id)
            engine = AgentEngine(
                _agent_config(agent, db), history,
                model_pool=mp, registry=registry,
                agent_id=agent.id, conversation_id=conv_id,
                db_session_factory=SessionLocal,
                uploaded_files=parsed_files,
                search_enabled=search_enabled or bool(agent.search_enabled),
            )
            async for event in engine.chat(message):
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
                if event["type"] == "text":
                    full_response += event["content"]

        if full_response:
            db.add(Message(
                conversation_id=conv_id, role="assistant",
                content=full_response,
                model_id=str(cluster_id or agent_id),
            ))
            db.commit()

        yield f"data: {json.dumps({'type': 'conversation_id', 'conversation_id': conv_id})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.post("/api/conversations")
async def create_conversation(
    agent_id: int = Form(...),
    cluster_id: Optional[int] = Form(None),
    title: str = Form("新对话"),
    db: Session = Depends(get_db),
):
    conv = Conversation(
        agent_id=agent_id, cluster_id=cluster_id,
        title=title[:200],
    )
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return {"id": conv.id, "title": conv.title, "created_at": str(conv.created_at)}


@router.post("/api/chat/upload")
async def upload_chat_file(
    file: UploadFile = File(...),
    agent_id: int = Form(...),
    conversation_id: int = Form(...),
    db: Session = Depends(get_db),
):
    content = await file.read()
    safe_name = Path(file.filename or "unnamed").name
    err = validate_file(safe_name, content)
    if err:
        raise HTTPException(400, err)

    files_dir = get_conversation_files_dir(agent_id, conversation_id)
    dest = files_dir / safe_name
    dest.write_bytes(content)

    cf = ConversationFile(
        conversation_id=conversation_id, agent_id=agent_id,
        filename=safe_name,
        filepath=str(dest.relative_to(get_conversation_workspace(agent_id, conversation_id))),
        size=len(content), mime_type=guess_mime(safe_name),
        source="upload",
    )
    db.add(cf)
    db.commit()

    text_content = extract_text(content, safe_name)

    return {
        "ok": True,
        "filename": safe_name,
        "size": len(content),
        "mime_type": cf.mime_type,
        "text_content": text_content if len(text_content) < 50000 else text_content[:50000] + "\n...（过长已截断）",
    }


def _agent_config(agent, db: Session = None) -> dict:
    provider_name = ""
    if db:
        from backend.models.model_provider import ModelProvider
        from backend.models.provider import Provider
        mp = db.query(ModelProvider).filter(ModelProvider.id == agent.model_id).first()
        if mp:
            p = db.query(Provider).filter(Provider.id == mp.provider_id).first()
            provider_name = p.name if p else ""
    return {
        "model_id": agent.model_id,
        "provider": provider_name,
        "system_prompt": agent.system_prompt,
        "tools": agent.tools or [],
        "max_history": agent.max_history,
        "temperature": agent.temperature,
        "max_tokens": agent.max_tokens,
        "search_enabled": bool(agent.search_enabled),
    }


def _load_history(db: Session, conv_id: int) -> list[dict]:
    msgs = db.query(Message).filter(
        Message.conversation_id == conv_id
    ).order_by(Message.id).all()
    result = []
    for m in msgs:
        if m.role not in ("user", "assistant"):
            continue
        entry = {"role": m.role, "content": m.content}
        if m.files:
            entry["files"] = m.files
        if m.tool_call:
            entry["tool_calls"] = m.tool_call
        result.append(entry)
    return result


@router.get("/api/conversations")
async def list_conversations(agent_id: int = Query(0),
                               skip: int = Query(0, ge=0),
                               limit: int = Query(50, ge=1, le=200),
                               db: Session = Depends(get_db)):
    query = db.query(Conversation)
    if agent_id:
        query = query.filter(Conversation.agent_id == agent_id)
    convs = query.order_by(Conversation.created_at.desc()).offset(skip).limit(limit).all()
    return [
        {"id": c.id, "title": c.title, "created_at": str(c.created_at)}
        for c in convs
    ]


@router.get("/api/conversations/{conv_id}/messages")
async def get_messages(conv_id: int,
                        skip: int = Query(0, ge=0),
                        limit: int = Query(200, ge=1, le=500),
                        db: Session = Depends(get_db)):
    msgs = db.query(Message).filter(
        Message.conversation_id == conv_id
    ).order_by(Message.id).offset(skip).limit(limit).all()
    return [
        {
            "id": m.id, "role": m.role, "content": m.content,
            "tool_call": m.tool_call, "model_id": m.model_id,
            "files": m.files,
            "created_at": str(m.created_at),
        }
        for m in msgs
    ]


@router.delete("/api/conversations/{conv_id}")
async def delete_conversation(conv_id: int, db: Session = Depends(get_db)):
    conv = db.query(Conversation).filter(Conversation.id == conv_id).first()
    if conv:
        from backend.workspace import get_conversation_workspace
        ws = get_conversation_workspace(conv.agent_id, conv_id, cluster_id=conv.cluster_id)
        if ws.exists():
            import shutil
            shutil.rmtree(str(ws), ignore_errors=True)
    db.query(ConversationFile).filter(ConversationFile.conversation_id == conv_id).delete()
    db.query(Message).filter(Message.conversation_id == conv_id).delete()
    if conv:
        db.delete(conv)
    db.commit()
    return {"ok": True}


# ── 工作空间文件 ─────────────────────────────────────────────

@router.get("/api/conversations/{conv_id}/files")
async def list_conversation_files(conv_id: int, agent_id: int = Query(0),
                                   db: Session = Depends(get_db)):
    conv = db.query(Conversation).filter(Conversation.id == conv_id).first()
    if not conv:
        raise HTTPException(404, "会话不存在")
    aid = agent_id or conv.agent_id

    records = {
        r.filename: {
            "id": r.id, "filename": r.filename, "size": r.size,
            "mime_type": r.mime_type, "source": r.source,
            "created_at": str(r.created_at),
        }
        for r in db.query(ConversationFile).filter(
            ConversationFile.conversation_id == conv_id
        ).all()
    }

    dir_files = list_workspace_files(aid, conv_id)
    merged = {}
    for f in dir_files:
        record = records.get(f["filename"], {})
        merged[f["filename"]] = {
            "filename": f["filename"],
            "filepath": f["filepath"],
            "size": f["size"],
            "mime_type": f["mime_type"],
            "source": record.get("source", "unknown"),
            "tracked": f["filename"] in records,
            "created_at": record.get("created_at", ""),
        }

    return sorted(merged.values(), key=lambda x: x["filename"])


@router.get("/api/conversations/{conv_id}/files/{filename:path}")
async def get_conversation_file(conv_id: int, filename: str,
                                 agent_id: int = Query(0),
                                 db: Session = Depends(get_db)):
    conv = db.query(Conversation).filter(Conversation.id == conv_id).first()
    if not conv:
        raise HTTPException(404, "会话不存在")
    aid = agent_id or conv.agent_id
    ws = get_conversation_workspace(aid, conv_id)
    candidates = [
        (ws / filename).resolve(),
        (ws / "files" / filename).resolve(),
    ]
    resolved = None
    for fp in candidates:
        try:
            fp.relative_to(ws.resolve())
            if fp.exists() and fp.is_file():
                resolved = fp
                break
        except ValueError:
            continue
    if not resolved:
        raise HTTPException(404, "文件不存在")
    return FileResponse(path=str(resolved), filename=resolved.name)


@router.post("/api/conversations/{conv_id}/files")
async def upload_conversation_file(conv_id: int, agent_id: int = Query(0),
                                    file: UploadFile = File(...),
                                    db: Session = Depends(get_db)):
    conv = db.query(Conversation).filter(Conversation.id == conv_id).first()
    if not conv:
        raise HTTPException(404, "会话不存在")
    aid = agent_id or conv.agent_id
    files_dir = get_conversation_files_dir(aid, conv_id)

    safe_name = Path(file.filename or "unnamed").name
    dest = files_dir / safe_name
    content = await file.read()
    dest.write_bytes(content)

    cf = ConversationFile(
        conversation_id=conv_id, agent_id=aid,
        filename=safe_name,
        filepath=str(dest.relative_to(get_conversation_workspace(aid, conv_id))),
        size=len(content), mime_type=guess_mime(safe_name),
        source="upload",
    )
    db.add(cf)
    db.commit()

    return {
        "ok": True, "filename": safe_name,
        "size": len(content), "mime_type": cf.mime_type,
    }