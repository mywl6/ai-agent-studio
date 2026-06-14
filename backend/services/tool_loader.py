"""工具加载器：动态加载内置/自定义/插件工具"""
import importlib
import importlib.util
import sys
from pathlib import Path
from backend.config import TOOLS_CUSTOM_DIR, PLUGINS_DIR
from backend.services.tool_registry import registry

BUILTIN_TOOL_MODULES = [
    "backend.tools_builtin.calculator",
    "backend.tools_builtin.command_runner",
    "backend.tools_builtin.dir_lister",
    "backend.tools_builtin.file_reader",
    "backend.tools_builtin.file_writer",
    "backend.tools_builtin.http_request",
    "backend.tools_builtin.web_search",
]


def load_builtin_tools():
    """加载内置工具（优先用模块导入，兼容 PyInstaller 打包）"""
    imported = 0
    for mod_name in BUILTIN_TOOL_MODULES:
        try:
            importlib.import_module(mod_name)
            imported += 1
        except Exception as e:
            print(f"导入内置工具 {mod_name} 失败: {e}")

    # 如果模块导入失败（非打包环境），回退到文件扫描
    if imported == 0:
        builtin_dir = Path(__file__).resolve().parent.parent / "tools_builtin"
        if builtin_dir.exists():
            _load_from_dir(builtin_dir)


def load_custom_tools():
    """加载 tools_custom/ 下所有 .py 文件"""
    if getattr(sys, 'frozen', False):
        return
    if TOOLS_CUSTOM_DIR.exists():
        _load_from_dir(TOOLS_CUSTOM_DIR)


def load_single_tool(filepath: str):
    """加载单个工具文件"""
    path = Path(filepath)
    if path.exists() and path.suffix == ".py":
        _load_module(path)


def load_plugin_tools(plugin_dir: str):
    """加载插件目录下的工具"""
    plugin_path = Path(plugin_dir)
    if plugin_path.exists():
        _load_from_dir(plugin_path)


def _load_from_dir(directory: Path):
    """遍历目录加载所有 .py 文件"""
    for py_file in directory.glob("*.py"):
        if py_file.name.startswith("_"):
            continue
        _load_module(py_file)


def _load_module(filepath: Path):
    """动态加载单个模块"""
    module_name = f"tool_{filepath.stem}"
    spec = importlib.util.spec_from_file_location(module_name, str(filepath))
    if spec and spec.loader:
        module = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(module)
        except Exception as e:
            print(f"加载工具 {filepath.name} 失败: {e}")