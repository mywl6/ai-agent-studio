"""AI 自动生成工具：API 文档 → Python 代码"""
from backend.services.model_pool import model_pool

GENERATE_PROMPT = """你是一个 Python 工具生成器。根据用户提供的 API 文档或描述，生成一个 Python 工具函数。

要求：
1. 使用 @registry.register(name="工具名", description="描述", icon="🔧", category="API") 装饰器
2. **description 必须详细描述工具的功能、用途和使用场景**，因为 AI 通过 description 决定何时调用此工具
3. 使用 httpx 发送 HTTP 请求
4. 所有参数带类型注解
5. 返回值为字符串
6. 中文 docstring
7. 完善的异常处理
8. 函数名使用 snake_case
9. 只输出 Python 代码，不要其他内容
10. 导入 registry 时必须使用：from backend.services.tool_registry import registry

输入类型：{input_type}
API 文档/描述：
{content}
"""


async def generate_tool_code(input_type: str, content: str, model_id: str = None) -> dict:
    """根据 API 文档生成工具代码"""
    prompt = GENERATE_PROMPT.format(input_type=input_type, content=content)

    if not model_id:
        raise ValueError("无可用模型，请先添加模型配置")

    resp = await model_pool.chat(
        model_id=model_id,
        messages=[{"role": "user", "content": prompt}],
        stream=False,
    )
    code = resp.choices[0].message.content or ""

    # 提取代码块
    if "```python" in code:
        code = code.split("```python")[1].split("```")[0]
    elif "```" in code:
        code = code.split("```")[1].split("```")[0]

    code = code.strip()

    # 尝试从代码中提取工具名
    suggested_name = "custom_tool"
    for line in code.split("\n"):
        if "@registry.register" in line and "name=" in line:
            start = line.index('name="') + 6
            end = line.index('"', start)
            suggested_name = line[start:end]
            break

    return {"code": code, "suggested_name": suggested_name}
