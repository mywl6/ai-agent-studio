"""智能体对话引擎：真实流式 + DI + 工作空间 + 文件/搜索支持"""
import json
import os
from pathlib import Path
from typing import AsyncGenerator, Optional, Callable
from backend.services.model_pool import ModelPool
from backend.services.tool_registry import ToolRegistry
from backend.workspace import get_conversation_workspace, get_conversation_files_dir
from backend.models.conversation_file import ConversationFile
from backend.file_processor import encode_image, extract_text, describe_uploaded_files

VISION_KEYWORDS = {"gpt-4o", "gpt-4-v", "gpt-4.1", "claude-3", "claude-4",
                     "gemini-1.5", "gemini-2.0", "gemini-2.5",
                     "qwen-vl", "qwen2-vl", "glm-4v", "step-1v",
                     "deepseek-vision", "mini-cpm", "internvl"}


class AgentEngine:
    def __init__(
        self,
        agent_config: dict,
        conversation_history: list[dict] = None,
        model_pool: ModelPool = None,
        registry: ToolRegistry = None,
        agent_id: int = 0,
        conversation_id: int = 0,
        cluster_id: Optional[int] = None,
        db_session_factory: Optional[Callable] = None,
        max_iterations: int = 10,
        uploaded_files: list[dict] = None,
        search_enabled: bool = False,
    ):
        self.agent = agent_config
        self.history = conversation_history or []
        self.max_history = agent_config.get("max_history", 20)
        self.max_iterations = max_iterations
        self._model_pool = model_pool
        self._registry = registry
        self._agent_id = agent_id
        self._conversation_id = conversation_id
        self._cluster_id = cluster_id
        self._db_session_factory = db_session_factory
        self._uploaded_files = uploaded_files or []
        self._search_enabled = search_enabled

        self.workspace = None
        self.files_dir = None
        if conversation_id:
            self.workspace = get_conversation_workspace(
                agent_id, conversation_id, cluster_id=cluster_id
            )
            self.files_dir = get_conversation_files_dir(
                agent_id, conversation_id, cluster_id=cluster_id
            )

    def _track_file(self, filepath: str):
        if not self._db_session_factory or not self.workspace:
            return
        try:
            fp = Path(filepath)
            if not fp.exists():
                return
            rel = str(fp.resolve().relative_to(self.workspace.resolve()))
            db = self._db_session_factory()
            try:
                existing = db.query(ConversationFile).filter(
                    ConversationFile.conversation_id == self._conversation_id,
                    ConversationFile.filepath == rel,
                ).first()
                if not existing:
                    cf = ConversationFile(
                        conversation_id=self._conversation_id,
                        agent_id=self._agent_id,
                        filename=fp.name,
                        filepath=rel,
                        size=fp.stat().st_size,
                        source="tool",
                    )
                    db.add(cf)
                    db.commit()
            finally:
                db.close()
        except Exception:
            pass

    def _truncate_history(self):
        if len(self.history) > self.max_history * 2:
            self.history = self.history[-(self.max_history * 2):]

    def _has_vision_capability(self) -> bool:
        model_id = self.agent.get("model_id", "")
        model_lower = model_id.lower()
        if any(kw in model_lower for kw in VISION_KEYWORDS):
            return True
        return False

    def _build_messages(self) -> list[dict]:
        system_content = self.agent.get("system_prompt", "")

        if self.workspace:
            ws_hint = (
                f"\n\n[工作空间] 你的工作目录是：{self.workspace}\n"
                f"文件存放目录：{self.files_dir}\n"
                "创建文件时请使用完整路径或相对此目录的路径。"
            )
            system_content += ws_hint

        if self._search_enabled:
            system_content += (
                "\n\n[联网搜索] 你有 web_search 工具可用。"
                "当用户问题涉及实时信息、最新新闻、未知知识时，主动使用 web_search 获取最新信息。"
            )

        messages = [{"role": "system", "content": system_content}]
        messages.extend(self.history)
        return messages

    def _get_tools_desc(self) -> list[dict]:
        tool_names = list(self.agent.get("tools", []))

        if self._search_enabled and "web_search" not in tool_names:
            tool_names.append("web_search")

        enabled = [
            t["name"] for t in self._registry.get_all_meta()
            if t["name"] in tool_names
        ]
        return self._registry.get_tools_for_llm(enabled)

    def _build_user_content(self, user_message: str) -> str | list:
        text = user_message
        has_images = any(
            f.get("mime_type", "").startswith("image/")
            for f in self._uploaded_files
        )
        can_see = self._has_vision_capability()

        if has_images and not can_see:
            text += "\n\n[注意：当前模型不支持视觉识别，无法查看图片内容。仅能获取到文件名。]"

        file_desc = describe_uploaded_files(self._uploaded_files)
        if file_desc:
            text += file_desc

        if not self._uploaded_files or not can_see:
            return text

        image_parts = []
        for f in self._uploaded_files:
            img = encode_image(f.get("raw", b""), f.get("filename", ""))
            if img:
                image_parts.append(img)

        if not image_parts:
            return text

        parts = [{"type": "text", "text": text}]
        parts.extend(image_parts)
        return parts

    async def chat(self, user_message: str) -> AsyncGenerator[dict, None]:
        user_content = self._build_user_content(user_message)
        self.history.append({"role": "user", "content": user_content})

        tools_desc = self._get_tools_desc()
        messages = self._build_messages()
        model_id = self.agent.get("model_id")

        saved_cwd = os.getcwd()
        if self.workspace:
            os.chdir(str(self.workspace))

        try:
            for iteration in range(self.max_iterations):
                try:
                    response = await self._model_pool.chat(
                        model_id=model_id,
                        messages=messages,
                        tools=tools_desc if tools_desc else None,
                        stream=True,
                        temperature=self.agent.get("temperature"),
                        max_tokens=self.agent.get("max_tokens"),
                    )
                except Exception as e:
                    yield {"type": "error", "message": str(e)}
                    return

                collected_content = ""
                tool_calls = []

                async for chunk in response:
                    if not chunk.choices:
                        continue
                    delta = chunk.choices[0].delta

                    if delta.content:
                        collected_content += delta.content
                        yield {"type": "text", "content": delta.content}

                    if delta.tool_calls:
                        for tc in delta.tool_calls:
                            idx = tc.index
                            while len(tool_calls) <= idx:
                                tool_calls.append({"id": "", "function": {"name": "", "arguments": ""}})
                            if tc.id:
                                tool_calls[idx]["id"] = tc.id
                            if tc.function:
                                if tc.function.name:
                                    tool_calls[idx]["function"]["name"] += tc.function.name
                                if tc.function.arguments:
                                    tool_calls[idx]["function"]["arguments"] += tc.function.arguments

                if tool_calls:
                    assistant_msg = {
                        "role": "assistant",
                        "content": collected_content or "",
                        "tool_calls": [
                            {"id": tc["id"], "type": "function",
                             "function": {"name": tc["function"]["name"], "arguments": tc["function"]["arguments"]}}
                            for tc in tool_calls
                        ],
                    }
                    messages.append(assistant_msg)
                    self.history.append(assistant_msg)

                    for tc in tool_calls:
                        tool_name = tc["function"]["name"]
                        try:
                            tool_args = json.loads(tc["function"]["arguments"])
                        except json.JSONDecodeError:
                            tool_args = {}

                        yield {"type": "tool_start", "tool": tool_name, "params": tool_args}

                        result = await self._registry.execute(tool_name, tool_args)

                        self._track_result_files(result)

                        yield {"type": "tool_result", "tool": tool_name, "result": result}

                        tool_msg = {
                            "role": "tool",
                            "tool_call_id": tc["id"],
                            "content": result,
                        }
                        messages.append(tool_msg)
                        self.history.append(tool_msg)

                    self._truncate_history()
                    continue

                if collected_content:
                    self.history.append({"role": "assistant", "content": collected_content})
                    self._truncate_history()

                yield {"type": "done"}
                return

            yield {"type": "error", "message": "工具调用循环超过最大次数"}
        finally:
            os.chdir(saved_cwd)

        yield {"type": "done"}

    def _track_result_files(self, result: str):
        if not self.files_dir or not self.files_dir.exists():
            return
        for f in self.files_dir.iterdir():
            if f.is_file():
                self._track_file(str(f))
        if self.workspace:
            for f in self.workspace.iterdir():
                if f.is_file() and f.parent == self.workspace and f.name != "files":
                    self._track_file(str(f))