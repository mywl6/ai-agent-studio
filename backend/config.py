"""全局配置 - 支持环境变量覆盖"""
import os
import sys
from pathlib import Path

if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys._MEIPASS)
    DATA_DIR = Path(os.path.dirname(sys.executable)) / "data"
else:
    BASE_DIR = Path(__file__).resolve().parent.parent
    DATA_DIR = BASE_DIR / "data"

DATA_DIR.mkdir(parents=True, exist_ok=True)

# 数据库
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DATA_DIR / 'app.db'}")

# 路径
DB_PATH = DATA_DIR / "app.db"
TOOLS_CUSTOM_DIR = BASE_DIR / "tools_custom"
PLUGINS_DIR = BASE_DIR / "plugins"
CLUSTERS_DIR = DATA_DIR / "clusters"
CLUSTERS_DIR.mkdir(parents=True, exist_ok=True)

# 加密（API Key 加密用）
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", "").encode() if os.getenv("ENCRYPTION_KEY") else None

# 模型默认配置
DEFAULT_MODEL_CONFIG = {
    "max_tokens": 4096,
    "support_tools": True,
    "support_stream": True,
}

# 白名单目录（允许文件操作的范围）
WHITE_LIST_DIRS = [
    os.path.expanduser("~"),
    str(BASE_DIR),
    str(TOOLS_CUSTOM_DIR),
    str(DATA_DIR),
]

# 白名单命令（取代黑名单）
ALLOWED_COMMANDS = [
    "echo", "ls", "dir", "pwd", "cat", "type", "head", "tail",
    "grep", "find", "where", "which",
    "python", "python3", "node", "npm", "npx",
    "git", "pip", "pip3",
    "mkdir", "cp", "copy", "mv", "move", "rename",
    "cd", "pushd", "popd",
]

# 前端 URL（开发时指向 vite 开发服务器）
FRONTEND_URL = os.getenv("FRONTEND_URL", "")

# API 版本
API_VERSION = os.getenv("API_VERSION", "v1")