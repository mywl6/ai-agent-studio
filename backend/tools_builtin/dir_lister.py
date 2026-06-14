"""列出目录工具"""
from backend.services.tool_registry import registry
from backend.services.local_ops import list_directory


@registry.register(
    name="list_directory",
    description="列出指定目录下的所有文件和子目录，显示文件大小。适用于浏览项目结构、查找文件。路径必须位于允许的工作目录内。",
    icon="📁",
    category="文件操作",
)
def list_directory_tool(dirpath: str) -> str:
    """列出目录内容"""
    return list_directory(dirpath)
