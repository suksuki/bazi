from __future__ import annotations

import socket
import json
from pathlib import Path
from urllib.error import HTTPError
from urllib import request
from typing import Any, Dict, Optional

from fastapi import APIRouter, Header, HTTPException, Query

from v17_rebirth.backend.logic.plugin_discovery import annotate_causal_trace, registry_rows_for_admin
from v17_rebirth.backend.services.plugin_runtime_state import merge_registry_with_runtime
from v17_rebirth.backend.services.verdict_orchestrator import restart_realtime_pipeline
from v17_rebirth.infrastructure.llm_bridge import get_runtime_llm_config, update_runtime_llm_config
from v17_rebirth.paths import RUNTIME_DIR

router = APIRouter(tags=["v17-admin"])

_DB_STATE_FILE = RUNTIME_DIR / "db_bridge.json"
_DB_FALLBACK_STATE_FILE = Path("/home/hlsystem/bazi/qiazhi/v17_rebirth/.runtime/db_bridge.json")

_DB_BRIDGE_STATE: Dict[str, Any] = {
    "driver": "postgres",
    "host": "127.0.0.1",
    "port": 5432,
    "database": "v17_rebirth",
    "username": "postgres",
    "password": "",
    "sslmode": "prefer",
    "url": "",
    "enabled": False,
}


def _load_db_state() -> None:
    path = _DB_STATE_FILE if _DB_STATE_FILE.exists() else _DB_FALLBACK_STATE_FILE
    if not path.exists():
        return
    try:
        blob = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(blob, dict):
            _DB_BRIDGE_STATE.update(blob)
    except Exception:
        pass


def _save_db_state() -> None:
    try:
        _DB_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        _DB_STATE_FILE.write_text(json.dumps(_DB_BRIDGE_STATE, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass


_load_db_state()


def _ensure_v17_origin(payload: Dict[str, Any]) -> None:
    origin = str(payload.get("v17_origin", "")).strip()
    if origin != "v17_rebirth":
        raise HTTPException(status_code=403, detail="v17_origin validation failed")


def _ensure_get_v17_origin(
    *,
    v17_origin: Optional[str] = Query(default=None),
    v17_origin_header: Optional[str] = Header(default=None, alias="v17_origin"),
) -> None:
    o = str(v17_origin or v17_origin_header or "").strip()
    if o != "v17_rebirth":
        raise HTTPException(status_code=403, detail="v17_origin validation failed")


def _probe_llm(base_url: str) -> Dict[str, Any]:
    for probe_url in (base_url.rstrip("/") + "/models", base_url.rstrip("/").removesuffix("/v1") + "/api/tags"):
        try:
            req = request.Request(probe_url, method="GET")
            with request.urlopen(req, timeout=2.5) as resp:
                code = int(getattr(resp, "status", 200))
            return {"reachable": 200 <= code < 500, "http_status": code, "probe_url": probe_url}
        except Exception:
            continue
    raise RuntimeError("unable to reach ollama/openai-compatible model list endpoint")


def _fetch_llm_models(base_url: str) -> Dict[str, Any]:
    openai_url = base_url.rstrip("/") + "/models"
    native_url = base_url.rstrip("/").removesuffix("/v1") + "/api/tags"
    names: list[str] = []
    code = 0
    used_url = openai_url
    try:
        req = request.Request(openai_url, method="GET")
        with request.urlopen(req, timeout=3.0) as resp:
            code = int(getattr(resp, "status", 200))
            raw = json.loads(resp.read().decode("utf-8"))
        rows = raw.get("data") if isinstance(raw, dict) else []
        if isinstance(rows, list):
            for item in rows:
                if isinstance(item, dict):
                    name = str(item.get("id", "")).strip()
                    if name:
                        names.append(name)
    except Exception:
        req = request.Request(native_url, method="GET")
        with request.urlopen(req, timeout=3.0) as resp:
            code = int(getattr(resp, "status", 200))
            raw = json.loads(resp.read().decode("utf-8"))
        used_url = native_url
        rows = raw.get("models") if isinstance(raw, dict) else []
        if isinstance(rows, list):
            for item in rows:
                if isinstance(item, dict):
                    name = str(item.get("name", "")).strip()
                    if name:
                        names.append(name)
    return {"http_status": code, "models": names, "models_url": used_url}


def _chat_llm(base_url: str, model: str, prompt: str) -> Dict[str, Any]:
    openai_endpoint = base_url.rstrip("/") + "/chat/completions"
    native_endpoint = base_url.rstrip("/").removesuffix("/v1") + "/api/chat"
    body = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2,
        "max_tokens": 120,
    }
    openai_fallback_reasoning = ""
    try:
        payload = json.dumps(body).encode("utf-8")
        req = request.Request(openai_endpoint, data=payload, method="POST")
        req.add_header("Content-Type", "application/json")
        with request.urlopen(req, timeout=10.0) as resp:
            code = int(getattr(resp, "status", 200))
            raw = json.loads(resp.read().decode("utf-8"))
        content = ""
        if isinstance(raw, dict):
            msg = ((((raw.get("choices") or [{}])[0] or {}).get("message") or {}) if isinstance(raw, dict) else {})
            content = str((msg.get("content")) or "").strip()
            if not content:
                openai_fallback_reasoning = str((msg.get("reasoning")) or (msg.get("thinking")) or "").strip()
        if content:
            return {"http_status": code, "reply": content, "endpoint": openai_endpoint}
    except HTTPError:
        pass
    except Exception:
        pass

    native_body = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "think": False,
        "options": {"temperature": 0.2, "num_predict": 160},
    }
    payload = json.dumps(native_body).encode("utf-8")
    req = request.Request(native_endpoint, data=payload, method="POST")
    req.add_header("Content-Type", "application/json")
    with request.urlopen(req, timeout=15.0) as resp:
        code = int(getattr(resp, "status", 200))
        raw = json.loads(resp.read().decode("utf-8"))
    content = ""
    if isinstance(raw, dict):
        msg = raw.get("message") if isinstance(raw.get("message"), dict) else {}
        content = str((msg.get("content")) or "").strip()
        if not content:
            content = str((msg.get("thinking")) or "").strip()
        if not content:
            content = str(raw.get("response") or "").strip()
    if not content and openai_fallback_reasoning:
        content = openai_fallback_reasoning
    return {"http_status": code, "reply": content, "endpoint": native_endpoint}


