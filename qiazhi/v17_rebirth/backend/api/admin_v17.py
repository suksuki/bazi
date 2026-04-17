from __future__ import annotations

import socket
import json
from urllib import request
from typing import Any, Dict

from fastapi import APIRouter, HTTPException

from v17_rebirth.backend.services.verdict_orchestrator import restart_realtime_pipeline
from v17_rebirth.infrastructure.llm_bridge import get_runtime_llm_config, update_runtime_llm_config

router = APIRouter(tags=["v17-admin"])

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


def _ensure_v17_origin(payload: Dict[str, Any]) -> None:
    origin = str(payload.get("v17_origin", "")).strip()
    if origin != "v17_rebirth":
        raise HTTPException(status_code=403, detail="v17_origin validation failed")


def _probe_llm(base_url: str) -> Dict[str, Any]:
    probe_url = base_url.rstrip("/") + "/models"
    req = request.Request(probe_url, method="GET")
    with request.urlopen(req, timeout=2.5) as resp:
        code = int(getattr(resp, "status", 200))
    return {"reachable": 200 <= code < 500, "http_status": code, "probe_url": probe_url}


def _fetch_llm_models(base_url: str) -> Dict[str, Any]:
    models_url = base_url.rstrip("/") + "/models"
    req = request.Request(models_url, method="GET")
    with request.urlopen(req, timeout=3.0) as resp:
        code = int(getattr(resp, "status", 200))
        raw = json.loads(resp.read().decode("utf-8"))
    rows = raw.get("data") if isinstance(raw, dict) else []
    names = []
    if isinstance(rows, list):
        for item in rows:
            if isinstance(item, dict):
                name = str(item.get("id", "")).strip()
                if name:
                    names.append(name)
    return {"http_status": code, "models": names, "models_url": models_url}


def _probe_db(host: str, port: int) -> Dict[str, Any]:
    with socket.create_connection((host, int(port)), timeout=2.5):
        return {"reachable": True, "host": host, "port": int(port)}


@router.get("/v17/admin/llm-node")
async def get_llm_node() -> Dict[str, Any]:
    return {"ok": True, "node": get_runtime_llm_config()}


@router.post("/v17/admin/llm-node")
async def update_llm_node(payload: Dict[str, Any]) -> Dict[str, Any]:
    _ensure_v17_origin(payload if isinstance(payload, dict) else {})
    node = update_runtime_llm_config(
        provider=str(payload.get("provider", "ollama")),
        base_url=str(payload.get("base_url", "")),
        username=str(payload.get("username", "")),
        password=str(payload.get("password", "")),
        api_key=str(payload.get("api_key", "")),
        model=str(payload.get("model", "")),
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


@router.get("/v17/admin/db-bridge")
async def get_db_bridge() -> Dict[str, Any]:
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
