"""LLM service helpers for chat and streaming endpoints."""
from __future__ import annotations

import json
from typing import Any, AsyncIterator, Dict, List

from app.api.contracts import ChatRequest
from app.api.router_helpers import lang_output_instruction
from app.core.runtime_config import get_runtime_config
from app.llm.client import QwenClient

STOP_WORDS = ["Thinking Process:", "Reasoning:", "思考过程", "推理过程"]
SYSTEM_PROMPT = "你是严谨命理分析助手，必须基于中文术语体系进行推演。"


def build_chat_messages(body: ChatRequest) -> List[Dict[str, str]]:
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        *body.messages,
        {"role": "user", "content": lang_output_instruction(body.lang)},
    ]


def build_llm_client() -> QwenClient:
    cfg = get_runtime_config().get("llm", {})
    return QwenClient(
        base_url=cfg.get("base_url"),
        api_key=cfg.get("api_key"),
        model=cfg.get("model") or None,
    )


async def run_chat_completion(body: ChatRequest) -> Dict[str, str]:
    client = build_llm_client()
    text = await client.chat(
        build_chat_messages(body),
        temperature=body.temperature,
        max_tokens=body.max_tokens,
        stop=STOP_WORDS,
    )
    return {"content": text}


async def stream_chat_events(body: ChatRequest) -> AsyncIterator[str]:
    client = build_llm_client()
    try:
        async for chunk in client.stream_chat(
            build_chat_messages(body),
            temperature=body.temperature,
            max_tokens=body.max_tokens,
            stop=STOP_WORDS,
        ):
            yield f"data: {json.dumps({'content': chunk}, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"
    except Exception as exc:
        yield f"data: {json.dumps({'error': str(exc)}, ensure_ascii=False)}\n\n"
