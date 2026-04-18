from __future__ import annotations

import json
import asyncio
import fcntl
import logging
import os
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, AsyncIterator, Dict, List, Optional, Tuple, Union

from v17_rebirth.paths import RUNTIME_DIR

from fastapi import APIRouter, Header, Query
from fastapi.responses import JSONResponse, StreamingResponse

from v17_rebirth.infrastructure.stream_interrupt import ActionInterruptDuringStream
from v17_rebirth.infrastructure.state_backend import get_state_backend

from v17_rebirth.backend.logic.L1_atomic_ops.l1_meta_hydration import hydrate_v17_physics_tensor
from v17_rebirth.backend.services.physics_service import DataSovereigntyError, PhysicsService
from v17_rebirth.backend.services.verdict_orchestrator import VerdictOrchestrator
from v17_rebirth.infrastructure.llm_bridge import V17_ROLE_JUDGE, V17_ROLE_WEAVER

router = APIRouter(tags=["v17"])
_WILL_IMPACT_BUFFER: List[Dict[str, Any]] = []
_ACTION_SEQ = 0
_FREEZE_FILE = RUNTIME_DIR / "v17_causal_reports.json"
# V17.23-Red：_SESSION_QUEUES 已迁移到 StateBackend.subscribe_actions/publish_action
# V17.20：六柱与流年锚点仅允许由服务端 physics core 写入，禁止 POST Body 覆盖。
_PHYS_SSOT_KEYS = frozenset({"four_pillars", "luck_pillar", "flow_pillar", "flow_year"})


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
    return {
        "deity_scores": {"正官": 51.34, "食神": 20.1, "比肩": 8.9, "偏印": 5.4},
        "ten_gods_absolute_intensity": {"正官": 51.34, "食神": 20.1, "比肩": 8.9, "偏印": 5.4},
        "ten_gods_absolute": {"正官": 51.34, "食神": 20.1, "比肩": 8.9, "偏印": 5.4},
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
    from datetime import timezone as _tz
    from v17_rebirth.backend.logic.L0_physics_fields.ten_gods_engine import calc_deity_scores

    _stems = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
    _branches = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
    dt = birth_time or datetime.now(_tz.utc).replace(tzinfo=None)
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
            "year": _pillar(_stems, _branches, year_idx),
            "month": _pillar(_stems, _branches, month_idx),
            "day": _pillar(_stems, _branches, day_idx),
            "hour": _pillar(_stems, _branches, hour_idx),
        }

    # 真实十神分值：基于日主干支阴阳五行生克关系（L0 层 ten_gods_engine）
    scores, ten_gods, total_energy_index, energy_meta = calc_deity_scores(
        four_pillars=four_pillars,
        luck_pillar=luck_pillar,
        flow_pillar=flow_pillar,
        gender=gender_norm,
        birth_time=dt,
    )
    facts = [
        {
            "fact": f"四柱落位：年{four_pillars['year']} 月{four_pillars['month']} 日{four_pillars['day']} 时{four_pillars['hour']}",
            "weight": 0.98,
            "tier": 0,
        },
        {
            "fact": f"大运（{fy}）：{luck_pillar}；流年：{flow_pillar}",
            "weight": 0.96,
            "tier": 0,
        },
        {
            "fact": f"十神主轴：{'、'.join(ten_gods)}",
            "weight": 0.82,
            "tier": 1,
        },
        {
            "fact": "命局主线已进入 V17 叙事织造阶段",
            "weight": 0.52,
            "tier": 2,
        },
    ]
    # V17.32: 序列化 Evolution Ledger（从 EvolutionLedger 对象转为 JSON-safe dict）
    from v17_rebirth.backend.logic.L0_physics_fields.evolution_ledger import EvolutionLedger
    raw_ledger = energy_meta.pop("ledger", None)
    ten_gods_ledger = raw_ledger.to_dict() if isinstance(raw_ledger, EvolutionLedger) else {}

    return {
        "deity_scores": scores,
        "ten_gods_absolute_intensity": scores,
        "ten_gods_absolute": scores,
        "total_energy_index": total_energy_index,
        "energy_meta": energy_meta,
        "ten_gods_ledger": ten_gods_ledger,
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


def _narrator_runtime_failure_frame(*, err: Exception, step_cursor: str = "") -> Dict[str, Any]:
    err_name = type(err).__name__
    err_text = str(err).strip()
    detail = f"{err_name}: {err_text}" if err_text else err_name
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "layer": "NARRATOR",
        "payload": {
            "render_text": f"[叙事协程异常中止] {detail}",
            "llm_meta": {
                "ok": False,
                "engine_state": "orchestrator_runtime_error",
                "error": detail,
                "step_position": str(step_cursor or "").strip(),
            },
        },
    }


