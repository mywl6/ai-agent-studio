"""系统设置 + 数据备份"""
import shutil
from pathlib import Path
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.config import DB_PATH

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("")
async def get_settings():
    """获取配置"""
    return {"app_name": "AI Agent 平台", "version": "1.0.0"}


@router.get("/export")
async def export_database():
    """导出数据库"""
    if not DB_PATH.exists():
        raise HTTPException(status_code=404, detail="数据库文件不存在")
    return FileResponse(
        path=str(DB_PATH),
        filename="app.db",
        media_type="application/octet-stream",
    )


@router.post("/import")
async def import_database(file: UploadFile = File(...)):
    """导入数据库"""
    if not file.filename.endswith(".db"):
        raise HTTPException(status_code=400, detail="只支持 .db 文件")
    backup = DB_PATH.with_suffix(".db.bak")
    if DB_PATH.exists():
        shutil.copy2(DB_PATH, backup)
    with open(DB_PATH, "wb") as f:
        content = await file.read()
        f.write(content)
    return {"ok": True, "message": "导入成功，请重启应用"}
