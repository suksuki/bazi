from __future__ import annotations

import os
from dataclasses import dataclass
from threading import Lock


_RUNTIME_CFG_LOCK = Lock()
_RUNTIME_CFG: dict[str, str] = {}
_RUNTIME_REVISION = 0


@dataclass
class V17LlmBridge:
    """Only reads connection/model configuration for micro-fusion."""

    base_url: str | None = None
    provider: str | None = None
    username: str | None = None
    password: str | None = None
    api_key: str | None = None
    model: str | None = None

    def resolve(self) -> dict[str, str]:
        with _RUNTIME_CFG_LOCK:
            runtime = dict(_RUNTIME_CFG)
        return {
            "provider": self.provider or runtime.get("provider") or os.getenv("QIAZHI_LLM_PROVIDER", "ollama"),
            "base_url": self.base_url or runtime.get("base_url") or os.getenv("QIAZHI_LLM_BASE_URL", "http://127.0.0.1:11434/v1"),
            "username": self.username or runtime.get("username") or os.getenv("QIAZHI_LLM_USERNAME", ""),
            "password": self.password or runtime.get("password") or os.getenv("QIAZHI_LLM_PASSWORD", ""),
            "api_key": self.api_key or runtime.get("api_key") or os.getenv("QIAZHI_LLM_API_KEY", ""),
            "model": self.model or runtime.get("model") or os.getenv("QIAZHI_LLM_MODEL", "qwen2.5:7b"),
        }


def get_runtime_llm_config() -> dict[str, str]:
    return V17LlmBridge().resolve()


def update_runtime_llm_config(
    *,
    provider: str,
    base_url: str,
    username: str,
    password: str,
    api_key: str,
    model: str,
) -> dict[str, str]:
    global _RUNTIME_REVISION
    clean = {
        "provider": str(provider or "ollama").strip() or "ollama",
        "base_url": str(base_url or "").strip(),
        "username": str(username or "").strip(),
        "password": str(password or "").strip(),
        "api_key": str(api_key or "").strip(),
        "model": str(model or "").strip(),
    }
    with _RUNTIME_CFG_LOCK:
        _RUNTIME_CFG.update(clean)
        _RUNTIME_REVISION += 1
    return {"revision": str(_RUNTIME_REVISION), **V17LlmBridge().resolve()}


def get_runtime_revision() -> int:
    with _RUNTIME_CFG_LOCK:
        return int(_RUNTIME_REVISION)
