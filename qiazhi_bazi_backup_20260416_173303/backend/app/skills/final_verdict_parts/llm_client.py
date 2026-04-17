from __future__ import annotations

from typing import Any, AsyncIterator, Dict, List, Tuple

from app.core.runtime_config import get_runtime_config
from app.llm.client import QwenClient


async def run_final_verdict_chat(
    messages: List[Dict[str, str]],
    *,
    temperature: float = 0.2,
    max_tokens: int = 720,
) -> Tuple[str, Any]:
    """终判专用：读取 runtime LLM 配置并发起单次 chat（含 telemetry）。"""
    cfg = get_runtime_config().get("llm", {})
    if isinstance(cfg, dict):
        try:
            to = float(cfg.get("final_verdict_timeout_s") or 30.0)
        except (TypeError, ValueError):
            to = 30.0
        to = max(12.0, min(180.0, to))
    else:
        to = 30.0
    client = QwenClient(
        base_url=cfg.get("base_url") if isinstance(cfg, dict) else None,
        api_key=cfg.get("api_key") if isinstance(cfg, dict) else None,
        model=cfg.get("model") if isinstance(cfg, dict) else None,
        timeout_s=to,
    )
    raw, tel = await client.chat_with_telemetry(messages, temperature=temperature, max_tokens=max_tokens, stop=None)
    return raw, tel


async def run_final_verdict_chat_stream(
    messages: List[Dict[str, str]],
    *,
    temperature: float = 0.2,
    max_tokens: int = 720,
) -> AsyncIterator[str]:
    """终判流式：OpenAI 兼容路径逐块产出；Ollama 原生非流式时整段 yield 一次。"""
    cfg = get_runtime_config().get("llm", {})
    if isinstance(cfg, dict):
        try:
            to = float(cfg.get("final_verdict_timeout_s") or 30.0)
        except (TypeError, ValueError):
            to = 30.0
        to = max(12.0, min(180.0, to))
    else:
        to = 30.0
    client = QwenClient(
        base_url=cfg.get("base_url") if isinstance(cfg, dict) else None,
        api_key=cfg.get("api_key") if isinstance(cfg, dict) else None,
        model=cfg.get("model") if isinstance(cfg, dict) else None,
        timeout_s=to,
    )
    if client._is_ollama():
        raw, _tel = await run_final_verdict_chat(messages, temperature=temperature, max_tokens=max_tokens)
        if raw:
            yield raw
        return
    async for piece in client.stream_chat(messages, temperature=temperature, max_tokens=max_tokens, stop=None):
        if piece:
            yield piece
