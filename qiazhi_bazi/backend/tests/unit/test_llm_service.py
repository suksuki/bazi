from __future__ import annotations

import asyncio
import os
from unittest.mock import patch

os.environ.setdefault("DATABASE_URL", "postgresql://tester:tester@127.0.0.1/qiazhi_test")

from app.api.contracts import ChatRequest
from app.services import llm_service


class _FakeClient:
    def __init__(self):
        self.chat_calls = []
        self.stream_calls = []

    async def chat(self, messages, temperature, max_tokens, stop):
        self.chat_calls.append(
            {
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "stop": stop,
            }
        )
        return "结论文本"

    async def stream_chat(self, messages, temperature, max_tokens, stop):
        self.stream_calls.append(
            {
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "stop": stop,
            }
        )
        for chunk in ["甲", "乙"]:
            yield chunk


class _ErrorStreamClient(_FakeClient):
    async def stream_chat(self, messages, temperature, max_tokens, stop):
        raise RuntimeError("stream failed")
        yield  # pragma: no cover


def test_build_chat_messages_appends_language_instruction():
    body = ChatRequest(messages=[{"role": "user", "content": "你好"}], lang="EN")
    messages = llm_service.build_chat_messages(body)
    assert messages[0]["role"] == "system"
    assert messages[-1]["role"] == "user"
    assert "英文输出" in messages[-1]["content"]


def test_run_chat_completion_uses_shared_stop_words():
    fake = _FakeClient()
    body = ChatRequest(messages=[{"role": "user", "content": "你好"}], temperature=0.2, max_tokens=32, lang="ZH")
    with patch.object(llm_service, "build_llm_client", return_value=fake):
        payload = asyncio.run(llm_service.run_chat_completion(body))
    assert payload == {"content": "结论文本"}
    assert fake.chat_calls[0]["stop"] == llm_service.STOP_WORDS


def test_stream_chat_events_emits_sse_chunks_and_done():
    fake = _FakeClient()
    body = ChatRequest(messages=[{"role": "user", "content": "你好"}], lang="ZH")

    async def _collect():
        items = []
        with patch.object(llm_service, "build_llm_client", return_value=fake):
            async for item in llm_service.stream_chat_events(body):
                items.append(item)
        return items

    chunks = asyncio.run(_collect())
    assert chunks[0].startswith("data: {\"content\": \"甲\"}")
    assert chunks[1].startswith("data: {\"content\": \"乙\"}")
    assert chunks[-1] == "data: [DONE]\n\n"


def test_stream_chat_events_wraps_errors():
    body = ChatRequest(messages=[{"role": "user", "content": "你好"}], lang="ZH")

    async def _collect():
        items = []
        with patch.object(llm_service, "build_llm_client", return_value=_ErrorStreamClient()):
            async for item in llm_service.stream_chat_events(body):
                items.append(item)
        return items

    chunks = asyncio.run(_collect())
    assert len(chunks) == 1
    assert "stream failed" in chunks[0]
