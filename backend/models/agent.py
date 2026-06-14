"""智能体表"""
from datetime import datetime
from sqlalchemy import Column, String, Integer, Text, DateTime
from sqlalchemy.types import JSON
from backend.database import Base


class Agent(Base):
    __tablename__ = "agents"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    avatar = Column(String(10), default="🤖")
    description = Column(Text, default="")
    model_id = Column(String(50), nullable=False)
    system_prompt = Column(Text, default="你是一个有用的 AI 助手。")
    tools = Column(JSON, default=list)
    search_enabled = Column(Integer, default=1)
    temperature = Column(Integer, default=70)
    max_tokens = Column(Integer, default=4096)
    max_history = Column(Integer, default=20)
    created_at = Column(DateTime, default=datetime.utcnow)
