"""安全模块：API Key 加密、命令白名单、代码沙箱"""
import os
import re
import subprocess
import shlex
from pathlib import Path
from typing import Optional

from backend.config import ENCRYPTION_KEY, ALLOWED_COMMANDS, WHITE_LIST_DIRS, CLUSTERS_DIR

try:
    from cryptography.fernet import Fernet
    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False


# ── API Key 加密 ──────────────────────────────────────────────

def _get_cipher():
    if not HAS_CRYPTO:
        return None
    key = ENCRYPTION_KEY or _get_machine_key()
    if not key:
        return None
    try:
        return Fernet(key)
    except Exception:
        return None


def _get_machine_key() -> bytes:
    """基于机器特征生成稳定密钥"""
    import hashlib
    machine_id = os.environ.get("COMPUTERNAME", "default")
    if not machine_id:
        machine_id = "ai-agent-default-key"
    return base64.urlsafe_b64encode(hashlib.sha256(machine_id.encode()).digest())


import base64


def encrypt_api_key(api_key: str) -> str:
    """加密 API Key"""
    cipher = _get_cipher()
    if not cipher:
        return api_key
    return cipher.encrypt(api_key.encode()).decode()


def decrypt_api_key(encrypted: str) -> str:
    """解密 API Key"""
    cipher = _get_cipher()
    if not cipher:
        return encrypted
    try:
        return cipher.decrypt(encrypted.encode()).decode()
    except Exception:
        return encrypted


# ── 命令白名单 ─────────────────────────────────────────────────

SAFE_COMMANDS = {cmd.lower() for cmd in ALLOWED_COMMANDS}


def is_command_allowed(command: str) -> tuple[bool, str]:
    """检查命令是否在白名单内。返回 (允许?, 拒绝原因)"""
    if not command or not command.strip():
        return False, "命令为空"

    tokens = shlex.split(command)
    if not tokens:
        return False, "无法解析命令"

    cmd_name = os.path.basename(tokens[0]).lower()

    if cmd_name in SAFE_COMMANDS:
        return True, ""

    # 检查是否包含路径分隔符（如 /bin/echo, C:\Windows\system32\net.exe）
    if cmd_name != tokens[0].lower():
        return False, f"禁止使用路径形式执行命令，请直接使用命令名（如 {cmd_name}）"

    return False, f"命令「{tokens[0]}」不在允许列表中"


def run_safe_command(command: str, cwd: Optional[str] = None, timeout: int = 30) -> str:
    """安全执行白名单命令"""
    allowed, reason = is_command_allowed(command)
    if not allowed:
        return f"❌ 安全拒绝：{reason}"

    if cwd:
        _check_path_safety(cwd)

    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=cwd or os.path.expanduser("~"),
        )
        output = result.stdout
        if result.stderr:
            output += f"\n[stderr] {result.stderr}"
        if not output.strip():
            output = "✅ 命令执行完成（无输出）"
        return output[:10000]
    except subprocess.TimeoutExpired:
        return f"❌ 命令执行超时（{timeout}秒限制）"
    except Exception as e:
        return f"❌ 命令执行错误：{e}"


# ── 路径安全 ─────────────────────────────────────────────────

def _get_safe_dirs() -> list[Path]:
    """获取所有安全目录"""
    dirs = [Path(d).resolve() for d in WHITE_LIST_DIRS]
    if CLUSTERS_DIR.exists():
        for cluster_dir in CLUSTERS_DIR.iterdir():
            if cluster_dir.is_dir():
                dirs.append(cluster_dir.resolve())
    return dirs


def _check_path_safety(filepath: str) -> Path:
    """检查路径是否在安全目录内，返回解析后的路径"""
    path = Path(filepath).resolve()
    safe = _get_safe_dirs()
    for sd in safe:
        try:
            path.relative_to(sd)
            return path
        except ValueError:
            continue
    raise PermissionError(f"路径 {filepath} 不在允许的目录范围内")


# ── 代码沙箱 ───────────────────────────────────────────────────

def sandbox_check_code(code: str) -> list[str]:
    """检查 Python 代码中的危险操作，仅拦截高危行为"""
    forbidden_patterns = [
        (r"__import__\s*\(", "禁止使用 __import__"),
        (r"\bexec\s*\(", "禁止使用 exec"),
        (r"\beval\s*\(", "禁止使用 eval"),
    ]
    violations = []
    for pattern, msg in forbidden_patterns:
        if re.search(pattern, code):
            violations.append(msg)
    return violations


def execute_sandboxed(code: str, context: dict = None, timeout: int = 10) -> dict:
    """在受限命名空间中安全执行代码"""
    violations = sandbox_check_code(code)
    if violations:
        return {"ok": False, "error": f"代码包含违规操作：{'；'.join(violations)}"}

    safe_builtins = {
        "abs": abs, "all": all, "any": any, "bool": bool, "bytes": bytes,
        "chr": chr, "dict": dict, "enumerate": enumerate, "filter": filter,
        "float": float, "format": format, "frozenset": frozenset, "hash": hash,
        "hex": hex, "int": int, "len": len, "list": list, "map": map,
        "max": max, "min": min, "oct": oct, "ord": ord, "pow": pow,
        "range": range, "repr": repr, "reversed": reversed, "round": round,
        "set": set, "slice": slice, "sorted": sorted, "str": str,
        "sum": sum, "tuple": tuple, "type": type, "zip": zip,
        "True": True, "False": False, "None": None,
        "print": lambda *a, **kw: None,  # disable print
    }

    namespace = {"__builtins__": safe_builtins}
    if context:
        namespace.update(context)

    try:
        compiled = compile(code, "<sandbox>", "exec")
        exec(compiled, namespace)
        return {"ok": True, "namespace": namespace}
    except Exception as e:
        return {"ok": False, "error": str(e)}


# ── 工作空间（已迁移到 workspace.py） ──
# get_agent_workspace / get_cluster_shared_dir 请从 workspace 导入