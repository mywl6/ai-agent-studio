"""对话表"""
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from backend.database import Base


class Conversation(Base):
    __tablename__ = "conversations"
    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_id = Column(Integer, nullable=False)
    cluster_id = Column(Integer, ForeignKey("agent_clusters.id"), nullable=True, index=True)
    title = Column(String(200), default="新对话")
    created_at = Column(DateTime, default=datetime.utcnow)
