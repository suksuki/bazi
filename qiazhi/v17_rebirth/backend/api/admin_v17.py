from __future__ import annotations

import asyncio
import socket
import json
import sqlite3
import time
from pathlib import Path
from urllib.error import HTTPError
from urllib import request
from typing import Any, Dict, Optional

from fastapi import APIRouter, Header, HTTPException, Query

from v17_rebirth.backend.logic.plugin_discovery import annotate_causal_trace, registry_rows_for_admin
from v17_rebirth.backend.services.plugin_runtime_state import merge_registry_with_runtime
from v17_rebirth.backend.services.verdict_orchestrator import restart_realtime_pipeline
from v17_rebirth.backend.services.conflict_resolution_service import apply_conflict_resolution
from v17_rebirth.backend.services.knowledge_store import build_knowledge_snapshot
from v17_rebirth.backend.services.arbiter_router import route_conflicts
from v17_rebirth.backend.services.llm_conflict_arbiter import (
    apply_llm_conflict_results,
    build_conflict_bundles,
    build_llm_conflict_prompt,
    parse_llm_conflict_reply,
)
from v17_rebirth.infrastructure.llm_bridge import get_runtime_llm_config, update_runtime_llm_config
from v17_rebirth.backend.infrastructure.evolution_db import evolution_storage
from v17_rebirth.infrastructure.state_backend import get_state_backend
from v17_rebirth.paths import RUNTIME_DIR
from v17_rebirth.testing.learning_campaign import (
    LearningCampaignConfig,
    render_learning_campaign_markdown,
    run_learning_campaign,
)

router = APIRouter(tags=["v17-admin"])

_DB_STATE_FILE = RUNTIME_DIR / "db_bridge.json"
_LEARNING_REPORT_JSON_FILE = RUNTIME_DIR / "learning_campaign_latest.json"
_LEARNING_REPORT_MD_FILE = RUNTIME_DIR / "learning_campaign_latest.md"


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


_LEARNING_CAMPAIGN_TASK: Optional[asyncio.Task] = None
_LEARNING_CAMPAIGN_PAUSE_REQUESTED = False
_LEARNING_CAMPAIGN_STATE: Dict[str, Any] = {
    "protocol": "v17.admin.learning_campaign_runtime.v1",
    "status": "idle",
    "progress_percent": 0,
    "current_step": "idle",
    "current_step_label": "等待启动",
    "estimated_remaining_seconds": 0,
    "started_at": "",
    "completed_at": "",
    "message": "等待启动自动学习 Campaign。",
    "config": {
        "max_minutes": 180,
        "max_extended_cases": None,
        "request_llm_review": False,
    },
    "latest_report": {},
    "latest_report_markdown": "",
}


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


def _now_label() -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S")


def _learning_campaign_status_payload() -> Dict[str, Any]:
    return {
        **_LEARNING_CAMPAIGN_STATE,
        "running": _LEARNING_CAMPAIGN_STATE.get("status") == "running",
        "pause_requested": bool(_LEARNING_CAMPAIGN_PAUSE_REQUESTED),
    }


def _learning_campaign_config_from_payload(payload: Dict[str, Any]) -> LearningCampaignConfig:
    raw_minutes = payload.get("max_minutes", payload.get("max_duration_minutes", 180))
    try:
        max_minutes = int(raw_minutes)
    except (TypeError, ValueError):
        max_minutes = 180
    max_minutes = max(1, min(180, max_minutes))

    raw_max_cases = payload.get("max_extended_cases")
    max_cases: int | None
    try:
        max_cases = int(raw_max_cases) if raw_max_cases not in {None, ""} else None
    except (TypeError, ValueError):
        max_cases = None
    if max_cases is not None:
        max_cases = max(1, min(128, max_cases))

    return LearningCampaignConfig(
        max_duration_seconds=max_minutes * 60,
        include_extended_synthetic=bool(payload.get("include_extended_synthetic", True)),
        include_practitioner_benchmarks=bool(payload.get("include_practitioner_benchmarks", True)),
        include_auto_learning_loop=bool(payload.get("include_auto_learning_loop", True)),
        request_llm_review=bool(payload.get("request_llm_review", False)),
        max_extended_cases=max_cases,
    )


