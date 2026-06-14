"""模型提供商表"""
from datetime import datetime
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text
from backend.database import Base


class Provider(Base):
    __tablename__ = "providers"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    type = Column(String(50), nullable=False)  # openai / anthropic / deepseek / ollama / aliyun / custom
    api_key = Column(Text, nullable=False)
    base_url = Column(String(500), nullable=False)
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
