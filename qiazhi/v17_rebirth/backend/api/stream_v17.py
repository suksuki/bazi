from __future__ import annotations

import json
import asyncio
import os
from pathlib import Path
from datetime import datetime
from typing import Any, AsyncIterator, Dict, List, Optional, Tuple, Union

from fastapi import APIRouter, Header, Query
from fastapi.responses import JSONResponse, StreamingResponse

from v17_rebirth.infrastructure.stream_interrupt import ActionInterruptDuringStream

from v17_rebirth.backend.logic.L1_atomic_ops.l1_meta_hydration import hydrate_v17_physics_tensor
from v17_rebirth.backend.services.physics_service import DataSovereigntyError, PhysicsService
from v17_rebirth.backend.services.verdict_orchestrator import VerdictOrchestrator
from v17_rebirth.infrastructure.llm_bridge import V17_ROLE_JUDGE, V17_ROLE_WEAVER

router = APIRouter(tags=["v17"])
_WILL_IMPACT_BUFFER: List[Dict[str, Any]] = []
_ACTION_SEQ = 0
_FREEZE_FILE = Path("/home/hlsystem/bazi/qiazhi/v17_rebirth/.runtime/v17_causal_reports.json")
_SESSION_QUEUES: Dict[str, "asyncio.Queue[Dict[str, Any]]"] = {}
# V17.20：六柱与流年锚点仅允许由服务端 physics core 写入，禁止 POST Body 覆盖。
_PHYS_SSOT_KEYS = frozenset({"four_pillars", "luck_pillar", "flow_pillar", "flow_year"})


def _sovereignty_v17(origin: Optional[str]) -> bool:
    return str(origin or "").strip() == "v17_rebirth"


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


def _safe_parse_birth_time(value: Optional[str]) -> Optional[datetime]:
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


def _pillars_from_lunar(*, birth_time: datetime, gender: Optional[str], flow_year: int) -> Tuple[Dict[str, str], str, str]:
    """
    与 legacy BaziProfile 一致：使用 lunar_python 排四柱；流年用年中点规避立春边界；
    大运按 lunar 大运表匹配 flow_year（起运前空干支则顺延至首个有效大运）。
    """
    from lunar_python import Lunar, Solar

    lunar = Lunar.fromDate(birth_time)
    ec = lunar.getEightChar()
    four_pillars = {
        "year": str(ec.getYear() or ""),
        "month": str(ec.getMonth() or ""),
        "day": str(ec.getDay() or ""),
        "hour": str(ec.getTime() or ""),
    }

    gender_code = 1 if str(gender or "").lower() == "male" else 0
    yun = ec.getYun(gender_code)
    luck_pillar = "—"
    for dy in yun.getDaYun():
        sy, ey = int(dy.getStartYear()), int(dy.getEndYear())
        if sy <= flow_year <= ey:
            gz = dy.getGanZhi()
            if isinstance(gz, str) and len(gz.strip()) >= 2:
                luck_pillar = gz.strip()
                break
    if luck_pillar == "—":
        for dy in yun.getDaYun():
            gz = dy.getGanZhi()
            if not (isinstance(gz, str) and len(gz.strip()) >= 2):
                continue
            sy = int(dy.getStartYear())
            if flow_year < sy:
                luck_pillar = gz.strip()
                break

    solar = Solar.fromYmd(int(flow_year), 6, 15)
    ygz = solar.getLunar().getYearInGanZhi()
    flow_pillar = str(ygz).strip() if ygz else "—"

    return four_pillars, luck_pillar, flow_pillar


def _run_v17_physics_core(
    *,
    birth_time: Optional[datetime],
    gender: Optional[str],
    flow_year: Optional[int] = None,
) -> Dict[str, Any]:
    stems = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
    branches = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
    dt = birth_time or datetime.utcnow()
    gender_norm = "male" if str(gender or "").lower() == "male" else "female"
    fy = int(flow_year) if flow_year is not None else datetime.now().year

    luck_pillar = "—"
    flow_pillar = "—"
    try:
        four_pillars, luck_pillar, flow_pillar = _pillars_from_lunar(birth_time=dt, gender=gender, flow_year=fy)
    except Exception:
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
        f"大运（{fy}）：{luck_pillar}；流年：{flow_pillar}",
        f"十神主轴：{'、'.join(ten_gods)}",
        "命局主线已进入 V17 叙事织造阶段",
    ]
    return {
        "deity_scores": scores,
        "facts": facts,
        "four_pillars": four_pillars,
        "luck_pillar": luck_pillar,
        "flow_pillar": flow_pillar,
        "flow_year": fy,
        "ten_gods": ten_gods,
        "gender": gender_norm,
        "birth_time": dt.isoformat(),
    }