def _set_learning_progress(row: Dict[str, Any]) -> None:
    _LEARNING_CAMPAIGN_STATE.update(
        {
            "status": "running",
            "current_step": str(row.get("step_key") or "running"),
            "current_step_label": str(row.get("step_label") or "运行中"),
            "progress_percent": int(row.get("progress_percent") or 0),
            "estimated_remaining_seconds": float(row.get("estimated_remaining_seconds") or 0.0),
            "message": f"{row.get('step_label') or '运行中'} · {int(row.get('progress_percent') or 0)}%",
        }
    )


def _save_learning_report(report: Dict[str, Any], markdown: str) -> None:
    try:
        _LEARNING_REPORT_JSON_FILE.parent.mkdir(parents=True, exist_ok=True)
        _LEARNING_REPORT_JSON_FILE.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        _LEARNING_REPORT_MD_FILE.write_text(markdown, encoding="utf-8")
    except Exception:
        pass


async def _run_learning_campaign_background(config: LearningCampaignConfig) -> None:
    global _LEARNING_CAMPAIGN_PAUSE_REQUESTED
    try:
        report = await asyncio.to_thread(
            run_learning_campaign,
            config,
            progress_callback=_set_learning_progress,
            should_stop=lambda: bool(_LEARNING_CAMPAIGN_PAUSE_REQUESTED),
        )
        markdown = render_learning_campaign_markdown(report)
        _save_learning_report(report, markdown)
        status = "paused" if report.get("interrupted") else "completed"
        _LEARNING_CAMPAIGN_STATE.update(
            {
                "status": status,
                "progress_percent": 100 if status == "completed" else int(_LEARNING_CAMPAIGN_STATE.get("progress_percent") or 0),
                "current_step": "paused" if status == "paused" else "completed",
                "current_step_label": "已暂停" if status == "paused" else "完成",
                "estimated_remaining_seconds": 0,
                "completed_at": _now_label(),
                "message": "学习 Campaign 已暂停，报告保留当前阶段结果。" if status == "paused" else "学习 Campaign 已完成。",
                "latest_report": report,
                "latest_report_markdown": markdown,
            }
        )
    except Exception as exc:
        _LEARNING_CAMPAIGN_STATE.update(
            {
                "status": "failed",
                "current_step": "failed",
                "current_step_label": "失败",
                "estimated_remaining_seconds": 0,
                "completed_at": _now_label(),
                "message": f"学习 Campaign 失败：{type(exc).__name__}: {exc}",
            }
        )
    finally:
        _LEARNING_CAMPAIGN_PAUSE_REQUESTED = False


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


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _to_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _llm_conflict_feedback_quality(
    *,
    resolved_by: str,
    resolution_type: str,
    confidence: float,
    conflict_score: float,
) -> float:
    # 将LLM裁决残差转为 [-1, 1] 质量信号，后续用于冲突路由学习。
    quality = (_to_float(confidence) - 0.5) * 1.2
    quality += 0.15 if str(resolved_by or "").strip().lower() == "system" else -0.05
    if str(resolution_type or "").strip() in {"reject", "context_only"}:
        quality -= 0.15
    elif str(resolution_type or "").strip() == "escalate_user":
        quality -= 0.35
    quality += 0.25 * _clamp(_to_float(conflict_score), 0.0, 1.0)
    return _clamp(quality, -1.0, 1.0)


def _manual_conflict_feedback_quality(*, resolved_by: str, conflict_score: float) -> float:
    # 手动裁决质量信号：默认有正反馈，但给低分冲突留一定惩罚空间。
    arbiter_bias = {
        "system": 0.12,
        "llm": 0.0,
        "user": 0.06,
    }.get(str(resolved_by or "").strip().lower(), 0.0)
    quality = -0.1 + 0.65 * _clamp(_to_float(conflict_score), 0.0, 1.0) + arbiter_bias
    return _clamp(quality, -1.0, 1.0)


