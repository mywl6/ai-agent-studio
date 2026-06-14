"""基础 Service / Repository 抽象层"""
from typing import Generic, TypeVar, Type, Optional, List
from sqlalchemy.orm import Session
from backend.database import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """基础仓储 — 封装 ORM 操作"""

    def __init__(self, db: Session, model_cls: Type[ModelType]):
        self.db = db
        self.model_cls = model_cls

    def get_by_id(self, id: int) -> Optional[ModelType]:
        return self.db.query(self.model_cls).filter(self.model_cls.id == id).first()

    def list_all(self, skip: int = 0, limit: int = 100) -> List[ModelType]:
        return self.db.query(self.model_cls).offset(skip).limit(limit).all()

    def add(self, instance: ModelType) -> ModelType:
        self.db.add(instance)
        self.db.commit()
        self.db.refresh(instance)
        return instance

    def delete(self, instance: ModelType):
        self.db.delete(instance)
        self.db.commit()

    def count(self) -> int:
        return self.db.query(self.model_cls).count()


class PaginatedResult:
    """分页结果包装"""

    def __init__(self, items: list, total: int, skip: int, limit: int):
        self.items = items
        self.total = total
        self.skip = skip
        self.limit = limit
        self.has_more = (skip + limit) < total

    def to_dict(self):
        return {
            "items": self.items,
            "total": self.total,
            "skip": self.skip,
            "limit": self.limit,
            "has_more": self.has_more,
        }


class BaseService:
    """基础 Service — 业务逻辑封装"""
    pass