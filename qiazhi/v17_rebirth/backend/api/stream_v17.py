from __future__ import annotations

import json
import asyncio
import logging
import os
import fcntl
from datetime import datetime, timezone
from typing import Any, AsyncIterator, Dict, List, Optional, Union

from v17_rebirth.paths import RUNTIME_DIR

from fastapi.responses import JSONResponse, StreamingResponse

from v17_rebirth.infrastructure.state_backend import get_state_backend
from v17_rebirth.backend.services.physics_service import PhysicsService

from v17_rebirth.backend.api import stream_v17_decision_flow as _decision_flow
from v17_rebirth.backend.api import stream_v17_action_flow as _action_flow
from v17_rebirth.backend.api import stream_v17_streaming as _streaming
from v17_rebirth.backend.api.stream_v17_physics import (
    _run_v17_physics_core as _run_v17_physics_core_delegate,
    _safe_parse_birth_time as _safe_parse_birth_time_delegate,
    _should_rebuild_physics_core as _should_rebuild_physics_core_delegate,
)

_WILL_IMPACT_BUFFER: List[Dict[str, Any]] = []
_ACTION_SEQ = 0
_FREEZE_FILE = RUNTIME_DIR / "v17_causal_reports.json"
# V17.23-Red：_SESSION_QUEUES 已迁移到 StateBackend.subscribe_actions/publish_action
# V17.20：六柱与流年锚点仅允许由服务端 physics core 写入，禁止 POST Body 覆盖。
_PHYS_SSOT_KEYS = frozenset({"four_pillars", "luck_pillar", "flow_pillar", "flow_year"})
_PLAN_AUTO_APPROVE_MAX_COUNT = 8
_PLAN_AUTO_APPROVE_MAX_RATIO = 0.18
_PLAN_AUTO_APPROVE_MAX_SUM = 1.0


_log = logging.getLogger(__name__)


def _warn_if_multi_worker() -> None:
    """V17.23：进程内 Queue / PhysicsService 在 multi-worker 下无法共享，启动时告警。"""
    concurrency = str(os.getenv("WEB_CONCURRENCY", "") or "").strip()
    workers_arg = str(os.getenv("UVICORN_WORKERS", "") or "").strip()
    try:
        if (concurrency and int(concurrency) > 1) or (workers_arg and int(workers_arg) > 1):
            _log.warning(
                "[V17-CRITICAL] Multi-worker mode detected (WEB_CONCURRENCY=%s / UVICORN_WORKERS=%s). "
                "_SESSION_QUEUES and _SESSION_PHYSICS are in-process only — "
                "Action signals WILL NOT reach streams in other workers. "
                "Mitigation: set --workers 1, or migrate queues to Redis Pub/Sub.",
                concurrency, workers_arg,
            )
    except (TypeError, ValueError):
        pass


_warn_if_multi_worker()



def _v17_api_secret() -> str:
    """
    V17.23：从环境变量读取 API 密钥。
    生产环境建议设置 QIAZHI_V17_API_SECRET 为一个随机高强度字符串。
    未设置时退化为默认字符串（开发兼容）。
    """
    return str(os.getenv("QIAZHI_V17_API_SECRET", "v17_rebirth") or "v17_rebirth").strip()


def _sovereignty_v17(origin: Optional[str]) -> bool:
    """校验 v17_origin / X-V17-Origin 头是否与当前密钥匹配。"""
    return str(origin or "").strip() == _v17_api_secret()


def _default_payload() -> Dict[str, Any]:
    scores = {"正官": 51.34, "食神": 20.1, "比肩": 8.9, "偏印": 5.4}
    return {
        "ten_gods_base_l0": dict(scores),
        "ten_gods_runtime": dict(scores),
        "deity_scores": dict(scores),
        "ten_gods_absolute_intensity": dict(scores),
        "ten_gods_absolute": dict(scores),
        "total_energy_index": 85.74,
        "facts": [
            "五行火旺，结构张力上扬",
            "正官牵引秩序诉求增强",
            "外部压力触发自我收束",
        ],
    }


def _sync_append_freeze_report(entry: Dict[str, Any]) -> str:
    """同步写入（在 asyncio.to_thread 中执行），带 fcntl 文件锁避免并发写入竞争。"""
    _FREEZE_FILE.parent.mkdir(parents=True, exist_ok=True)
    rid = f"v17r_{int(datetime.now(timezone.utc).timestamp() * 1000)}"
    with open(_FREEZE_FILE, "a+", encoding="utf-8") as fh:
        fcntl.flock(fh, fcntl.LOCK_EX)
        try:
            fh.seek(0)
            raw = fh.read()
            rows: List[Dict[str, Any]] = []
            if raw.strip():
                try:
                    parsed = json.loads(raw)
                    if isinstance(parsed, list):
                        rows = [x for x in parsed if isinstance(x, dict)]
                except Exception:
                    rows = []
            rows.append({"report_id": rid, **entry})
            rows = rows[-300:]
            fh.seek(0)
            fh.truncate()
            fh.write(json.dumps(rows, ensure_ascii=False, indent=2))
        finally:
            fcntl.flock(fh, fcntl.LOCK_UN)
    return rid


