"""读取本地文件工具"""
from backend.services.tool_registry import registry
from backend.services.local_ops import read_file


@registry.register(
    name="read_file",
    description="读取本地文本文件的内容（代码、配置、日志、文档等）。自动检测 UTF-8/GBK 编码。路径必须位于允许的工作目录内。返回文件完整文本内容。",
    icon="📄",
    category="文件操作",
)
def read_file_tool(filepath: str) -> str:
    """读取本地文本文件"""
    return read_file(filepath)
