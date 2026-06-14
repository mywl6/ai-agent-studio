"""本地操作层：文件/目录/命令（使用安全模块）"""
from pathlib import Path
from backend.security import _check_path_safety, run_safe_command
from backend.config import WHITE_LIST_DIRS


def read_file(filepath: str) -> str:
    """读取文件内容"""
    try:
        path = _check_path_safety(filepath)
    except PermissionError as e:
        return f"❌ {e}"
    if not path.exists():
        return f"❌ 文件不存在：{filepath}"
    if not path.is_file():
        return f"❌ 不是文件：{filepath}"
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="gbk", errors="replace")


def write_file(filepath: str, content: str) -> str:
    """写入文件"""
    try:
        path = _check_path_safety(filepath)
    except PermissionError as e:
        return f"❌ {e}"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return f"✅ 已写入文件：{filepath}，共 {len(content)} 字符"


def list_directory(dirpath: str) -> str:
    """列出目录内容"""
    try:
        path = _check_path_safety(dirpath)
    except PermissionError as e:
        return f"❌ {e}"
    if not path.exists():
        return f"❌ 目录不存在：{dirpath}"
    if not path.is_dir():
        return f"❌ 不是目录：{dirpath}"
    items = []
    for item in sorted(path.iterdir()):
        prefix = "📁 " if item.is_dir() else "📄 "
        size = f" ({item.stat().st_size} bytes)" if item.is_file() else ""
        items.append(f"{prefix}{item.name}{size}")
    return "\n".join(items) if items else "空目录"


def run_command(command: str) -> str:
    """执行 shell 命令（白名单检查）"""
    return run_safe_command(command)