def _probe_db(host: str, port: int) -> Dict[str, Any]:
    with socket.create_connection((host, int(port)), timeout=2.5):
        return {"reachable": True, "host": host, "port": int(port)}


@router.get("/v17/admin/plugins")
async def list_plugins(
    v17_origin: Optional[str] = Query(default=None),
    v17_origin_header: Optional[str] = Header(default=None, alias="v17_origin"),
) -> Dict[str, Any]:
    _ensure_get_v17_origin(v17_origin=v17_origin, v17_origin_header=v17_origin_header)
    rows = merge_registry_with_runtime(registry_rows_for_admin())
    annotate_causal_trace(rows)
    enriched = [
        {
            **r,
            "power_tier": int(r.get("causal_tier", 0) or 0),
            "execution_order": int(r.get("execution_order", 0) or 0),
        }
        for r in rows
    ]
    return {"ok": True, "plugins": enriched}


@router.get("/v17/admin/llm-node")
async def get_llm_node(
    v17_origin: Optional[str] = Query(default=None),
    v17_origin_header: Optional[str] = Header(default=None, alias="v17_origin"),
) -> Dict[str, Any]:
    _ensure_get_v17_origin(v17_origin=v17_origin, v17_origin_header=v17_origin_header)
    return {"ok": True, "node": get_runtime_llm_config()}


@router.post("/v17/admin/llm-node")
async def update_llm_node(payload: Dict[str, Any]) -> Dict[str, Any]:
    _ensure_v17_origin(payload if isinstance(payload, dict) else {})
    p = payload if isinstance(payload, dict) else {}
    prev = get_runtime_llm_config()

    def _coalesce(key: str, default: str = "") -> str:
        """表单未提交的字段保留上次持久化值，避免仅改 host/model 时清空密钥。"""
        if key in p and p.get(key) is not None:
            return str(p.get(key) or "").strip()
        return str(prev.get(key, default) or "").strip()

    node = update_runtime_llm_config(
        provider=_coalesce("provider", "ollama") or "ollama",
        base_url=_coalesce("base_url"),
        username=_coalesce("username"),
        password=_coalesce("password"),
        api_key=_coalesce("api_key"),
        model=_coalesce("model"),
        http_timeout_sec=_coalesce("http_timeout_sec", ""),
        fuse_wait_timeout_sec=_coalesce("fuse_wait_timeout_sec", ""),
    )
    pipeline_state = restart_realtime_pipeline()
    return {"ok": True, "node": node, **pipeline_state}