def _is_terminal_narrator_frame(frame: Dict[str, Any]) -> bool:
    if str(frame.get("layer") or "").strip().upper() != "NARRATOR":
        return False
    payload = frame.get("payload") if isinstance(frame.get("payload"), dict) else {}
    llm_meta = payload.get("llm_meta") if isinstance(payload.get("llm_meta"), dict) else {}
    if llm_meta.get("ok") is False:
        return True
    try:
        return llm_meta.get("elapsed_ms") is not None and not bool(llm_meta.get("stream_partial"))
    except Exception:
        return False


async def _hydrate_physics_atomically(pl: Dict[str, Any]) -> None:
    """在发出任何 SNAPSHOT(physics) 之前，于线程中完成 meta 张量注水，与 HTTP 响应流解耦。"""

    def _sync() -> None:
        hydrate_v17_physics_tensor(pl)

    await asyncio.to_thread(_sync)


async def _self_heal_physics_if_missing(session_id: str, pl: Dict[str, Any]) -> bool:
    """
    Redis/StateBackend 读空时，现场同步重算一遍 physics core 并重新绑定，
    尽量吸收前端请求快于后端持久化的竞态。
    """
    backend = get_state_backend()
    current = await backend.get_physics(session_id)
    if isinstance(current, dict) and current:
        return False

    _log.warning(
        "[V17-HEAL] Session %s physics tensor missing in backend; forcing synchronous physics core rebuild",
        session_id,
    )
    raw_flow_year = pl.get("flow_year")
    try:
        healed_flow_year = int(raw_flow_year) if raw_flow_year is not None else None
    except (TypeError, ValueError):
        healed_flow_year = None
    healed_payload = _run_v17_physics_core(
        birth_time=_safe_parse_birth_time(str(pl.get("birth_time") or "").strip() or None),
        gender=str(pl.get("gender") or "").strip() or None,
        flow_year=healed_flow_year,
    )
    pl.update(healed_payload)
    PhysicsService.prime_local_tensor(session_id, pl)
    await _hydrate_physics_atomically(pl)
    VerdictOrchestrator().assert_six_pillars_physics(pl)
    await PhysicsService.abind_session_tensor(session_id, pl)
    await PhysicsService.ensure_stability(session_id, local_physics=pl)
    return True


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


def _heartbeat_status_frame(*, step_cursor: str, idle_sec: float, idle_beats: int) -> Dict[str, Any] | None:
    """长时间无正文时，补发一条可审计的 NARRATOR 状态帧，避免前端只能盲等 HEARTBEAT。"""
    step = str(step_cursor or "START").strip() or "START"
    if step.startswith("SNAPSHOT:llm_audit_preview") or step.startswith("NARRATOR:已联通"):
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "layer": "NARRATOR",
            "payload": {
                "render_text": "",
                "llm_meta": {
                    "stream_partial": True,
                    "engine_state": "awaiting_first_token",
                    "heartbeat_step": step,
                    "idle_sec": idle_sec,
                    "idle_beats": idle_beats,
                },
                "source_facts": [],
            },
        }
    if step.startswith("NARRATOR:streaming_partial"):
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "layer": "NARRATOR",
            "payload": {
                "render_text": "",
                "llm_meta": {
                    "stream_partial": True,
                    "engine_state": "stream_stalled",
                    "heartbeat_step": step,
                    "idle_sec": idle_sec,
                    "idle_beats": idle_beats,
                },
                "source_facts": [],
            },
        }
    return None


def _should_retry_premature_close(step_cursor: str, retry_count: int) -> bool:
    step = str(step_cursor or "").strip()
    if retry_count >= 1:
        return False
    return (
        step == "START"
        or step.startswith("SNAPSHOT:llm_audit_dispatch")
        or step.startswith("SNAPSHOT:llm_audit_preview")
        or step.startswith("NARRATOR:已联通")
    )


