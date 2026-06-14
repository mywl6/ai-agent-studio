"""受限 shell 执行工具"""
from backend.services.tool_registry import registry
from backend.services.local_ops import run_command


@registry.register(
    name="run_command",
    description="在本地系统执行 shell 命令，返回命令输出结果。有安全限制：禁止危险命令（rm -rf、format 等），30秒超时。适用于运行脚本、编译代码、启动服务等本地操作。",
    icon="⚡",
    category="系统",
)
def run_command_tool(command: str) -> str:
    """执行 shell 命令"""
    return run_command(command)
