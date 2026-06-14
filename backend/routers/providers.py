"""提供商路由"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from backend.database import get_db
from backend.models.provider import Provider
from backend.models.model_provider import ModelProvider
from backend.security import encrypt_api_key, decrypt_api_key

router = APIRouter(prefix="/api/providers", tags=["providers"])


class ProviderCreate(BaseModel):
    name: str
    type: str  # openai / anthropic / deepseek / ollama / aliyun / custom
    api_key: str
    base_url: str


class ProviderUpdate(BaseModel):
    name: str | None = None
    api_key: str | None = None
    base_url: str | None = None
    enabled: bool | None = None


@router.get("")
async def list_providers(db: Session = Depends(get_db)):
    providers = db.query(Provider).all()
    result = []
    for p in providers:
        model_count = db.query(ModelProvider).filter(ModelProvider.provider_id == p.id).count()
        result.append({
            "id": p.id, "name": p.name, "type": p.type,
            "base_url": p.base_url, "enabled": p.enabled,
            "model_count": model_count,
            "api_key_masked": p.api_key[:8] + "..." + p.api_key[-4:] if len(p.api_key) > 12 else "****",
        })
    return result


@router.post("")
async def add_provider(config: ProviderCreate, db: Session = Depends(get_db)):
    encrypted_key = encrypt_api_key(config.api_key)
    provider = Provider(
        name=config.name, type=config.type,
        api_key=encrypted_key, base_url=config.base_url,
    )
    db.add(provider)
    db.commit()
    db.refresh(provider)
    return {"ok": True, "id": provider.id}


@router.put("/{provider_id}")
async def update_provider(provider_id: int, config: ProviderUpdate,
                          db: Session = Depends(get_db)):
    provider = db.query(Provider).filter(Provider.id == provider_id).first()
    if not provider:
        raise HTTPException(404, "提供商不存在")
    updates = {k: v for k, v in config.model_dump(exclude_none=True).items() if v != ""}
    if "api_key" in updates:
        updates["api_key"] = encrypt_api_key(updates["api_key"])
    for key, value in updates.items():
        setattr(provider, key, value)
    db.commit()
    return {"ok": True}


@router.delete("/{provider_id}")
async def delete_provider(provider_id: int, db: Session = Depends(get_db)):
    provider = db.query(Provider).filter(Provider.id == provider_id).first()
    if not provider:
        raise HTTPException(404, "提供商不存在")
    # 删除关联的模型
    db.query(ModelProvider).filter(ModelProvider.provider_id == provider_id).delete()
    db.delete(provider)
    db.commit()
    return {"ok": True}


@router.post("/{provider_id}/fetch_models")
async def fetch_models(provider_id: int, db: Session = Depends(get_db)):
    """从提供商 API 获取可用模型列表"""
    provider = db.query(Provider).filter(Provider.id == provider_id).first()
    if not provider:
        raise HTTPException(404, "提供商不存在")

    api_key = decrypt_api_key(provider.api_key)
    models = []

    try:
        if provider.type == "anthropic":
            # Anthropic 没有 models 列表 API，返回预置列表
            models = [
                {"id": "claude-opus-4-20250514", "name": "Claude Opus 4", "context_window": 200000},
                {"id": "claude-sonnet-4-20250514", "name": "Claude Sonnet 4", "context_window": 200000},
                {"id": "claude-3-5-sonnet-20241022", "name": "Claude 3.5 Sonnet", "context_window": 200000},
                {"id": "claude-3-5-haiku-20241022", "name": "Claude 3.5 Haiku", "context_window": 200000},
                {"id": "claude-3-opus-20240229", "name": "Claude 3 Opus", "context_window": 200000},
            ]
        else:
            # OpenAI 兼容接口（OpenAI / DeepSeek / Ollama / 阿里云等）
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=api_key, base_url=provider.base_url)
            resp = await client.models.list()
            for m in resp.data:
                models.append({
                    "id": m.id,
                    "name": m.id,
                    "context_window": getattr(m, "context_length", None),
                })
    except Exception as e:
        raise HTTPException(400, f"获取模型列表失败：{str(e)}")

    return {"models": models}