def _find_conflict_row(conflicts: list[dict[str, Any]], conflict_id: str) -> dict[str, Any]:
    target = str(conflict_id or "").strip()
    for row in conflicts:
        if str(row.get("conflict_id") or "").strip() == target:
            return dict(row)
    return {}


def _find_resolution_row(rows: list[dict[str, Any]], conflict_id: str) -> dict[str, Any]:
    target = str(conflict_id or "").strip()
    for row in rows:
        if str(row.get("conflict_id") or "").strip() == target:
            return dict(row)
    return {}


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
    claims = meta.get("plugin_claims") if isinstance(meta.get("plugin_claims"), list) else []
    conflicts = meta.get("plugin_conflicts") if isinstance(meta.get("plugin_conflicts"), list) else []
    conflict_resolutions = (
        meta.get("plugin_conflict_resolutions")
        if isinstance(meta.get("plugin_conflict_resolutions"), list)
        else []
    )
    knowledge_snapshot = meta.get("knowledge_snapshot") if isinstance(meta.get("knowledge_snapshot"), dict) else {}
    brain_action_queue = meta.get("brain_action_queue") if isinstance(meta.get("brain_action_queue"), list) else []
    auto_ratios = meta.get("plugin_auto_ratio_totals") if isinstance(meta.get("plugin_auto_ratio_totals"), dict) else {}
    core_engine_authority = meta.get("god_ring_authority") if isinstance(meta.get("god_ring_authority"), dict) else {}
    ten_gods_decomposition_l0 = (
        physics.get("ten_gods_decomposition_l0")
        if isinstance(physics, dict) and isinstance(physics.get("ten_gods_decomposition_l0"), dict)
        else {}
    )
    energy_meta = physics.get("energy_meta") if isinstance(physics, dict) and isinstance(physics.get("energy_meta"), dict) else {}
    relation_formation_summary = (
        energy_meta.get("relation_formation_summary")
        if isinstance(energy_meta.get("relation_formation_summary"), list)
        else []
    )
    relation_dynamics_summary = (
        energy_meta.get("relation_dynamics_summary")
        if isinstance(energy_meta.get("relation_dynamics_summary"), list)
        else []
    )
    climate_field = (
        energy_meta.get("climate_field")
        if isinstance(energy_meta.get("climate_field"), dict)
        else {}
    )
    climate_modifier_layer = (
        energy_meta.get("climate_modifier_layer")
        if isinstance(energy_meta.get("climate_modifier_layer"), dict)
        else {}
    )
    climate_theme = meta.get("climate_theme") if isinstance(meta.get("climate_theme"), dict) else {}
    xiangfa_theme = meta.get("xiangfa_theme") if isinstance(meta.get("xiangfa_theme"), dict) else {}
    recompute_contributions = (
        meta.get("plugin_recompute_contributions")
        if isinstance(meta.get("plugin_recompute_contributions"), list)
        else []
    )
    return {
        "ok": True,
        "session_id": resolved_session_id,
        "statuses": statuses,
        "proposal_count": len(proposals),
        "claims": claims,
        "conflicts": conflicts,
        "conflict_resolutions": conflict_resolutions,
        "knowledge_snapshot": knowledge_snapshot,
        "brain_action_queue": brain_action_queue,
        "auto_ratio_totals": auto_ratios,
        "core_engine_authority": core_engine_authority,
        "ten_gods_decomposition_l0": ten_gods_decomposition_l0,
        "relation_formation_summary": relation_formation_summary,
        "relation_dynamics_summary": relation_dynamics_summary,
        "climate_field": climate_field,
        "climate_modifier_layer": climate_modifier_layer,
        "climate_theme": climate_theme,
        "xiangfa_theme": xiangfa_theme,
        "recompute_contributions": recompute_contributions,
    }