@router.post("/v17/admin/llm-node/test")
async def test_llm_node(payload: Dict[str, Any]) -> Dict[str, Any]:
    _ensure_v17_origin(payload if isinstance(payload, dict) else {})
    base_url = str(payload.get("base_url", "")).strip()
    if not base_url:
        raise HTTPException(status_code=400, detail="base_url is required")
    try:
        result = _probe_llm(base_url)
        return {"ok": True, "result": result}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


@router.post("/v17/admin/llm-node/models")
async def list_llm_models(payload: Dict[str, Any]) -> Dict[str, Any]:
    _ensure_v17_origin(payload if isinstance(payload, dict) else {})
    base_url = str(payload.get("base_url", "")).strip()
    if not base_url:
        raise HTTPException(status_code=400, detail="base_url is required")
    try:
        result = _fetch_llm_models(base_url)
        return {"ok": True, "result": result}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


@router.post("/v17/admin/llm-node/chat-test")
async def chat_test_llm(payload: Dict[str, Any]) -> Dict[str, Any]:
    _ensure_v17_origin(payload if isinstance(payload, dict) else {})
    base_url = str(payload.get("base_url", "")).strip()
    model = str(payload.get("model", "")).strip()
    prompt = str(payload.get("prompt", "")).strip() or "请用一句话问候。"
    if not base_url:
        raise HTTPException(status_code=400, detail="base_url is required")
    if not model:
        raise HTTPException(status_code=400, detail="model is required")
    try:
        result = _chat_llm(base_url, model, prompt)
        return {"ok": True, "result": result}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


@router.get("/v17/admin/db-bridge")
async def get_db_bridge(
    v17_origin: Optional[str] = Query(default=None),
    v17_origin_header: Optional[str] = Header(default=None, alias="v17_origin"),
) -> Dict[str, Any]:
    _ensure_get_v17_origin(v17_origin=v17_origin, v17_origin_header=v17_origin_header)
    return {"ok": True, "bridge": dict(_DB_BRIDGE_STATE)}


@router.post("/v17/admin/db-bridge")
async def update_db_bridge(payload: Dict[str, Any]) -> Dict[str, Any]:
    _ensure_v17_origin(payload if isinstance(payload, dict) else {})
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="invalid payload")
    _DB_BRIDGE_STATE.update(
        {
            "driver": str(payload.get("driver", _DB_BRIDGE_STATE["driver"])),
            "host": str(payload.get("host", _DB_BRIDGE_STATE["host"])),
            "port": int(payload.get("port", _DB_BRIDGE_STATE["port"])),
            "database": str(payload.get("database", _DB_BRIDGE_STATE["database"])),
            "username": str(payload.get("username", _DB_BRIDGE_STATE["username"])),
            "password": str(payload.get("password", _DB_BRIDGE_STATE["password"])),
            "sslmode": str(payload.get("sslmode", _DB_BRIDGE_STATE["sslmode"])),
            "url": str(payload.get("url", _DB_BRIDGE_STATE["url"])),
            "enabled": bool(payload.get("enabled", _DB_BRIDGE_STATE["enabled"])),
        }
    )
    _save_db_state()
    return {"ok": True, "bridge": dict(_DB_BRIDGE_STATE)}


@router.post("/v17/admin/db-bridge/test")
async def test_db_bridge(payload: Dict[str, Any]) -> Dict[str, Any]:
    _ensure_v17_origin(payload if isinstance(payload, dict) else {})
    host = str(payload.get("host", "")).strip()
    port = int(payload.get("port", 0) or 0)
    if not host or port <= 0:
        raise HTTPException(status_code=400, detail="host and port are required")
    try:
        result = _probe_db(host, port)
        return {"ok": True, "result": result}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}
