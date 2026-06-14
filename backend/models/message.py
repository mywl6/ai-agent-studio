"""消息表"""
from datetime import datetime
from sqlalchemy import Column, String, Integer, Text, DateTime
from sqlalchemy.types import JSON
from backend.database import Base


class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(Integer, nullable=False)
    role = Column(String(20), nullable=False)
    content = Column(Text, default="")
    tool_call = Column(JSON, default=None)
    model_id = Column(String(50))
    files = Column(JSON, default=None)
    created_at = Column(DateTime, default=datetime.utcnow)