def _physical_void_stop_frame() -> Dict[str, Any]:
    """物理门控失败时唯一出帧：禁止 physics 快照与 LLM 抢跑。"""
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "layer": "SNAPSHOT",
        "payload": {
            "snapshot_kind": "physical_void",
            "render_text": "[圣殿警告] 物理因果缺失，叙事引擎已强行熄火。",
            "llm_meta": {
                "ok": False,
                "engine_state": "physical_void",
                "physics_guard": True,
            },
        },
    }


def _system_init_failure_stop_frame() -> Dict[str, Any]:
    """元数据未稳定（DataSovereigntyError）：禁止任何 NARRATOR 抢跑。"""
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "layer": "SNAPSHOT",
        "payload": {
            "snapshot_kind": "system_init_failure",
            "render_text": "系统初始化失败",
            "llm_meta": {
                "ok": False,
                "engine_state": "physics_metadata_unstable",
                "visibility_lock": True,
                "data_sovereignty": True,
            },
        },
    }


async def _hydrate_physics_atomically(pl: Dict[str, Any]) -> None:
    """在发出任何 SNAPSHOT(physics) 之前，于线程中完成 meta 张量注水，与 HTTP 响应流解耦。"""

    def _sync() -> None:
        hydrate_v17_physics_tensor(pl)

    await asyncio.to_thread(_sync)


def _sse_heartbeat_sec() -> float:
    """编排协程超过该间隔未 yield 则下发 HEARTBEAT；默认 2s；可用 QIAZHI_V17_SSE_HEARTBEAT_SEC 覆盖。"""
    try:
        v = float(str(os.getenv("QIAZHI_V17_SSE_HEARTBEAT_SEC", "2.0") or "2.0").strip())
        return max(1.0, min(120.0, v))
    except (TypeError, ValueError):
        return 2.0


def _frame_step_cursor(frame: Dict[str, Any]) -> str:
    """从 NDJSON 帧推断当前步进标签，供 HEARTBEAT 携带。"""
    layer = str(frame.get("layer") or "")
    pl = frame.get("payload") if isinstance(frame.get("payload"), dict) else {}
    if layer == "SNAPSHOT":
        sk = str(pl.get("snapshot_kind") or "").strip()
        if sk == "system_init_failure":
            return "SNAPSHOT:system_init_failure"
        if sk == "physical_void":
            return "SNAPSHOT:physical_void"
        return f"SNAPSHOT:{sk}" if sk else "SNAPSHOT"
    if layer == "WILL_FLASH":
        return "WILL_FLASH:ACTION_TAKEN"
    if layer == "NARRATOR":
        lm = pl.get("llm_meta") if isinstance(pl.get("llm_meta"), dict) else {}
        beat = str(lm.get("叙事节拍") or lm.get("engine_state") or "").strip()
        if beat:
            return f"NARRATOR:{beat}"
        if lm.get("stream_partial") or lm.get("audit_preview"):
            return "NARRATOR:streaming_partial"
        return "NARRATOR:body"
    if layer == "HEARTBEAT":
        return str(pl.get("step_position") or "HEARTBEAT")
    return layer or "unknown"


async def _narrator_with_heartbeat(
    agen: AsyncIterator[Dict[str, Any]],
) -> AsyncIterator[Dict[str, Any]]:
    """在 async for 迭代上包一层：超过间隔无帧则下发 HEARTBEAT（含步进位置），避免 SSE 被代理/浏览器静默掐断。"""
    sec = _sse_heartbeat_sec()
    it = agen.__aiter__()
    step_cursor = "START"
    while True:
        try:
            frame = await asyncio.wait_for(it.__anext__(), timeout=sec)
        except StopAsyncIteration:
            break
        except asyncio.TimeoutError:
            yield {
                "timestamp": datetime.utcnow().isoformat(),
                "layer": "HEARTBEAT",
                "payload": {"signal": "sse_tick", "idle_sec": sec, "step_position": step_cursor},
            }
            continue
        step_cursor = _frame_step_cursor(frame)
        yield frame