async def _append_freeze_report(entry: Dict[str, Any]) -> str:
    """async 包装：将同步文件 I/O 卓罴到线程池，不阻塞事件循环。"""
    return await asyncio.to_thread(_sync_append_freeze_report, entry)


def _safe_parse_birth_time(value: Optional[str]) -> Optional[datetime]:
    return _safe_parse_birth_time_delegate(value)


def _should_rebuild_physics_core(
    *,
    current_physics: Dict[str, Any] | None,
    birth_time: Optional[str],
    gender: Optional[str],
    flow_year: Optional[int],
) -> bool:
    return _should_rebuild_physics_core_delegate(
        current_physics=current_physics,
        birth_time=birth_time,
        gender=gender,
        flow_year=flow_year,
    )


def _run_v17_physics_core(
    *,
    birth_time: Optional[datetime],
    gender: Optional[str],
    flow_year: Optional[int] = None,
) -> Dict[str, Any]:
    return _run_v17_physics_core_delegate(birth_time=birth_time, gender=gender, flow_year=flow_year)


def _decision_route_reason(payload: Dict[str, Any], rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    return _decision_flow.decision_route_reason(
        payload=payload,
        rows=rows,
        plan_auto_approve_max_count=_PLAN_AUTO_APPROVE_MAX_COUNT,
        plan_auto_approve_max_ratio=_PLAN_AUTO_APPROVE_MAX_RATIO,
        plan_auto_approve_max_sum=_PLAN_AUTO_APPROVE_MAX_SUM,
    )


def _boolish(value: Any, *, default: bool = False) -> bool:
    return _decision_flow.boolish(value=value, default=default)



async def _self_heal_physics_if_missing(session_id: str, pl: Dict[str, Any]) -> bool:
    return await _streaming.self_heal_physics_if_missing(
        session_id=session_id,
        pl=pl,
        run_physics_core=_run_v17_physics_core,
        parse_birth_time=_safe_parse_birth_time,
    )


async def _hydrate_physics_atomically(pl: Dict[str, Any]) -> None:
    await _streaming.hydrate_physics_atomically(pl)


def _normalize_plan_signal(payload_signal: str, status: str) -> str:
    return _decision_flow.normalize_plan_signal(payload_signal=payload_signal, status=status)


def _stream_frames(*, will_proxy: str, payload: Dict[str, Any]) -> AsyncIterator[bytes]:
    return _streaming.stream_frames(
        will_proxy=will_proxy,
        payload=payload,
        run_physics_core=_run_v17_physics_core,
    )


async def stream_v17(
    will_proxy: str = "stable",
    birth_time: Optional[str] = None,
    gender: Optional[str] = "male",
    flow_year: Optional[int] = None,
    v17_origin: Optional[str] = None,
) -> Union[StreamingResponse, JSONResponse]:
    if not _sovereignty_v17(v17_origin):
        return JSONResponse({"ok": False, "detail": "v17_origin validation failed"}, status_code=403)
    physics_payload = _run_v17_physics_core(
        birth_time=_safe_parse_birth_time(birth_time),
        gender=gender,
        flow_year=flow_year,
    )
    return StreamingResponse(
        _stream_frames(will_proxy=will_proxy, payload=physics_payload),
        media_type="application/x-ndjson",
        headers={
            "X-Accel-Buffering": "no",
            "Cache-Control": "no-cache, no-store",
            "Connection": "keep-alive",
        },
    )


async def stream_v17_post(
    payload: Dict[str, Any],
    will_proxy: str = "stable",
    birth_time: Optional[str] = None,
    gender: Optional[str] = "male",
    flow_year: Optional[int] = None,
) -> Union[StreamingResponse, JSONResponse]:
    session_id = str((payload or {}).get("session_id", "")).strip() or "default"
    current_physics = await get_state_backend().get_physics(session_id)
    if _should_rebuild_physics_core(
        current_physics=current_physics if isinstance(current_physics, dict) else None,
        birth_time=birth_time,
        gender=gender,
        flow_year=flow_year,
    ):
        merged_payload = _run_v17_physics_core(
            birth_time=_safe_parse_birth_time(birth_time),
            gender=gender,
            flow_year=flow_year,
        )
    else:
        merged_payload = dict(current_physics) if isinstance(current_physics, dict) and current_physics else _run_v17_physics_core(
            birth_time=_safe_parse_birth_time(birth_time),
            gender=gender,
            flow_year=flow_year,
        )
    if isinstance(payload, dict):
        for _k, _v in payload.items():
            if _k in _PHYS_SSOT_KEYS:
                continue
            merged_payload[_k] = _v
    if not _sovereignty_v17(str(merged_payload.get("v17_origin", "")) if isinstance(merged_payload, dict) else None):
        return JSONResponse({"ok": False, "detail": "v17_origin validation failed"}, status_code=403)
    if _WILL_IMPACT_BUFFER:
        last = _WILL_IMPACT_BUFFER[-1]
        if str(last.get("signal", "")).upper() == "ACTION_TAKEN":
            merged_payload["user_message"] = str(last.get("action", "")).strip()
            merged_payload["_action_seq"] = int(last.get("seq", 0) or 0)
    return StreamingResponse(
        _stream_frames(will_proxy=will_proxy, payload=merged_payload if isinstance(merged_payload, dict) else _default_payload()),
        media_type="application/x-ndjson",
        headers={
            "X-Accel-Buffering": "no",
            "Cache-Control": "no-cache, no-store",
            "Connection": "keep-alive",
        },
    )


async def v17_action(
    payload: Dict[str, Any],
    v17_origin: Optional[str] = None,
) -> JSONResponse:
    global _ACTION_SEQ
    body_origin = str(payload.get("v17_origin", "")).strip()
    header_origin = str(v17_origin or "").strip()
    if not _sovereignty_v17(body_origin) and not _sovereignty_v17(header_origin):
        return JSONResponse({"ok": False, "detail": "v17_origin validation failed"}, status_code=403)
    signal = str(payload.get("signal", "")).strip().upper()
    action = str(payload.get("action", "")).strip()
    raw_status = str(payload.get("status", "APPROVED")).strip().upper()
    if signal in {"", "INJECT_PATCH"}:
        signal = "PLAN_SUBMIT"
    plan_signal = _normalize_plan_signal(signal, raw_status)
    if plan_signal not in {"PLAN_SUBMIT", "PLAN_APPROVE", "PLAN_REJECT", "PLAN_ESCALATE", "PLAN_WITHDRAW"}:
        return JSONResponse({"ok": False, "detail": "invalid action signal"}, status_code=400)
    _ACTION_SEQ += 1
    session_id = str(payload.get("session_id", "")).strip() or "default"
    decision_id = str(payload.get("decision_id", "")).strip()
    plan_id = str(payload.get("plan_id", "")).strip()
    event = {
        "signal": signal,
        "plan_signal": plan_signal,
        "action": action,
        "plan_id": plan_id,
        "ts": datetime.now(timezone.utc).isoformat(),
        "seq": _ACTION_SEQ,
        "session_id": session_id,
    }
    request_verdict = _boolish(payload.get("request_verdict"), default=True)
    return await _action_flow.process_plan_signal_action(
        payload=payload,
        signal=signal,
        action=action,
        raw_status=raw_status,
        plan_signal=plan_signal,
        session_id=session_id,
        decision_id=decision_id,
        plan_id=plan_id,
        action_seq=_ACTION_SEQ,
        request_verdict=request_verdict,
        get_state_backend_fn=get_state_backend,
    )


async def freeze_report(
    payload: Dict[str, Any],
    v17_origin_header: Optional[str] = None,
) -> JSONResponse:
    origin = str(payload.get("v17_origin", "")).strip() or str(v17_origin_header or "").strip()
    if not _sovereignty_v17(origin):
        return JSONResponse({"ok": False, "detail": "v17_origin validation failed"}, status_code=403)
    render_text = str(payload.get("render_text", "")).strip()
    decisions = payload.get("decisions")
    if not render_text:
        return JSONResponse({"ok": False, "detail": "render_text is required"}, status_code=400)
    rows = decisions if isinstance(decisions, list) else []
    sanitized_rows = [{"id": str((x or {}).get("id", "")).strip(), "label": str((x or {}).get("label", "")).strip()} for x in rows if isinstance(x, dict)]
    rid = _append_freeze_report(
        {
            "v17_origin": "v17_rebirth",
            "timestamp": datetime.utcnow().isoformat(),
            "render_text": render_text,
            "decisions": [x for x in sanitized_rows if x["label"]],
        }
    )
    return JSONResponse({"ok": True, "report_id": rid})
