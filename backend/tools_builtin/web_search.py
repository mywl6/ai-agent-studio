"""网络搜索工具"""
import httpx
from backend.services.tool_registry import registry


@registry.register(
    name="web_search",
    description="使用 DuckDuckGo 搜索引擎进行网络搜索，返回相关结果摘要（标题、描述、相关主题）。适用于获取最新信息、查询知识、查找资料。注意搜索结果来自 DuckDuckGo，可能不如 Google 全面。",
    icon="🔍",
    category="网络",
)
async def web_search(query: str) -> str:
    """网络搜索"""
    url = "https://api.duckduckgo.com/"
    params = {"q": query, "format": "json", "no_html": 1, "skip_disambig": 1}
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url, params=params)
            data = resp.json()

        results = []
        if data.get("AbstractText"):
            results.append(f"摘要：{data['AbstractText']}")
        if data.get("Heading"):
            results.append(f"标题：{data['Heading']}")

        for topic in data.get("RelatedTopics", [])[:5]:
            if isinstance(topic, dict) and "Text" in topic:
                results.append(f"• {topic['Text'][:200]}")

        if not results:
            return f"未找到关于 '{query}' 的结果，建议换一个关键词试试"

        return "\n".join(results)
    except Exception as e:
        return f"搜索出错：{e}"