async def _stream_frames(*, will_proxy: str, payload: Dict[str, Any]) -> AsyncIterator[bytes]:
    orchestrator = VerdictOrchestrator()
    pl = payload if isinstance(payload, dict) else {}
    session_id = str(pl.get("session_id", "")).strip() or "default"
    await _hydrate_physics_atomically(pl)
    try:
        orchestrator.assert_six_pillars_physics(pl)
    except DataSovereigntyError:
        yield (json.dumps(_physical_void_stop_frame(), ensure_ascii=False) + "\n").encode("utf-8")
        await asyncio.sleep(0)
        return
    PhysicsService.bind_session_tensor(session_id, pl)
    try:
        await PhysicsService.ensure_stability(session_id)
    except DataSovereigntyError:
        yield (json.dumps(_system_init_failure_stop_frame(), ensure_ascii=False) + "\n").encode("utf-8")
        await asyncio.sleep(0)
        return
    raw_physics = pl
    facts = pl.get("facts") if isinstance(pl.get("facts"), list) else []
    dec_raw = pl.get("decisions") if isinstance(pl.get("decisions"), list) else []
    decisions_rows: List[Dict[str, Any]] = []
    for x in dec_raw:
        if not isinstance(x, dict):
            continue
        lab = str(x.get("label") or x.get("title") or "").strip()
        if lab:
            decisions_rows.append({"id": str(x.get("id") or "").strip(), "label": lab, "title": str(x.get("title") or "").strip()})
    narrative_role = V17_ROLE_JUDGE if decisions_rows else V17_ROLE_WEAVER
    queue = _SESSION_QUEUES.setdefault(session_id, asyncio.Queue())
    # Frame 0: SNAPSHOT（柱位与 LLM 锚定同源：bind 后强读 PhysicsService；禁止空柱快照出闸）
    try:
        snap = orchestrator.snapshot_frame(raw_physics=raw_physics, session_id=session_id)
    except DataSovereigntyError:
        yield (json.dumps(_physical_void_stop_frame(), ensure_ascii=False) + "\n").encode("utf-8")
        await asyncio.sleep(0)
        return
    yield (json.dumps(snap, ensure_ascii=False) + "\n").encode("utf-8")
    await asyncio.sleep(0)
    # Frame 1..N: NARRATOR — LLM 真流式 + ActionQueue 内联 cancel，异常即 WILL_FLASH 重启
    current_user_message = str(pl.get("user_message", "")).strip()
    current_action_signal = bool(current_user_message)
    current_proxy = str(will_proxy or "stable")
    decision_anchor = current_user_message
    while True:
        restarted = False
        try:
            async for frame in _narrator_with_heartbeat(
                orchestrator.narrator_frames(
                    raw_physics=raw_physics,
                    facts=[str(x) for x in facts if str(x).strip()],
                    will_proxy=current_proxy,
                    user_message=current_user_message,
                    action_signal=current_action_signal,
                    decision_anchor=decision_anchor,
                    action_queue=queue,
                    role_style=narrative_role,
                    decisions=decisions_rows,
                    session_id=session_id,
                )
            ):
                yield (json.dumps(frame, ensure_ascii=False) + "\n").encode("utf-8")
                await asyncio.sleep(0)
        except DataSovereigntyError as _dse:
            if str(_dse).strip() == "physics_metadata_unstable":
                yield (json.dumps(_system_init_failure_stop_frame(), ensure_ascii=False) + "\n").encode("utf-8")
            else:
                yield (json.dumps(_physical_void_stop_frame(), ensure_ascii=False) + "\n").encode("utf-8")
            await asyncio.sleep(0)
            break
        except ActionInterruptDuringStream as exc:
            pl = exc.payload if isinstance(exc.payload, dict) else {}
            current_user_message = str(pl.get("action", "")).strip()
            decision_anchor = current_user_message
            current_action_signal = True
            if any(k in current_user_message for k in ["进", "冲", "突破", "加码"]):
                current_proxy = "aggressive"
            elif any(k in current_user_message for k in ["稳", "守", "风控", "谨慎", "避险"]):
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
            await asyncio.sleep(0)
            restarted = True
        if restarted:
            continue
        break


@router.get("/v17/stream", response_model=None)
@router.get("/api/v17/stream", response_model=None)
async def stream_v17(
    will_proxy: str = Query(default="stable", pattern="^(stable|aggressive|neutral)$"),
    birth_time: Optional[str] = Query(default=None),
    gender: Optional[str] = Query(default="female", pattern="^(male|female)$"),
    flow_year: Optional[int] = Query(default=None, ge=1800, le=2200),
    v17_origin: Optional[str] = Query(default=None),
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


@router.post("/v17/stream", response_model=None)
@router.post("/api/v17/stream", response_model=None)
async def stream_v17_post(
    payload: Dict[str, Any],
    will_proxy: str = Query(default="stable", pattern="^(stable|aggressive|neutral)$"),
    birth_time: Optional[str] = Query(default=None),
    gender: Optional[str] = Query(default="female", pattern="^(male|female)$"),
    flow_year: Optional[int] = Query(default=None, ge=1800, le=2200),
) -> Union[StreamingResponse, JSONResponse]:
    merged_payload = _run_v17_physics_core(
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


@router.post("/v17/action")
@router.post("/api/v17/action")
async def v17_action(payload: Dict[str, Any], v17_origin: Optional[str] = Header(default=None, alias="v17_origin")) -> JSONResponse:
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
async def freeze_report(
    payload: Dict[str, Any],
    v17_origin_header: Optional[str] = Header(default=None, alias="v17_origin"),
) -> JSONResponse:
    origin = str(payload.get("v17_origin", "")).strip() or str(v17_origin_header or "").strip()
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
