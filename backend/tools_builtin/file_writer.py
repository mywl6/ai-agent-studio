"""写入本地文件工具"""
from backend.services.tool_registry import registry
from backend.services.local_ops import write_file


@registry.register(
    name="write_file",
    description="将文本内容写入本地文件。如果文件不存在会自动创建，路径必须位于允许的工作目录内。返回写入结果及字符数。适用于创建和修改本地文件。",
    icon="✏️",
    category="文件操作",
)
def write_file_tool(filepath: str, content: str) -> str:
    """写入本地文件"""
    return write_file(filepath, content)
