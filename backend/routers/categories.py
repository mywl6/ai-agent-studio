"""工具分类 CRUD"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from backend.database import get_db
from backend.models.tool_category import ToolCategory
from backend.services.base import BaseRepository, PaginatedResult

router = APIRouter(prefix="/api/categories", tags=["categories"])


class CategoryCreate(BaseModel):
    name: str
    description: str = ""
    icon: str = "📂"
    sort_order: int = 0


class CategoryUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    icon: str | None = None
    sort_order: int | None = None


@router.get("")
async def list_categories(skip: int = Query(0, ge=0), limit: int = Query(100, ge=1),
                           db: Session = Depends(get_db)):
    cats = db.query(ToolCategory).order_by(
        ToolCategory.sort_order, ToolCategory.name
    ).offset(skip).limit(limit).all()
    return [
        {"id": c.id, "name": c.name, "description": c.description,
         "icon": c.icon, "sort_order": c.sort_order}
        for c in cats
    ]


@router.post("")
async def create_category(config: CategoryCreate, db: Session = Depends(get_db)):
    existing = db.query(ToolCategory).filter(ToolCategory.name == config.name).first()
    if existing:
        raise HTTPException(400, f"分类「{config.name}」已存在")
    cat = ToolCategory(**config.model_dump())
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return {"ok": True, "id": cat.id}


@router.put("/{category_id}")
async def update_category(category_id: int, config: CategoryUpdate,
                           db: Session = Depends(get_db)):
    cat = db.query(ToolCategory).filter(ToolCategory.id == category_id).first()
    if not cat:
        raise HTTPException(404, "分类不存在")
    updates = {k: v for k, v in config.model_dump(exclude_none=True).items() if v != ""}
    for k, v in updates.items():
        setattr(cat, k, v)
    db.commit()
    return {"ok": True}


@router.delete("/{category_id}")
async def delete_category(category_id: int, db: Session = Depends(get_db)):
    cat = db.query(ToolCategory).filter(ToolCategory.id == category_id).first()
    if not cat:
        raise HTTPException(404, "分类不存在")
    db.delete(cat)
    db.commit()
    return {"ok": True}