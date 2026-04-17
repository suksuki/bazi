"""单元：SSE / chat blob 解析（无网络）。"""
from __future__ import annotations

from v17_rebirth.infrastructure.llm_micro_client import _chunk_text_from_chat_blob, _sse_delta_content


def test_sse_delta_prefers_content_over_reasoning() -> None:
    line = (
        'data: {"choices":[{"delta":{"content":"甲","reasoning_content":"想"}}]}'
    )
    assert _sse_delta_content(line) == "甲"


def test_sse_delta_falls_back_to_reasoning() -> None:
    line = 'data: {"choices":[{"delta":{"reasoning_content":"推理"}}]}'
    assert _sse_delta_content(line) == "推理"


def test_chunk_text_from_message_content() -> None:
    blob = {"choices": [{"message": {"content": "终稿"}}]}
    assert _chunk_text_from_chat_blob(blob) == "终稿"


def test_chunk_text_ollama_response_field() -> None:
    blob = {"response": "hi"}
    assert _chunk_text_from_chat_blob(blob) == "hi"
