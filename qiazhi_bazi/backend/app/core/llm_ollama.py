"""判断是否走 Ollama 原生 HTTP（/api/tags、/api/chat），避免在业务代码里散落魔数端口。"""
from __future__ import annotations

import json
import os
from typing import Any, Dict, Optional
from urllib.parse import urlparse


def merge_ollama_chat_options(
    *,
    temperature: float,
    num_predict: int,
    request_options: Optional[Dict[str, Any]] = None,
    runtime_options: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """合并 Ollama `/api/chat` 的 `options`（后写覆盖先写）；`temperature` / `num_predict` 始终来自调用方。

    优先级（低到高）：QIAZHI_OLLAMA_FAST_LITE 默认 num_ctx → QIAZHI_OLLAMA_OPTIONS_JSON →
    runtime `llm.ollama_options` → 单次请求 `request_options`。
    """
    opts: Dict[str, Any] = {}
    if (os.getenv("QIAZHI_OLLAMA_FAST_LITE", "") or "").lower() in ("1", "true", "yes"):
        opts.setdefault("num_ctx", 2048)
    raw = (os.getenv("QIAZHI_OLLAMA_OPTIONS_JSON") or "").strip()
    if raw:
        try:
            blob = json.loads(raw)
            if isinstance(blob, dict):
                opts.update({k: v for k, v in blob.items() if v is not None})
        except (json.JSONDecodeError, TypeError):
            pass
    if isinstance(runtime_options, dict):
        opts.update({k: v for k, v in runtime_options.items() if v is not None})
    if isinstance(request_options, dict):
        opts.update({k: v for k, v in request_options.items() if v is not None})
    opts["temperature"] = float(temperature)
    opts["num_predict"] = int(num_predict)
    return opts


def native_ollama_ports() -> frozenset[int]:
    raw = (os.getenv("QIAZHI_OLLAMA_NATIVE_PORTS") or "11434").strip()
    ports: set[int] = set()
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        try:
            ports.add(int(part))
        except ValueError:
            continue
    return frozenset(ports) if ports else frozenset({11434})


def looks_like_native_ollama_base_url(url: str) -> bool:
    s = (url or "").strip()
    if not s:
        return False
    ports = native_ollama_ports()
    try:
        parsed = urlparse(s)
        if parsed.port is not None and parsed.port in ports:
            return True
    except Exception:
        pass
    return any(f":{p}" in s for p in ports)
