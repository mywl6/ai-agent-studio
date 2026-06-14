"""模型网关：统一多模型调用"""
import time
from typing import Optional, AsyncGenerator
from openai import AsyncOpenAI
from backend.security import decrypt_api_key


class ModelPool:
    """模型池管理器，启动时加载所有启用的模型配置"""

    def __init__(self):
        self._clients: dict[str, AsyncOpenAI] = {}
        self._configs: dict[str, dict] = {}

    def load_models(self, models: list):
        """从数据库加载模型配置，实例化客户端"""
        for m in models:
            api_key = decrypt_api_key(m.api_key)
            self._add_client(m.id, api_key, m.base_url)
            self._configs[m.id] = {
                "model_id": m.model_id,
                "max_tokens": m.max_tokens,
                "temperature": m.temperature,
                "support_tools": m.support_tools,
                "support_stream": m.support_stream,
            }

    def _add_client(self, model_id: str, api_key: str, base_url: str):
        self._clients[model_id] = AsyncOpenAI(api_key=api_key, base_url=base_url)

    def add_model(self, model_id: str, api_key: str, base_url: str, config: dict):
        """运行时添加模型"""
        self._add_client(model_id, api_key, base_url)
        self._configs[model_id] = config

    def remove_model(self, model_id: str):
        self._clients.pop(model_id, None)
        self._configs.pop(model_id, None)

    def get_client(self, model_id: str) -> AsyncOpenAI:
        if model_id not in self._clients:
            raise ValueError(f"模型 {model_id} 不存在或未启用")
        return self._clients[model_id]

    def get_config(self, model_id: str) -> dict:
        return self._configs.get(model_id, {})

    async def test_connection(self, api_key: str, base_url: str, model_id: str) -> dict:
        """测试模型连通性，返回 {ok, latency, error, detail}"""
        client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        start = time.time()
        try:
            resp = await client.chat.completions.create(
                model=model_id,
                messages=[{"role": "user", "content": "hi"}],
                max_tokens=50,
                timeout=15,
            )
            latency = round(time.time() - start, 2)
            choice = resp.choices[0] if resp.choices else None
            if not choice:
                return {"ok": False, "latency": latency, "error": "模型返回空 choices", "detail": str(resp.model_dump())}
            content = choice.message.content or ""
            finish = choice.finish_reason or "unknown"
            if not content.strip():
                if finish == "length":
                    return {"ok": True, "latency": latency, "model": resp.model, "detail": "连接正常（响应被截断）"}
                return {"ok": False, "latency": latency, "error": f"模型返回空内容 (finish_reason={finish})", "detail": f"model={resp.model}, finish_reason={finish}"}
            return {"ok": True, "latency": latency, "model": resp.model, "usage": str(resp.usage) if resp.usage else None}
        except Exception as e:
            return {"ok": False, "latency": round(time.time() - start, 2), "error": str(e)}

    async def chat(
        self,
        model_id: str,
        messages: list[dict],
        tools: Optional[list] = None,
        stream: bool = False,
        temperature: int = None,
        max_tokens: int = None,
    ):
        """统一调用接口"""
        client = self.get_client(model_id)
        config = self.get_config(model_id)
        kwargs = {
            "model": config.get("model_id", model_id),
            "messages": messages,
            "max_tokens": max_tokens or config.get("max_tokens", 4096),
            "temperature": (temperature if temperature is not None else config.get("temperature", 70)) / 100.0,
        }
        if tools and config.get("support_tools"):
            kwargs["tools"] = tools
        if stream:
            kwargs["stream"] = True
        return await client.chat.completions.create(**kwargs)

    async def stream_chat(
        self,
        model_id: str,
        messages: list[dict],
        tools: Optional[list] = None,
    ) -> AsyncGenerator:
        """流式调用，yield 文本片段"""
        resp = await self.chat(model_id, messages, tools=tools, stream=True)
        async for chunk in resp:
            delta = chunk.choices[0].delta if chunk.choices else None
            if delta and delta.content:
                yield delta.content


model_pool = ModelPool()
