"""通用 HTTP 请求工具"""
import httpx
from backend.services.tool_registry import registry


@registry.register(
    name="http_request",
    description="发送 HTTP 请求（GET/POST/PUT/DELETE/PATCH），支持自定义请求头、JSON/文本请求体。返回 HTTP 状态码和响应内容（最多3000字符）。适用于调用外部 API 接口、抓取网页内容。",
    icon="🌐",
    category="网络",
)
async def http_request(
    url: str,
    method: str = "GET",
    headers: str = "",
    body: str = "",
) -> str:
    """发送 HTTP 请求"""
    try:
        import json as _json
        parsed_headers = {}
        if headers:
            parsed_headers = _json.loads(headers) if isinstance(headers, str) else headers

        parsed_body = None
        if body:
            try:
                parsed_body = _json.loads(body)
            except _json.JSONDecodeError:
                parsed_body = body

        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            resp = await client.request(
                method=method.upper(),
                url=url,
                headers=parsed_headers,
                content=parsed_body if isinstance(parsed_body, str) else _json.dumps(parsed_body) if parsed_body else None,
            )
            return f"状态码：{resp.status_code}\n响应：{resp.text[:3000]}"
    except Exception as e:
        return f"请求出错：{e}"
