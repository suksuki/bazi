"""判断是否走 Ollama 原生 HTTP（/api/tags、/api/chat），避免在业务代码里散落魔数端口。"""
from __future__ import annotations

import os
from urllib.parse import urlparse


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
