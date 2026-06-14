"""SQLAlchemy 引擎 + SessionLocal + Base"""
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from backend.config import DATABASE_URL, DB_PATH

is_sqlite = DATABASE_URL.startswith("sqlite")
connect_args = {"check_same_thread": False} if is_sqlite else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """创建所有表 + 自动迁移缺失字段"""
    from backend.models import provider, model_provider, agent, tool, tool_category, conversation, conversation_file, message, cluster, mcp_server
    Base.metadata.create_all(bind=engine)

    # 自动迁移：为已存在的表补充缺失列
    _auto_migrate()


def _auto_migrate():
    """检测并补充缺失的列（只增不减，不改变类型）"""
    import logging
    from sqlalchemy import inspect, text
    from backend.models import Conversation

    logger = logging.getLogger(__name__)

    # Conversation 表的迁移
    _add_column(Conversation.__tablename__, "cluster_id", "INTEGER", logger)

    # Message 表的迁移
    _add_column("messages", "files", "JSON", logger)

    # Agent 表的迁移
    _add_column("agents", "search_enabled", "INTEGER DEFAULT 1", logger)

    # model_providers 表的迁移：添加 provider_id 列 + 自动迁移数据
    _add_column("model_providers", "provider_id", "INTEGER", logger)
    _migrate_providers(logger)


def _add_column(table: str, column: str, col_type: str, logger):
    """安全地添加列（如果不存在）"""
    from sqlalchemy import inspect, text
    try:
        inspector = inspect(engine)
        existing = {c["name"] for c in inspector.get_columns(table)}
        if column not in existing:
            sql = f"ALTER TABLE {table} ADD COLUMN {column} {col_type}"
            with engine.begin() as conn:
                conn.execute(text(sql))
            logger.info(f"迁移：表 {table} 添加列 {column} ({col_type})")
    except Exception as e:
        logger.warning(f"迁移 {table}.{column} 跳过：{e}")


def _migrate_providers(logger):
    """自动迁移：从旧的扁平 model_providers 表创建 providers 表并关联"""
    from sqlalchemy import inspect, text
    from backend.models.provider import Provider
    from backend.models.model_provider import ModelProvider

    try:
        inspector = inspect(engine)
        columns = {c["name"] for c in inspector.get_columns("model_providers")}

        # 步骤 1: 如果有旧的 provider 列且没有 provider_id，先迁移数据
        if "provider" in columns and ("provider_id" not in columns or columns.get("provider_id") is None):
            _add_column("model_providers", "provider_id", "INTEGER", logger)

            with engine.begin() as conn:
                # 获取现有 providers
                existing = conn.execute(text("SELECT id, type FROM providers")).fetchall()
                type_to_id = {row[1]: row[0] for row in existing}

                # 按旧 provider 列分组迁移
                rows = conn.execute(text(
                    "SELECT id, provider, api_key, base_url FROM model_providers WHERE provider_id IS NULL OR provider_id = 0"
                )).fetchall()

                provider_data = {}
                for row in rows:
                    model_id, provider_type, api_key, base_url = row
                    if provider_type not in provider_data:
                        provider_data[provider_type] = {"api_key": api_key, "base_url": base_url}

                for ptype, pdata in provider_data.items():
                    if ptype not in type_to_id:
                        name_map = {
                            "openai": "OpenAI", "anthropic": "Anthropic", "deepseek": "DeepSeek",
                            "ollama": "Ollama", "aliyun": "阿里云", "custom": "自定义",
                        }
                        conn.execute(text(
                            "INSERT INTO providers (name, type, api_key, base_url, enabled) VALUES (:name, :type, :api_key, :base_url, 1)"
                        ), {"name": name_map.get(ptype, ptype), "type": ptype,
                            "api_key": pdata["api_key"], "base_url": pdata["base_url"]})
                        type_to_id[ptype] = conn.execute(text("SELECT last_insert_rowid()")).scalar()

                # 更新 model_providers 的 provider_id
                for ptype, pid in type_to_id.items():
                    conn.execute(text(
                        "UPDATE model_providers SET provider_id = :pid WHERE provider = :ptype AND (provider_id IS NULL OR provider_id = 0)"
                    ), {"pid": pid, "ptype": ptype})

            logger.info("提供商数据迁移完成")

        # 步骤 2: 重建 model_providers 表（去掉旧列，添加 UNIQUE 约束）
        _recreate_model_providers_table(logger)

    except Exception as e:
        logger.warning(f"提供商迁移跳过：{e}")


