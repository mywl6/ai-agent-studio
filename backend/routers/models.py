"""模型路由 — 通过 Service + DI"""
import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from backend.database import get_db
from backend.models.provider import Provider
from backend.models.model_provider import ModelProvider
from backend.services.model_pool import ModelPool
from backend.di import get_model_pool
from backend.security import decrypt_api_key

router = APIRouter(prefix="/api/models", tags=["models"])


class ModelConfig(BaseModel):
    provider_id: int
    model_id: str
    name: str
    max_tokens: int = 4096
    temperature: int = 70
    support_tools: bool = True
    support_stream: bool = True


class ModelUpdate(BaseModel):
    name: str | None = None
    max_tokens: int | None = None
    temperature: int | None = None
    support_tools: bool | None = None
    support_stream: bool | None = None
    enabled: bool | None = None


def _build_model_dict(m: ModelProvider, provider: Provider = None) -> dict:
    api_key = decrypt_api_key(provider.api_key) if provider else ""
    masked = api_key[:8] + "..." + api_key[-4:] if len(api_key) > 12 else "****"
    return {
        "id": m.id, "provider_id": m.provider_id,
        "name": m.name, "model_id": m.model_id,
        "max_tokens": m.max_tokens, "temperature": m.temperature,
        "support_tools": m.support_tools,
        "support_stream": m.support_stream,
        "is_default": m.is_default, "enabled": m.enabled,
        "provider_name": provider.name if provider else "",
        "provider_type": provider.type if provider else "",
        "base_url": provider.base_url if provider else "",
        "api_key_masked": masked,
    }


@router.get("")
async def list_models(provider_id: int = None, db: Session = Depends(get_db)):
    query = db.query(ModelProvider)
    if provider_id:
        query = query.filter(ModelProvider.provider_id == provider_id)
    models = query.order_by(ModelProvider.provider_id, ModelProvider.model_id).all()

    # 批量加载 providers
    provider_ids = {m.provider_id for m in models}
    providers = {p.id: p for p in db.query(Provider).filter(Provider.id.in_(provider_ids)).all()}

    return [_build_model_dict(m, providers.get(m.provider_id)) for m in models]


@router.post("")
async def add_model(config: ModelConfig, db: Session = Depends(get_db),
                    mp: ModelPool = Depends(get_model_pool)):
    provider = db.query(Provider).filter(Provider.id == config.provider_id).first()
    if not provider:
        raise HTTPException(400, "提供商不存在")

    # 同一提供商下 model_id 不能重复
    existing = db.query(ModelProvider).filter(
        ModelProvider.provider_id == config.provider_id,
        ModelProvider.model_id == config.model_id,
    ).first()
    if existing:
        raise HTTPException(400, f"提供商下已存在模型「{config.model_id}」")

    record_id = str(uuid.uuid4())

    api_key = decrypt_api_key(provider.api_key)
    model = ModelProvider(
        id=record_id,
        provider_id=config.provider_id,
        name=config.name,
        model_id=config.model_id,
        max_tokens=config.max_tokens,
        temperature=config.temperature,
        support_tools=config.support_tools,
        support_stream=config.support_stream,
    )
    db.add(model)
    db.commit()

    mp.add_model(record_id, api_key, provider.base_url, {
        "model_id": config.model_id, "max_tokens": config.max_tokens,
        "temperature": config.temperature,
        "support_tools": config.support_tools,
        "support_stream": config.support_stream,
    })
    return {"ok": True, "id": record_id}


@router.put("/{model_id}")
async def update_model(model_id: str, config: ModelUpdate,
                       db: Session = Depends(get_db),
                       mp: ModelPool = Depends(get_model_pool)):
    model = db.query(ModelProvider).filter(ModelProvider.id == model_id).first()
    if not model:
        raise HTTPException(404, "模型不存在")

    updates = {k: v for k, v in config.model_dump(exclude_none=True).items() if v != ""}
    for key, value in updates.items():
        setattr(model, key, value)
    db.commit()

    # 刷新模型池
    mp.remove_model(model_id)
    provider = db.query(Provider).filter(Provider.id == model.provider_id).first()
    if provider and model.enabled:
        api_key = decrypt_api_key(provider.api_key)
        mp.add_model(model_id, api_key, provider.base_url, {
            "model_id": model.model_id, "max_tokens": model.max_tokens,
            "temperature": model.temperature,
            "support_tools": model.support_tools,
            "support_stream": model.support_stream,
        })
    return {"ok": True}


@router.post("/{model_id}/test")
async def test_model(model_id: str, db: Session = Depends(get_db),
                     mp: ModelPool = Depends(get_model_pool)):
    model = db.query(ModelProvider).filter(ModelProvider.id == model_id).first()
    if not model:
        raise HTTPException(404, "模型不存在")
    provider = db.query(Provider).filter(Provider.id == model.provider_id).first()
    if not provider:
        raise HTTPException(404, "提供商不存在")
    api_key = decrypt_api_key(provider.api_key)
    return await mp.test_connection(api_key, provider.base_url, model.model_id)


@router.delete("/{model_id}")
async def delete_model(model_id: str, db: Session = Depends(get_db),
                       mp: ModelPool = Depends(get_model_pool)):
    model = db.query(ModelProvider).filter(ModelProvider.id == model_id).first()
    if not model:
        raise HTTPException(404, "模型不存在")
    db.delete(model)
    db.commit()
    mp.remove_model(model_id)
    return {"ok": True}


@router.put("/{model_id}/default")
async def set_default_model(model_id: str, db: Session = Depends(get_db)):
    model = db.query(ModelProvider).filter(ModelProvider.id == model_id).first()
    if not model:
        raise HTTPException(404, "模型不存在")
    db.query(ModelProvider).update({"is_default": False})
    model.is_default = True
    db.commit()
    return {"ok": True}
