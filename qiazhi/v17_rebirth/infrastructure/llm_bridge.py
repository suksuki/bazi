from __future__ import annotations

import os
import json
from pathlib import Path
from dataclasses import dataclass
from threading import Lock

from v17_rebirth.paths import RUNTIME_DIR

# V17.18：多态角色引擎 — 叙事织造（主判词）与圣殿裁决（决策收束）
V17_ROLE_WEAVER = "WEAVER"
V17_ROLE_JUDGE = "JUDGE"
V17_ROLES: dict[str, str] = {
    V17_ROLE_WEAVER: "织造官",
    V17_ROLE_JUDGE: "裁决者",
}


_RUNTIME_CFG_LOCK = Lock()
_RUNTIME_CFG: dict[str, str] = {}
_RUNTIME_REVISION = 0
_RUNTIME_CFG_LOADED = False
_LLM_CFG_FILE = RUNTIME_DIR / "llm_node.json"


# 叙事微客户端超时：环境变量可覆盖；运行时 llm_node.json 可再覆盖（秒）
_ENV_HTTP_TIMEOUT = "QIAZHI_V17_LLM_HTTP_TIMEOUT_SEC"
_ENV_FUSE_WAIT = "QIAZHI_V17_LLM_FUSE_WAIT_TIMEOUT_SEC"


def _default_http_timeout_sec() -> str:
    v = str(os.getenv(_ENV_HTTP_TIMEOUT, "15") or "15").strip()
    return v or "15"


def _default_fuse_wait_timeout_sec() -> str:
    v = str(os.getenv(_ENV_FUSE_WAIT, "30") or "30").strip()
    return v or "30"


def _clamp_timeout_sec(raw: str, fallback: str) -> str:
    try:
        x = float(str(raw).strip())
        x = max(1.0, min(600.0, x))
        return str(int(x)) if x == int(x) else str(round(x, 2))
    except (TypeError, ValueError):
        return fallback


def _load_runtime_from_disk() -> None:
    global _RUNTIME_CFG_LOADED
    if _RUNTIME_CFG_LOADED:
        return
    path = _LLM_CFG_FILE
    if path.exists():
        try:
            blob = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(blob, dict):
                _RUNTIME_CFG.update({str(k): str(v) for k, v in blob.items() if v is not None})
        except Exception:
            pass
    _RUNTIME_CFG_LOADED = True


def _save_runtime_to_disk() -> None:
    try:
        _LLM_CFG_FILE.parent.mkdir(parents=True, exist_ok=True)
        _LLM_CFG_FILE.write_text(json.dumps(_RUNTIME_CFG, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass


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
            _load_runtime_from_disk()
            runtime = dict(_RUNTIME_CFG)
        http_fb = _default_http_timeout_sec()
        fuse_fb = _default_fuse_wait_timeout_sec()
        return {
            "provider": self.provider or runtime.get("provider") or os.getenv("QIAZHI_LLM_PROVIDER", "ollama"),
            "base_url": self.base_url or runtime.get("base_url") or os.getenv("QIAZHI_LLM_BASE_URL", "http://127.0.0.1:11434/v1"),
            "username": self.username or runtime.get("username") or os.getenv("QIAZHI_LLM_USERNAME", ""),
            "password": self.password or runtime.get("password") or os.getenv("QIAZHI_LLM_PASSWORD", ""),
            "api_key": self.api_key or runtime.get("api_key") or os.getenv("QIAZHI_LLM_API_KEY", ""),
            "model": self.model or runtime.get("model") or os.getenv("QIAZHI_LLM_MODEL", "qwen2.5:7b"),
            "http_timeout_sec": _clamp_timeout_sec(str(runtime.get("http_timeout_sec") or ""), http_fb),
            "fuse_wait_timeout_sec": _clamp_timeout_sec(str(runtime.get("fuse_wait_timeout_sec") or ""), fuse_fb),
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
    http_timeout_sec: str | None = None,
    fuse_wait_timeout_sec: str | None = None,
) -> dict[str, str]:
    global _RUNTIME_REVISION
    http_fb = _default_http_timeout_sec()
    fuse_fb = _default_fuse_wait_timeout_sec()
    with _RUNTIME_CFG_LOCK:
        _load_runtime_from_disk()
        prev_http = str(_RUNTIME_CFG.get("http_timeout_sec") or "").strip()
        prev_fuse = str(_RUNTIME_CFG.get("fuse_wait_timeout_sec") or "").strip()
    http_val = str(http_timeout_sec).strip() if http_timeout_sec is not None else (prev_http or http_fb)
    fuse_val = str(fuse_wait_timeout_sec).strip() if fuse_wait_timeout_sec is not None else (prev_fuse or fuse_fb)
    clean = {
        "provider": str(provider or "ollama").strip() or "ollama",
        "base_url": str(base_url or "").strip(),
        "username": str(username or "").strip(),
        "password": str(password or "").strip(),
        "api_key": str(api_key or "").strip(),
        "model": str(model or "").strip(),
        "http_timeout_sec": _clamp_timeout_sec(http_val, http_fb),
        "fuse_wait_timeout_sec": _clamp_timeout_sec(fuse_val, fuse_fb),
    }
    with _RUNTIME_CFG_LOCK:
        _load_runtime_from_disk()
        _RUNTIME_CFG.update(clean)
        _RUNTIME_REVISION += 1
        _save_runtime_to_disk()
    return {"revision": str(_RUNTIME_REVISION), **V17LlmBridge().resolve()}


def get_runtime_revision() -> int:
    with _RUNTIME_CFG_LOCK:
        return int(_RUNTIME_REVISION)
