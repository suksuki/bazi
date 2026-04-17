from __future__ import annotations

import json
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Any, AsyncIterator, Dict, List

from fastapi import APIRouter, Header, Query
from fastapi.responses import JSONResponse, StreamingResponse

from v17_rebirth.backend.services.verdict_orchestrator import VerdictOrchestrator

router = APIRouter(tags=["v17"])
_WILL_IMPACT_BUFFER: List[Dict[str, Any]] = []
_ACTION_SEQ = 0
_FREEZE_FILE = Path("/home/hlsystem/bazi/qiazhi/v17_rebirth/.runtime/v17_causal_reports.json")
_SESSION_QUEUES: Dict[str, "asyncio.Queue[Dict[str, Any]]"] = {}


def _default_payload() -> Dict[str, Any]:
    return {
        "deity_scores": {"正官": 51.34, "食神": 20.1, "比肩": 8.9, "偏印": 5.4},
        "facts": [
            "五行火旺，结构张力上扬",
            "正官牵引秩序诉求增强",
            "外部压力触发自我收束",
        ],
    }


def _append_freeze_report(entry: Dict[str, Any]) -> str:
    _FREEZE_FILE.parent.mkdir(parents=True, exist_ok=True)
    rows: List[Dict[str, Any]] = []
    if _FREEZE_FILE.exists():
        try:
            raw = json.loads(_FREEZE_FILE.read_text(encoding="utf-8"))
            if isinstance(raw, list):
                rows = [x for x in raw if isinstance(x, dict)]
        except Exception:
            rows = []
    rid = f"v17r_{int(datetime.utcnow().timestamp() * 1000)}"
    rows.append({"report_id": rid, **entry})
    rows = rows[-300:]
    _FREEZE_FILE.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    return rid


def _safe_parse_birth_time(value: str | None) -> datetime | None:
    if not value:
        return None
    raw = str(value).strip()
    if not raw:
        return None
    try:
        # Accept "Z" suffix for web clients.
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None


def _pillar(stems: List[str], branches: List[str], idx: int) -> str:
    return f"{stems[idx % len(stems)]}{branches[idx % len(branches)]}"


def _run_v17_physics_core(*, birth_time: datetime | None, gender: str | None) -> Dict[str, Any]:
    stems = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
    branches = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
    dt = birth_time or datetime.utcnow()
    gender_norm = "male" if str(gender or "").lower() == "male" else "female"

    year_idx = dt.year
    month_idx = dt.year * 12 + dt.month
    day_idx = dt.toordinal()
    hour_idx = day_idx * 12 + (dt.hour // 2)
    four_pillars = {
        "year": _pillar(stems, branches, year_idx),
        "month": _pillar(stems, branches, month_idx),
        "day": _pillar(stems, branches, day_idx),
        "hour": _pillar(stems, branches, hour_idx),
    }

    base = {
        "正官": 28.0 + (dt.month % 6) * 3.2,
        "食神": 16.0 + (dt.day % 7) * 2.4,
        "比肩": 10.0 + (dt.hour % 6) * 2.1,
        "偏印": 8.0 + (dt.year % 5) * 1.8,
        "正财": 12.0 + (dt.month % 4) * 2.0,
    }
    if gender_norm == "male":
        base["正官"] += 2.2
        base["比肩"] += 1.3
    else:
        base["食神"] += 2.0
        base["正财"] += 1.1

    scores = {k: round(v, 2) for k, v in base.items()}
    ten_gods = [k for k, _ in sorted(scores.items(), key=lambda kv: kv[1], reverse=True)[:4]]
    facts = [
        f"四柱落位：年{four_pillars['year']} 月{four_pillars['month']} 日{four_pillars['day']} 时{four_pillars['hour']}",
        f"十神主轴：{'、'.join(ten_gods)}",
        "命局主线已进入 V17 叙事织造阶段",
    ]
    return {
        "deity_scores": scores,
        "facts": facts,
        "four_pillars": four_pillars,
        "ten_gods": ten_gods,
        "gender": gender_norm,
        "birth_time": dt.isoformat(),
    }


async def _stream_frames(*, will_proxy: str, payload: Dict[str, Any]) -> AsyncIterator[bytes]:
    orchestrator = VerdictOrchestrator()
    raw_physics = payload if isinstance(payload, dict) else {}
    facts = payload.get("facts") if isinstance(payload.get("facts"), list) else []
    session_id = str(payload.get("session_id", "")).strip() or "default"
    queue = _SESSION_QUEUES.setdefault(session_id, asyncio.Queue())
    # Frame 0: SNAPSHOT
    snap = orchestrator.snapshot_frame(raw_physics=raw_physics)
    yield (json.dumps(snap, ensure_ascii=False) + "\n").encode("utf-8")
    # Frame 1..N: NARRATOR with side-channel abort/restart
    current_user_message = str(payload.get("user_message", "")).strip()
    current_action_signal = bool(current_user_message)
    current_proxy = str(will_proxy or "stable")
    decision_anchor = current_user_message
    while True:
        restarted = False
        async for frame in orchestrator.narrator_frames(
            raw_physics=raw_physics,
            facts=[str(x) for x in facts if str(x).strip()],
            will_proxy=current_proxy,
            user_message=current_user_message,
            action_signal=current_action_signal,
            decision_anchor=decision_anchor,
        ):
            action = None
            if not queue.empty():
                try:
                    action = queue.get_nowait()
                except asyncio.QueueEmpty:
                    action = None
            if action:
                current_user_message = str(action.get("action", "")).strip()
                decision_anchor = current_user_message
                current_action_signal = True
                if any(k in current_user_message for k in ["进", "冲", "突破", "加码"]):
                    current_proxy = "aggressive"
                elif any(k in current_user_message for k in ["稳", "守", "风控", "谨慎"]):
                    current_proxy = "stable"
                will_flash = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "layer": "WILL_FLASH",
                    "payload": {
                        "signal": "ACTION_TAKEN",
                        "action": current_user_message,
                        "will_proxy": current_proxy,
                        "will_flash": True,
                    },
                }
                yield (json.dumps(will_flash, ensure_ascii=False) + "\n").encode("utf-8")
                restarted = True
                break
            yield (json.dumps(frame, ensure_ascii=False) + "\n").encode("utf-8")
        if restarted:
            continue
        break


