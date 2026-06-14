"""工具分类表"""
from datetime import datetime
from sqlalchemy import Column, String, Integer, Text, DateTime
from backend.database import Base


class ToolCategory(Base):
    __tablename__ = "tool_categories"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(Text, default="")
    icon = Column(String(10), default="📂")
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)