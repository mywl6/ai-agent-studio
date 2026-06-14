"""会话文件追踪"""
from datetime import datetime
from sqlalchemy import Column, String, Integer, BigInteger, DateTime, ForeignKey
from backend.database import Base


class ConversationFile(Base):
    """会话中产生的文件记录"""
    __tablename__ = "conversation_files"
    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False, index=True)
    agent_id = Column(Integer, nullable=False, index=True)
    filename = Column(String(500), nullable=False)
    filepath = Column(String(1000), nullable=False)  # 相对工作空间的路径
    size = Column(BigInteger, default=0)
    mime_type = Column(String(100), default="application/octet-stream")
    source = Column(String(50), default="tool")  # tool / upload
    created_at = Column(DateTime, default=datetime.utcnow)