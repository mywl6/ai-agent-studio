"""FastAPI 主入口 — 依赖注入 + 模块化"""
import sys
import logging
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys._MEIPASS)
else:
    BASE_DIR = Path(__file__).resolve().parent.parent

sys.path.insert(0, str(BASE_DIR))

from backend.database import init_db, SessionLocal, get_db
from backend.models.provider import Provider
from backend.models.model_provider import ModelProvider
from backend.models.tool_category import ToolCategory
from backend.di import get_model_pool, get_tool_registry
from backend.services.tool_loader import load_builtin_tools, load_custom_tools
from backend.services.mcp_manager import MCPService
from backend.routers import models, agents, tools, categories, chat, settings, clusters, mcp_router, providers

logger = logging.getLogger(__name__)


# ── 启动初始化 ─────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        init_db()
        logger.info("数据库初始化完成")
    except Exception as e:
        logger.error(f"数据库初始化失败：{e}")

    db = SessionLocal()
    try:
        # 加载启用的模型，需要关联 provider 信息
        models_list = db.query(ModelProvider).filter(ModelProvider.enabled == True).all()
        provider_ids = {m.provider_id for m in models_list}
        providers = {p.id: p for p in db.query(Provider).filter(Provider.id.in_(provider_ids)).all()}

        mp = get_model_pool()
        for m in models_list:
            p = providers.get(m.provider_id)
            if p and p.enabled:
                from backend.security import decrypt_api_key
                api_key = decrypt_api_key(p.api_key)
                mp.add_model(m.id, api_key, p.base_url, {
                    "model_id": m.model_id, "max_tokens": m.max_tokens,
                    "temperature": m.temperature,
                    "support_tools": m.support_tools,
                    "support_stream": m.support_stream,
                })
        logger.info(f"模型池加载完成：{len(models_list)} 个模型")

        _seed_default_categories(db)
        logger.info("默认分类已生成")

        load_builtin_tools()
        load_custom_tools()
        logger.info(f"工具加载完成：{len(get_tool_registry().get_all_meta())} 个工具")

        # 自动加载启用的 MCP 服务器
        try:
            mcp_srv = MCPService(db)
            for srv in mcp_srv.repo.list_enabled():
                if srv.tools_auto_discover:
                    mcp_srv.discover_tools(srv.id)
                    logger.info(f"MCP 自动发现：{srv.name}")
        except Exception as e:
            logger.warning(f"MCP 加载异常（可忽略）：{e}")
    except Exception as e:
        logger.error(f"启动初始化异常：{e}")
    finally:
        db.close()

    yield


def _seed_default_categories(db):
    defaults = [
        {"name": "文件操作", "description": "读写文件、目录浏览", "icon": "📁", "sort_order": 1},
        {"name": "网络", "description": "HTTP 请求、搜索", "icon": "🌐", "sort_order": 2},
        {"name": "系统", "description": "命令行、系统管理", "icon": "⚡", "sort_order": 3},
        {"name": "通用", "description": "计算、工具", "icon": "🔧", "sort_order": 4},
        {"name": "MCP", "description": "MCP 协议工具", "icon": "🔌", "sort_order": 5},
        {"name": "集群", "description": "集群协作工具", "icon": "🌐", "sort_order": 6},
    ]
    for cfg in defaults:
        exists = db.query(ToolCategory).filter(ToolCategory.name == cfg["name"]).first()
        if not exists:
            db.add(ToolCategory(**cfg))
    db.commit()


# ── FastAPI 应用 ───────────────────────────────────────────────

app = FastAPI(title="AI Agent 平台", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(providers.router)
app.include_router(models.router)
app.include_router(agents.router)
app.include_router(tools.router)
app.include_router(categories.router)
app.include_router(clusters.router)
app.include_router(mcp_router.router)
app.include_router(chat.router)
app.include_router(settings.router)

frontend_dist = BASE_DIR / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="static")