@router.post("/v17/admin/conflict-resolve")
async def resolve_plugin_conflict(payload: Dict[str, Any]) -> Dict[str, Any]:
    _ensure_v17_origin(payload if isinstance(payload, dict) else {})
    session_id = str(payload.get("session_id", "")).strip() or "default"
    conflict_id = str(payload.get("conflict_id", "")).strip()
    arbiter = str(payload.get("arbiter", "system")).strip().lower() or "system"
    if arbiter not in {"system", "llm", "user"}:
        arbiter = "system"
    raw_conflict_ids = payload.get("conflict_ids", [])
    conflict_ids: list[str] = []
    if isinstance(raw_conflict_ids, (list, tuple)):
        for item in raw_conflict_ids:
            cid = str(item or "").strip()
            if cid and cid not in conflict_ids:
                conflict_ids.append(cid)
    if conflict_id and conflict_id not in conflict_ids:
        conflict_ids.insert(0, conflict_id)
    if not conflict_ids:
        raise HTTPException(status_code=400, detail="conflict_ids or conflict_id is required")
    normalized_conflict_id = conflict_ids[0]

    backend = get_state_backend()
    physics = await backend.get_physics(session_id)
    if not isinstance(physics, dict):
        raise HTTPException(status_code=404, detail="physics not found")
    meta = physics.get("meta") if isinstance(physics.get("meta"), dict) else {}
    if arbiter == "llm":
        bundle = build_conflict_bundles(meta=meta, conflict_ids=conflict_ids)
        if not bundle.get("conflicts"):
            raise HTTPException(status_code=404, detail="no valid conflicts in this request")
        cfg = get_runtime_llm_config()
        base_url = str(cfg.get("base_url") or "").strip()
        model = str(cfg.get("model") or "").strip()
        if not base_url or not model:
            raise HTTPException(status_code=400, detail="llm config incomplete")
        prompt = build_llm_conflict_prompt(bundle=bundle)
        try:
            llm_result = _chat_llm(base_url, model, prompt)
        except Exception as exc:
            raise HTTPException(status_code=502, detail=f"llm conflict arbitration failed: {exc}")
        reply = str(llm_result.get("reply") or "").strip()
        parsed = parse_llm_conflict_reply(reply=reply, bundle=bundle)
        updated_meta = apply_llm_conflict_results(
            meta=meta,
            conflict_ids=conflict_ids,
            bundle=bundle,
            reply=reply,
            parsed=parsed,
        )
        feedback_rows = evolution_storage.get_feedback(session_id=session_id, action="conflict_resolution", limit=200)
        conflict_rows = updated_meta.get("plugin_conflicts") if isinstance(updated_meta.get("plugin_conflicts"), list) else []
        resolution_rows = (
            updated_meta.get("plugin_conflict_resolutions")
            if isinstance(updated_meta.get("plugin_conflict_resolutions"), list)
            else []
        )
        for item_id in conflict_ids:
            row_status = "llm"
            conflict_row = _find_conflict_row(conflict_rows, item_id)
            resolution_row = _find_resolution_row(resolution_rows, item_id)
            resolved_by = str(resolution_row.get("resolved_by") or "llm").strip().lower()
            if resolved_by in {"system", "llm", "user"}:
                row_status = resolved_by
            resolution_type = str(resolution_row.get("llm_resolution_type") or resolution_row.get("resolution_type") or "context_only")
            llm_result = resolution_row.get("llm_result") if isinstance(resolution_row.get("llm_result"), dict) else {}
            llm_confidence = _to_float(llm_result.get("confidence") or resolution_row.get("llm_confidence"))
            conflict_score = _to_float(conflict_row.get("conflict_score"))
            residual = _llm_conflict_feedback_quality(
                resolved_by=row_status,
                resolution_type=resolution_type,
                confidence=llm_confidence,
                conflict_score=conflict_score,
            )
            meta_payload = {
                "route": "llm",
                "arbiter": row_status,
                "conflict_id": item_id,
                "resolution_type": resolution_type,
                "llm_confidence": round(llm_confidence, 4),
                "conflict_score": round(conflict_score, 4),
            }
            try:
                evolution_storage.log_feedback(
                    session_id=session_id,
                    decision_id=item_id,
                    action="conflict_resolution",
                    status=row_status,
                    residual=residual,
                    meta=meta_payload,
                )
                feedback_rows.append(
                    {
                        "session_id": session_id,
                        "decision_id": item_id,
                        "action": "conflict_resolution",
                        "status": row_status,
                        "residual_correction": residual,
                        "meta": meta_payload,
                    }
                )
            except Exception:
                pass
        knowledge_snapshot = build_knowledge_snapshot(
            claims=updated_meta.get("plugin_claims", []),
            conflicts=updated_meta.get("plugin_conflicts", []),
            conflict_resolutions=updated_meta.get("plugin_conflict_resolutions", []),
            feedback_rows=feedback_rows
        )
        updated_meta["knowledge_snapshot"] = dict(knowledge_snapshot)
        updated_meta["plugin_conflicts"] = route_conflicts(
            conflicts=updated_meta.get("plugin_conflicts", []),
            knowledge_snapshot=knowledge_snapshot,
        )
        physics["meta"] = updated_meta
        await backend.set_physics(session_id, physics)
        return {
            "ok": True,
            "session_id": session_id,
            "conflict_id": normalized_conflict_id,
            "conflict_ids": conflict_ids,
            "arbiter": arbiter,
            "bundle": bundle,
            "prompt": prompt,
            "llm_reply": reply,
            "llm_result": parsed,
            "brain_action_queue": updated_meta.get("brain_action_queue", []),
            "knowledge_snapshot": updated_meta.get("knowledge_snapshot", {}),
            "conflicts": updated_meta.get("plugin_conflicts", []),
            "conflict_resolutions": updated_meta.get("plugin_conflict_resolutions", []),
        }

    updated_meta = meta
    manual_feedback_rows: list[dict[str, Any]] = []
    for item_id in conflict_ids:
        updated_meta = apply_conflict_resolution(meta=updated_meta, conflict_id=item_id, arbiter=arbiter)
        conflict_rows = (
            updated_meta.get("plugin_conflicts")
            if isinstance(updated_meta.get("plugin_conflicts"), list)
            else []
        )
        resolution_rows = (
            updated_meta.get("plugin_conflict_resolutions")
            if isinstance(updated_meta.get("plugin_conflict_resolutions"), list)
            else []
        )
        conflict_row = _find_conflict_row(conflict_rows, item_id)
        resolution_row = _find_resolution_row(resolution_rows, item_id)
        resolved_by = str(conflict_row.get("resolved_by") or resolution_row.get("resolved_by") or arbiter).strip().lower()
        if resolved_by not in {"system", "llm", "user"}:
            resolved_by = arbiter
        conflict_score = _to_float(conflict_row.get("conflict_score"))
        residual = _manual_conflict_feedback_quality(
            resolved_by=resolved_by,
            conflict_score=conflict_score,
        )
        meta_payload = {
            "route": "manual",
            "arbiter": resolved_by,
            "conflict_id": item_id,
            "conflict_score": round(conflict_score, 4),
        }
        try:
            evolution_storage.log_feedback(
                session_id=session_id,
                decision_id=item_id,
                action="conflict_resolution",
                status=resolved_by,
                residual=residual,
                meta=meta_payload,
            )
        except Exception:
            pass
        manual_feedback_rows.append(
            {
                "session_id": session_id,
                "decision_id": item_id,
                "action": "conflict_resolution",
                "status": resolved_by,
                "residual_correction": residual,
                "meta": meta_payload,
            }
        )
    feedback_rows = evolution_storage.get_feedback(session_id=session_id, action="conflict_resolution", limit=200)
    feedback_rows.extend(manual_feedback_rows)
    knowledge_snapshot = build_knowledge_snapshot(
        claims=updated_meta.get("plugin_claims", []),
        conflicts=updated_meta.get("plugin_conflicts", []),
        conflict_resolutions=updated_meta.get("plugin_conflict_resolutions", []),
        feedback_rows=feedback_rows,
    )
    updated_meta["knowledge_snapshot"] = dict(knowledge_snapshot)
    updated_meta["plugin_conflicts"] = route_conflicts(
        conflicts=updated_meta.get("plugin_conflicts", []),
        knowledge_snapshot=knowledge_snapshot,
    )
    physics["meta"] = updated_meta
    await backend.set_physics(session_id, physics)
    return {
        "ok": True,
        "session_id": session_id,
        "conflict_id": normalized_conflict_id,
        "conflict_ids": conflict_ids,
        "arbiter": arbiter,
        "conflicts": updated_meta.get("plugin_conflicts", []),
        "conflict_resolutions": updated_meta.get("plugin_conflict_resolutions", []),
    }