@router.get("/v17/stream")
@router.get("/api/v17/stream")
async def stream_v17(
    will_proxy: str = Query(default="stable", pattern="^(stable|aggressive|neutral)$"),
    birth_time: str | None = Query(default=None),
    gender: str | None = Query(default="female", pattern="^(male|female)$"),
) -> StreamingResponse:
    physics_payload = _run_v17_physics_core(
        birth_time=_safe_parse_birth_time(birth_time),
        gender=gender,
    )
    return StreamingResponse(
        _stream_frames(will_proxy=will_proxy, payload=physics_payload),
        media_type="application/x-ndjson",
    )


@router.post("/v17/stream")
@router.post("/api/v17/stream")
async def stream_v17_post(
    payload: Dict[str, Any],
    will_proxy: str = Query(default="stable", pattern="^(stable|aggressive|neutral)$"),
    birth_time: str | None = Query(default=None),
    gender: str | None = Query(default="female", pattern="^(male|female)$"),
) -> StreamingResponse:
    merged_payload = _run_v17_physics_core(
        birth_time=_safe_parse_birth_time(birth_time),
        gender=gender,
    )
    if isinstance(payload, dict):
        merged_payload.update(payload)
    if _WILL_IMPACT_BUFFER:
        last = _WILL_IMPACT_BUFFER[-1]
        if str(last.get("signal", "")).upper() == "ACTION_TAKEN":
            merged_payload["user_message"] = str(last.get("action", "")).strip()
            merged_payload["_action_seq"] = int(last.get("seq", 0) or 0)
    return StreamingResponse(
        _stream_frames(will_proxy=will_proxy, payload=merged_payload if isinstance(merged_payload, dict) else _default_payload()),
        media_type="application/x-ndjson",
    )


@router.post("/v17/action")
@router.post("/api/v17/action")
async def v17_action(payload: Dict[str, Any], v17_origin: str | None = Header(default=None, alias="v17_origin")) -> JSONResponse:
    global _ACTION_SEQ
    body_origin = str(payload.get("v17_origin", "")).strip()
    header_origin = str(v17_origin or "").strip()
    if body_origin != "v17_rebirth" and header_origin != "v17_rebirth":
        return JSONResponse({"ok": False, "detail": "v17_origin validation failed"}, status_code=403)
    signal = str(payload.get("signal", "")).strip().upper()
    action = str(payload.get("action", "")).strip()
    if signal not in {"ACTION_TAKEN", "INJECT_PATCH"} or not action:
        return JSONResponse({"ok": False, "detail": "invalid action signal"}, status_code=400)
    _ACTION_SEQ += 1
    session_id = str(payload.get("session_id", "")).strip() or "default"
    event = {"signal": signal, "action": action, "ts": datetime.utcnow().isoformat(), "seq": _ACTION_SEQ, "session_id": session_id}
    _WILL_IMPACT_BUFFER.append(event)
    _WILL_IMPACT_BUFFER[:] = _WILL_IMPACT_BUFFER[-20:]
    q = _SESSION_QUEUES.setdefault(session_id, asyncio.Queue())
    if q.qsize() > 20:
        try:
            q.get_nowait()
        except asyncio.QueueEmpty:
            pass
    q.put_nowait(event)
    return JSONResponse({"ok": True, "signal": signal, "will_proxy_delta": "aggressive" if any(k in action for k in ["进", "冲", "加码"]) else "stable"})


@router.post("/v17/freeze-report")
@router.post("/api/v17/freeze-report")
async def freeze_report(payload: Dict[str, Any]) -> JSONResponse:
    origin = str(payload.get("v17_origin", "")).strip()
    if origin != "v17_rebirth":
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
