"""工具表"""
from datetime import datetime
from sqlalchemy import Column, String, Integer, Text, Boolean, DateTime
from sqlalchemy.types import JSON
from backend.database import Base


class Tool(Base):
    __tablename__ = "tools"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False)
    display_name = Column(String(100))
    description = Column(Text)
    icon = Column(String(10), default="🔧")
    category = Column(String(50), default="通用")
    source = Column(String(20), default="builtin")
    code = Column(Text, default="")
    params_schema = Column(JSON, default=dict)
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
