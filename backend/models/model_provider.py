"""模型表 — 属于某个提供商"""
from datetime import datetime
from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, UniqueConstraint
from backend.database import Base


class ModelProvider(Base):
    __tablename__ = "model_providers"
    id = Column(String(50), primary_key=True)  # UUID
    provider_id = Column(Integer, ForeignKey("providers.id"), nullable=False)
    name = Column(String(100), nullable=False)
    model_id = Column(String(100), nullable=False)
    max_tokens = Column(Integer, default=4096)
    temperature = Column(Integer, default=70)  # 0-200, 代表 0.0-2.0
    support_tools = Column(Boolean, default=True)
    support_stream = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("provider_id", "model_id", name="uix_provider_model"),
    )