def _recreate_model_providers_table(logger):
    """重建 model_providers 表：去掉旧列，ID 改为 UUID"""
    import uuid as _uuid
    from sqlalchemy import inspect, text

    try:
        inspector = inspect(engine)
        columns = {c["name"] for c in inspector.get_columns("model_providers")}

        # 如果旧列已不存在，说明已经重建过了，但需要检查 ID 格式
        if "provider" not in columns:
            # 检查是否有旧格式的 ID（provider_id-model_id）
            _migrate_ids_to_uuid(logger)
            return

        with engine.begin() as conn:
            # 读取所有旧数据
            rows = conn.execute(text("SELECT * FROM model_providers")).fetchall()
            col_names = [c["name"] for c in inspector.get_columns("model_providers")]

            # 删除旧表
            conn.execute(text("DROP TABLE model_providers"))

            # 创建新表
            conn.execute(text("""
                CREATE TABLE model_providers (
                    id VARCHAR(50) PRIMARY KEY,
                    provider_id INTEGER NOT NULL REFERENCES providers(id),
                    name VARCHAR(100) NOT NULL,
                    model_id VARCHAR(100) NOT NULL,
                    max_tokens INTEGER DEFAULT 4096,
                    temperature INTEGER DEFAULT 70,
                    support_tools BOOLEAN DEFAULT 1,
                    support_stream BOOLEAN DEFAULT 1,
                    is_default BOOLEAN DEFAULT 0,
                    enabled BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP,
                    UNIQUE(provider_id, model_id)
                )
            """))

            # 迁移数据，ID 改为 UUID
            for row in rows:
                row_dict = dict(zip(col_names, row))
                pid = row_dict.get("provider_id", 0)
                mid = row_dict.get("model_id") or row_dict.get("id", "")

                conn.execute(text("""
                    INSERT OR REPLACE INTO model_providers
                    (id, provider_id, name, model_id, max_tokens, temperature,
                     support_tools, support_stream, is_default, enabled, created_at)
                    VALUES (:id, :provider_id, :name, :model_id, :max_tokens, :temperature,
                            :support_tools, :support_stream, :is_default, :enabled, :created_at)
                """), {
                    "id": str(_uuid.uuid4()), "provider_id": pid,
                    "name": row_dict.get("name", mid),
                    "model_id": mid,
                    "max_tokens": row_dict.get("max_tokens", 4096),
                    "temperature": row_dict.get("temperature", 70),
                    "support_tools": row_dict.get("support_tools", 1),
                    "support_stream": row_dict.get("support_stream", 1),
                    "is_default": row_dict.get("is_default", 0),
                    "enabled": row_dict.get("enabled", 1),
                    "created_at": row_dict.get("created_at"),
                })

        logger.info("model_providers 表重建完成（ID 改为 UUID）")
    except Exception as e:
        logger.warning(f"model_providers 表重建跳过：{e}")


def _migrate_ids_to_uuid(logger):
    """将旧的 provider_id-model_id 格式 ID 迁移为 UUID"""
    import uuid as _uuid
    from sqlalchemy import text

    try:
        with engine.begin() as conn:
            rows = conn.execute(text("SELECT id FROM model_providers")).fetchall()
            old_format = [r[0] for r in rows if r[0] and "-" in r[0] and r[0].split("-")[0].isdigit()]
            if not old_format:
                return

            logger.info(f"迁移 {len(old_format)} 条模型 ID 为 UUID 格式...")
            for old_id in old_format:
                new_id = str(_uuid.uuid4())
                conn.execute(text("UPDATE model_providers SET id = :new_id WHERE id = :old_id"),
                             {"new_id": new_id, "old_id": old_id})

            logger.info("模型 ID 迁移完成")
    except Exception as e:
        logger.warning(f"模型 ID 迁移跳过：{e}")