async def _narrator_with_heartbeat(
    agen: AsyncIterator[Dict[str, Any]],
) -> AsyncIterator[Dict[str, Any]]:
    """在 async for 迭代上包一层：超过间隔无帧则下发 HEARTBEAT（含步进位置），避免 SSE 被代理/浏览器静默掐断。"""
    sec = _sse_heartbeat_sec()
    it = agen.__aiter__()
    step_cursor = "START"
    idle_beats = 0
    next_task: asyncio.Task[Dict[str, Any]] | None = None
    while True:
        try:
            if next_task is None:
                next_task = asyncio.create_task(it.__anext__())
            done, _ = await asyncio.wait({next_task}, timeout=sec, return_when=asyncio.FIRST_COMPLETED)
            if not done:
                raise asyncio.TimeoutError()
            frame = next_task.result()
            next_task = None
        except StopAsyncIteration:
            next_task = None
            break
        except asyncio.TimeoutError:
            idle_beats += 1
            yield {
                "timestamp": datetime.utcnow().isoformat(),
                "layer": "HEARTBEAT",
                "payload": {"signal": "sse_tick", "idle_sec": sec, "step_position": step_cursor},
            }
            if idle_beats >= 2:
                status_frame = _heartbeat_status_frame(
                    step_cursor=step_cursor,
                    idle_sec=sec,
                    idle_beats=idle_beats,
                )
                if status_frame is not None:
                    yield status_frame
            continue
        step_cursor = _frame_step_cursor(frame)
        idle_beats = 0
        yield frame
    if next_task is not None:
        next_task.cancel()
        try:
            await next_task
        except Exception:
            pass


