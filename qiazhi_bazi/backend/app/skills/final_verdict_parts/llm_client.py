from __future__ import annotations

from typing import Any, Dict, List, Tuple

from app.core.runtime_config import get_runtime_config
from app.llm.client import QwenClient


async def run_final_verdict_chat(
    messages: List[Dict[str, str]],
    *,
    temperature: float = 0.2,
    max_tokens: int = 900,
) -> Tuple[str, Any]:
    """终判专用：读取 runtime LLM 配置并发起单次 chat（含 telemetry）。"""
    cfg = get_runtime_config().get("llm", {})
    client = QwenClient(
        base_url=cfg.get("base_url"),
        api_key=cfg.get("api_key"),
        model=cfg.get("model") or None,
    )
    raw, tel = await client.chat_with_telemetry(messages, temperature=temperature, max_tokens=max_tokens, stop=None)
    return raw, tel
