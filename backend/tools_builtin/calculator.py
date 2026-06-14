"""安全数学计算工具"""
from asteval import Interpreter
from backend.services.tool_registry import registry

_asteval = Interpreter(minimal=True)


@registry.register(
    name="calculator",
    description="执行安全的数学计算，支持基本四则运算和数学函数（sin、cos、sqrt、log、abs、pi、e 等）。适用于数值计算、公式求值、数学表达式计算。使用安全解释器执行，不会产生副作用。",
    icon="🔢",
    category="通用",
)
def calculator(expression: str) -> str:
    """安全的数学计算器"""
    try:
        result = _asteval.eval(expression)
        return str(result)
    except Exception as e:
        return f"计算错误：{e}"