@router.get("/v17/admin/learning-campaign")
async def get_learning_campaign_status(
    v17_origin: Optional[str] = Query(default=None),
    v17_origin_header: Optional[str] = Header(default=None, alias="v17_origin"),
) -> Dict[str, Any]:
    _ensure_get_v17_origin(v17_origin=v17_origin, v17_origin_header=v17_origin_header)
    return {"ok": True, "campaign": _learning_campaign_status_payload()}


@router.post("/v17/admin/learning-campaign/start")
async def start_learning_campaign(payload: Dict[str, Any]) -> Dict[str, Any]:
    global _LEARNING_CAMPAIGN_TASK, _LEARNING_CAMPAIGN_PAUSE_REQUESTED
    _ensure_v17_origin(payload)
    if _LEARNING_CAMPAIGN_TASK is not None and not _LEARNING_CAMPAIGN_TASK.done():
        return {"ok": False, "detail": "learning campaign already running", "campaign": _learning_campaign_status_payload()}

    config = _learning_campaign_config_from_payload(payload)
    max_minutes = int(config.max_duration_seconds / 60)
    _LEARNING_CAMPAIGN_PAUSE_REQUESTED = False
    _LEARNING_CAMPAIGN_STATE.update(
        {
            "status": "running",
            "progress_percent": 1,
            "current_step": "queued",
            "current_step_label": "已排队",
            "estimated_remaining_seconds": config.max_duration_seconds,
            "started_at": _now_label(),
            "completed_at": "",
            "message": "学习 Campaign 已启动。",
            "config": {
                "max_minutes": max_minutes,
                "max_extended_cases": config.max_extended_cases,
                "request_llm_review": bool(config.request_llm_review),
                "include_extended_synthetic": bool(config.include_extended_synthetic),
                "include_practitioner_benchmarks": bool(config.include_practitioner_benchmarks),
                "include_auto_learning_loop": bool(config.include_auto_learning_loop),
            },
            "latest_report": {},
            "latest_report_markdown": "",
        }
    )
    _LEARNING_CAMPAIGN_TASK = asyncio.create_task(_run_learning_campaign_background(config))
    return {"ok": True, "campaign": _learning_campaign_status_payload()}


@router.post("/v17/admin/learning-campaign/pause")
async def pause_learning_campaign(payload: Dict[str, Any]) -> Dict[str, Any]:
    global _LEARNING_CAMPAIGN_PAUSE_REQUESTED
    _ensure_v17_origin(payload)
    if _LEARNING_CAMPAIGN_TASK is not None and not _LEARNING_CAMPAIGN_TASK.done():
        _LEARNING_CAMPAIGN_PAUSE_REQUESTED = True
        _LEARNING_CAMPAIGN_STATE.update(
            {
                "status": "pause_requested",
                "message": "已请求暂停；当前阶段结束后停止。",
            }
        )
    else:
        _LEARNING_CAMPAIGN_STATE.update(
            {
                "status": "paused",
                "current_step": "paused",
                "current_step_label": "已暂停",
                "message": "当前没有运行中的 Campaign。",
            }
        )
    return {"ok": True, "campaign": _learning_campaign_status_payload()}


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
