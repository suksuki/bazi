from __future__ import annotations

import socket
import json
import sqlite3
from pathlib import Path
from urllib.error import HTTPError
from urllib import request
from typing import Any, Dict, Optional

from fastapi import APIRouter, Header, HTTPException, Query

from v17_rebirth.backend.logic.plugin_discovery import annotate_causal_trace, registry_rows_for_admin
from v17_rebirth.backend.services.plugin_runtime_state import merge_registry_with_runtime
from v17_rebirth.backend.services.verdict_orchestrator import restart_realtime_pipeline
from v17_rebirth.infrastructure.llm_bridge import get_runtime_llm_config, update_runtime_llm_config
from v17_rebirth.backend.infrastructure.evolution_db import evolution_storage
from v17_rebirth.infrastructure.state_backend import get_state_backend
from v17_rebirth.paths import RUNTIME_DIR

router = APIRouter(tags=["v17-admin"])

_DB_STATE_FILE = RUNTIME_DIR / "db_bridge.json"


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
    path = _DB_STATE_FILE
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


def _resolve_runtime_session_id(raw_session_id: str) -> str:
    sid = str(raw_session_id or "").strip()
    if sid and sid != "default":
        return sid
    try:
        with sqlite3.connect(evolution_storage.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                """
                SELECT session_id
                FROM evolution_ledger
                WHERE session_id IS NOT NULL AND session_id != ''
                ORDER BY timestamp DESC
                LIMIT 1
                """
            ).fetchone()
            if row and str(row["session_id"] or "").strip():
                return str(row["session_id"]).strip()
    except Exception:
        pass
    return sid or "default"
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


@router.get("/v17/admin/physics-constants")
async def get_physics_constants(
    v17_origin: Optional[str] = Query(default=None),
    v17_origin_header: Optional[str] = Header(default=None, alias="v17_origin"),
) -> Dict[str, Any]:
    _ensure_get_v17_origin(v17_origin=v17_origin, v17_origin_header=v17_origin_header)
    from v17_rebirth.backend.logic.configs.manager import get_v17_constants

    constants = get_v17_constants()
    return {"ok": True, "constants": constants}


@router.post("/v17/admin/physics-constants")
async def update_physics_constants(payload: Dict[str, Any]) -> Dict[str, Any]:
    _ensure_v17_origin(payload)
    from v17_rebirth.paths import V17_REBIRTH_ROOT

    # 1. 验证新常数（Payload 中应包含 constants 字典）
    new_constants = payload.get("constants")
    if not isinstance(new_constants, dict):
        raise HTTPException(status_code=400, detail="constants must be a dictionary")

    # 2. 持久化至 v17_core_constants.json
    cfg_path = V17_REBIRTH_ROOT / "backend" / "logic" / "configs" / "v17_core_constants.json"
    full_json = {"protocol": "V17_ALPHA_STABLE", "constants": new_constants}
    try:
        cfg_path.write_text(json.dumps(full_json, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to write config: {e}")

    # 3. 强制重启 Narrative Pipeline 以同步缓存（逻辑对齐）
    restart_realtime_pipeline()

    return {"ok": True, "constants": new_constants, "message": "Physics constants updated and pipeline restarted"}


@router.get("/v17/admin/plugin-config/{plugin_id}")
async def get_plugin_config_api(
    plugin_id: str,
    v17_origin: Optional[str] = Query(default=None),
    v17_origin_header: Optional[str] = Header(default=None, alias="v17_origin"),
) -> Dict[str, Any]:
    _ensure_get_v17_origin(v17_origin=v17_origin, v17_origin_header=v17_origin_header)
    from v17_rebirth.backend.logic.configs.manager import get_plugin_config

    config = get_plugin_config(plugin_id)
    return {"ok": True, "config": config}


@router.post("/v17/admin/plugin-config/{plugin_id}")
async def update_plugin_config_api(plugin_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    _ensure_v17_origin(payload)
    from v17_rebirth.paths import V17_REBIRTH_ROOT

    new_config = payload.get("config")
    if not isinstance(new_config, dict):
        raise HTTPException(status_code=400, detail="config must be a dictionary")

    cfg_path = V17_REBIRTH_ROOT / "backend" / "logic" / "configs" / f"{plugin_id}.json"
    try:
        cfg_path.write_text(json.dumps(new_config, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to write plugin config: {e}")

    restart_realtime_pipeline()
    return {"ok": True, "config": new_config, "message": f"Plugin {plugin_id} config updated"}


@router.get("/v17/admin/evolution-logs")
async def get_evolution_logs(
    limit: int = Query(default=50),
    v17_origin: Optional[str] = Query(default=None),
    v17_origin_header: Optional[str] = Header(default=None, alias="v17_origin"),
) -> Dict[str, Any]:
    _ensure_get_v17_origin(v17_origin=v17_origin, v17_origin_header=v17_origin_header)
    logs = evolution_storage.get_recent_evolution(limit=limit)
    return {"ok": True, "logs": logs}


@router.get("/v17/admin/plugin-runtime-status")
async def get_plugin_runtime_status(
    session_id: str = Query(default="default"),
    v17_origin: Optional[str] = Query(default=None),
    v17_origin_header: Optional[str] = Header(default=None, alias="v17_origin"),
) -> Dict[str, Any]:
    _ensure_get_v17_origin(v17_origin=v17_origin, v17_origin_header=v17_origin_header)
    resolved_session_id = _resolve_runtime_session_id(session_id)
    physics = await get_state_backend().get_physics(resolved_session_id)
    meta = physics.get("meta") if isinstance(physics, dict) and isinstance(physics.get("meta"), dict) else {}
    statuses = meta.get("plugin_execution_status") if isinstance(meta.get("plugin_execution_status"), list) else []
    proposals = meta.get("plugin_modifier_proposals") if isinstance(meta.get("plugin_modifier_proposals"), list) else []
    auto_ratios = meta.get("plugin_auto_ratio_totals") if isinstance(meta.get("plugin_auto_ratio_totals"), dict) else {}
    return {
        "ok": True,
        "session_id": resolved_session_id,
        "statuses": statuses,
        "proposal_count": len(proposals),
        "auto_ratio_totals": auto_ratios,
    }


@router.get("/v17/admin/rlhf-feedback")
async def get_rlhf_feedback(
    v17_origin: Optional[str] = Query(default=None),
    v17_origin_header: Optional[str] = Header(default=None, alias="v17_origin"),
) -> Dict[str, Any]:
    _ensure_get_v17_origin(v17_origin=v17_origin, v17_origin_header=v17_origin_header)
    # 暂时重用 evolution_storage 的方法，后续可扩展专用查询
    import sqlite3
    with sqlite3.connect(evolution_storage.db_path) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.execute("SELECT * FROM rlhf_feedback ORDER BY timestamp DESC LIMIT 100")
        rows = [dict(row) for row in cursor.fetchall()]
    return {"ok": True, "feedback": rows}