async def _stream_frames(*, will_proxy: str, payload: Dict[str, Any]) -> AsyncIterator[bytes]:
    orchestrator = VerdictOrchestrator()
    pl = payload if isinstance(payload, dict) else {}
    session_id = str(pl.get("session_id", "")).strip() or "default"
    print(f"[V17-TRACE] Stream Request In: {session_id}", flush=True)

    # V17.24：Redis 活性探针——如果配置了 Redis 但连接失败，拒绝 SSE 启动（避免异常写入导致一系列下游报错）
    backend = get_state_backend()
    from v17_rebirth.infrastructure.state_backend import RedisStateBackend
    if isinstance(backend, RedisStateBackend):
        try:
            redis_ok = await backend.ping()
        except Exception:  # noqa: BLE001
            redis_ok = False
        if not redis_ok:
            _log.error("[V17-FATAL] Redis backend unreachable for session=%s — refusing SSE stream", session_id)
            yield (json.dumps({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "layer": "SNAPSHOT",
                "payload": {
                    "snapshot_kind": "system_init_failure",
                    "render_text": "[V17-FATAL] Redis 连接丢失，请查看后端 8017 日志。",
                    "llm_meta": {"ok": False, "engine_state": "redis_unreachable"},
                },
            }, ensure_ascii=False) + "\n").encode("utf-8")
            await asyncio.sleep(0)
            return

    await _hydrate_physics_atomically(pl)
    PhysicsService.prime_local_tensor(session_id, pl)
    try:
        orchestrator.assert_six_pillars_physics(pl)
    except DataSovereigntyError:
        # V17.24：因果残影——找出当前张量内容（帮助判断是数据未写入还是写错了地方）
        _log.error(
            "[V17-FATAL] Session %s assert_six_pillars_physics FAILED. "
            "Current pl keys: %s  |  four_pillars: %s  |  luck_pillar: %s  |  flow_pillar: %s",
            session_id,
            list(pl.keys()),
            pl.get("four_pillars"),
            pl.get("luck_pillar"),
            pl.get("flow_pillar"),
        )
        yield (json.dumps(_physical_void_stop_frame(), ensure_ascii=False) + "\n").encode("utf-8")
        await asyncio.sleep(0)
        return
    raw_physics = pl
    try:
        snap = orchestrator.snapshot_frame(
            raw_physics=raw_physics,
            session_id=session_id,
            causal_anchor="local_memory",
        )
    except DataSovereigntyError:
        yield (json.dumps(_physical_void_stop_frame(), ensure_ascii=False) + "\n").encode("utf-8")
        await asyncio.sleep(0)
        return
    _log.warning("[Local-Snapshot] session=%s causal_anchor=local_memory", session_id)
    yield (json.dumps(snap, ensure_ascii=False) + "\n").encode("utf-8")
    await asyncio.sleep(0)
    # 第二动：Redis 锁定确认；未确认即视为主权失败
    try:
        await PhysicsService.abind_session_tensor(session_id, raw_physics)
    except DataSovereigntyError:
        _log.error("[V17-FATAL] Session %s Redis bind confirmation failed", session_id)
        yield (json.dumps(_system_init_failure_stop_frame(), ensure_ascii=False) + "\n").encode("utf-8")
        await asyncio.sleep(0)
        return
    _log.warning("[Redis-Bind-Success] session=%s", session_id)
    try:
        await PhysicsService.ensure_stability(session_id, local_physics=raw_physics)
    except DataSovereigntyError:
        try:
            healed = await _self_heal_physics_if_missing(session_id, raw_physics)
        except DataSovereigntyError:
            healed = False
        if healed:
            _log.warning("[V17-HEAL] Session %s recovered after backend MISS", session_id)
        else:
            # V17.24：因果残影——展示 Redis 里实际存的 key
            try:
                tensor_keys = await PhysicsService.get_physics_keys(session_id)
            except Exception:  # noqa: BLE001
                tensor_keys = ["<failed to query>"]
            _log.error(
                "[V17-FATAL] Session %s tensor keys in backend: %s",
                session_id, tensor_keys,
            )
            yield (json.dumps(_system_init_failure_stop_frame(), ensure_ascii=False) + "\n").encode("utf-8")
            await asyncio.sleep(0)
            return
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
    # V17.23-Red：由 StateBackend 订阅事件（内存模式向后兼容，Redis 模式跨 worker）
    async with get_state_backend().subscribe_actions(session_id) as queue:
        _log.warning("[Narrator-Start] session=%s causal_anchor=redis_sync", session_id)
        # Frame 1..N: NARRATOR — LLM 真流式 + ActionQueue 内联 cancel，异常即 WILL_FLASH 重启
        current_user_message = str(pl.get("user_message", "")).strip()
        current_action_signal = bool(current_user_message)
        current_proxy = str(will_proxy or "stable")
        decision_anchor = current_user_message
        last_step_cursor = "START"
        premature_close_retry_count = 0
        while True:
            restarted = False
            saw_terminal_narrator = False
            try:
                async for frame in _narrator_with_heartbeat(
                    orchestrator.narrator_frames(
                        raw_physics=raw_physics,
                        facts=[x for x in facts if str(x).strip()],
                        will_proxy=current_proxy,
                        user_message=current_user_message,
                        action_signal=current_action_signal,
                        decision_anchor=decision_anchor,
                        action_queue=queue,
                        role_style=narrative_role,
                        decisions=decisions_rows,
                        session_id=session_id,
                        causal_anchor="redis_sync",
                        stability_checked=True,
                    )
                ):
                    if isinstance(frame, dict):
                        last_step_cursor = _frame_step_cursor(frame)
                        if _is_terminal_narrator_frame(frame):
                            saw_terminal_narrator = True
                    yield (json.dumps(frame, ensure_ascii=False) + "\n").encode("utf-8")
                    await asyncio.sleep(0)
                if not restarted and not saw_terminal_narrator:
                    if _should_retry_premature_close(last_step_cursor, premature_close_retry_count):
                        premature_close_retry_count += 1
                        _log.warning(
                            "[V17-NARRATOR-SOFT-RETRY] session=%s step=%s retry=%s",
                            session_id,
                            last_step_cursor,
                            premature_close_retry_count,
                        )
                        restarted = True
                    else:
                        _log.error(
                            "[V17-NARRATOR-PREMATURE-CLOSE] session=%s step=%s",
                            session_id,
                            last_step_cursor,
                        )
                        yield (
                            json.dumps(
                                _narrator_runtime_failure_frame(
                                    err=RuntimeError("narrator_stream_closed_without_terminal_frame"),
                                    step_cursor=last_step_cursor,
                                ),
                                ensure_ascii=False,
                            )
                            + "\n"
                        ).encode("utf-8")
                        await asyncio.sleep(0)
            except DataSovereigntyError as _dse:
                if str(_dse).strip() == "physics_metadata_unstable":
                    yield (json.dumps(_system_init_failure_stop_frame(), ensure_ascii=False) + "\n").encode("utf-8")
                else:
                    yield (json.dumps(_physical_void_stop_frame(), ensure_ascii=False) + "\n").encode("utf-8")
                await asyncio.sleep(0)
                break
            except ActionInterruptDuringStream as exc:
                action_pl = exc.payload if isinstance(exc.payload, dict) else {}
                current_user_message = str(action_pl.get("action", "")).strip()
                decision_anchor = current_user_message
                current_action_signal = True
                if any(k in current_user_message for k in ["进", "冲", "突破", "加码"]):
                    current_proxy = "aggressive"
                elif any(k in current_user_message for k in ["稳", "守", "风控", "谨慎", "避险"]):
                    current_proxy = "stable"
                will_flash = {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
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
            except Exception as exc:  # noqa: BLE001
                _log.exception("[V17-NARRATOR-CRASH] session=%s step=%s", session_id, last_step_cursor)
                yield (
                    json.dumps(
                        _narrator_runtime_failure_frame(err=exc, step_cursor=last_step_cursor),
                        ensure_ascii=False,
                    )
                    + "\n"
                ).encode("utf-8")
                await asyncio.sleep(0)
                break
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
    session_id = str((payload or {}).get("session_id", "")).strip() or "default"
    current_physics = await get_state_backend().get_physics(session_id)
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


@router.post("/v17/action")
@router.post("/api/v17/action")
async def v17_action(payload: Dict[str, Any], v17_origin: Optional[str] = Header(default=None, alias="v17_origin")) -> JSONResponse:
    global _ACTION_SEQ
    body_origin = str(payload.get("v17_origin", "")).strip()
    header_origin = str(v17_origin or "").strip()
    if not _sovereignty_v17(body_origin) and not _sovereignty_v17(header_origin):
        return JSONResponse({"ok": False, "detail": "v17_origin validation failed"}, status_code=403)
    signal = str(payload.get("signal", "")).strip().upper()
    action = str(payload.get("action", "")).strip()
    if signal not in {"ACTION_TAKEN", "INJECT_PATCH"} or not action:
        return JSONResponse({"ok": False, "detail": "invalid action signal"}, status_code=400)
    _ACTION_SEQ += 1
    session_id = str(payload.get("session_id", "")).strip() or "default"
    decision_id = str(payload.get("decision_id", "")).strip()
    event = {"signal": signal, "action": action, "ts": datetime.now(timezone.utc).isoformat(), "seq": _ACTION_SEQ, "session_id": session_id}
    kernel_dispatch_ok = True
    kernel_dispatch_detail = ""
    # V17.45: 全域因果调度 (SRC_MANUAL)
    if signal == "ACTION_TAKEN":
        from v17_rebirth.backend.logic.L1_atomic_ops.physics_kernel import PhysicsKernel
        try:
            current_physics = await get_state_backend().get_physics(session_id)
            if isinstance(current_physics, dict):
                pending = current_physics.get("pending_decisions")
                if isinstance(pending, list):
                    matched_decision = None
                    for item in pending:
                        if not isinstance(item, dict):
                            continue
                        item_id = str(item.get("id", "")).strip()
                        item_label = str(item.get("label", "")).strip()
                        item_title = str(item.get("title", "")).strip()
                        if (decision_id and item_id == decision_id) or action in {item_label, item_title}:
                            matched_decision = item
                            item["applied"] = True
                            break
                    if isinstance(matched_decision, dict):
                        if not isinstance(payload.get("physical_impact"), dict) and isinstance(matched_decision.get("physical_impact"), dict):
                            payload["physical_impact"] = matched_decision.get("physical_impact")
                        if not str(payload.get("target_god", "")).strip() and str(matched_decision.get("target_god", "")).strip():
                            payload["target_god"] = matched_decision.get("target_god")
                    await get_state_backend().set_physics(session_id, current_physics)
            kernel_dispatch_ok = await PhysicsKernel.dispatch_perturbation(
                session_id=session_id,
                source="SRC_MANUAL",
                payload={**payload, "reason": f"手动激活动作: {action}"}
            )
            if not kernel_dispatch_ok:
                kernel_dispatch_detail = "physics kernel rejected perturbation"
                _log.error(
                    "[V17-ACTION-REJECTED] session=%s action=%s detail=%s",
                    session_id,
                    action,
                    kernel_dispatch_detail,
                )
        except Exception as e:
            kernel_dispatch_ok = False
            kernel_dispatch_detail = str(e)
            _log.error(f"[V17-KERNEL-DISPATCH-FAIL] {e}")

    if signal == "ACTION_TAKEN" and not kernel_dispatch_ok:
        return JSONResponse(
            {
                "ok": False,
                "detail": kernel_dispatch_detail or "physics kernel dispatch failed",
                "signal": signal,
            },
            status_code=500,
        )

    # 发布原始事件（用于 Narrator 重启等逻辑）
    await get_state_backend().publish_action(session_id, event)
    return JSONResponse({"ok": True, "signal": signal, "will_proxy_delta": "aggressive" if any(k in action for k in ["进", "冲", "加码"]) else "stable"})


@router.post("/v17/freeze-report")
@router.post("/api/v17/freeze-report")
async def freeze_report(
    payload: Dict[str, Any],
    v17_origin_header: Optional[str] = Header(default=None, alias="v17_origin"),
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
