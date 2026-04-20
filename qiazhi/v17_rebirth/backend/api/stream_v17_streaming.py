from __future__ import annotations

import json
import asyncio
from datetime import datetime, timezone
from typing import Any, AsyncIterator, Dict, List, Optional
import os
import logging

from v17_rebirth.infrastructure.stream_interrupt import ActionInterruptDuringStream
from v17_rebirth.infrastructure.state_backend import RedisStateBackend, get_state_backend
from v17_rebirth.infrastructure.llm_bridge import V17_ROLE_JUDGE, V17_ROLE_WEAVER
from v17_rebirth.backend.logic.L1_atomic_ops.l1_meta_hydration import hydrate_v17_physics_tensor
from v17_rebirth.backend.services.physics_service import DataSovereigntyError, PhysicsService
from v17_rebirth.backend.services.verdict_orchestrator import VerdictOrchestrator
from v17_rebirth.backend.api.stream_v17_decision_flow import boolish


_log = logging.getLogger(__name__)


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
                "engine_state": "system_init_failure",
                "visibility_lock": True,
                "data_sovereignty": True,
            },
        },
    }


async def hydrate_physics_atomically(pl: Dict[str, Any]) -> None:
    """在发出任何 SNAPSHOT(physics) 之前，于线程中完成 meta 张量注水，与 HTTP 响应流解耦。"""

    def _sync() -> None:
        hydrate_v17_physics_tensor(pl)

    await asyncio.to_thread(_sync)


async def self_heal_physics_if_missing(session_id: str, pl: Dict[str, Any], run_physics_core, parse_birth_time) -> bool:
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
    healed_payload = run_physics_core(
        birth_time=parse_birth_time(str(pl.get("birth_time") or "").strip() or None),
        gender=str(pl.get("gender") or "").strip() or None,
        flow_year=healed_flow_year,
    )
    pl.update(healed_payload)
    PhysicsService.prime_local_tensor(session_id, pl)
    await hydrate_physics_atomically(pl)
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


def _build_will_flash(action: str, proxy: str) -> Dict[str, Any]:
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "layer": "WILL_FLASH",
        "payload": {
            "signal": "ACTION_TAKEN",
            "action": action,
            "will_proxy": proxy,
            "will_flash": True,
        },
    }


async def _narrator_with_heartbeat(
    agen: AsyncIterator[Dict[str, Any]],
) -> AsyncIterator[Dict[str, Any]]:
    """在 async for 迭代上包一层：超过间隔无帧则下发 HEARTBEAT（含步进位置）。"""
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


def _event_for_publish(event: Dict[str, Any], *, physics_tensor: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(event)
    request_verdict = boolish(out.get("request_verdict"), default=True)
    if request_verdict:
        return out
    out["signal"] = "PHYSICS_SYNC"
    out["payload"] = {
        "type": "PHYSICS_SYNC",
        "decision_inbox_contract": str(physics_tensor.get("decision_inbox_contract") or "v17.decision.inbox.v2"),
        "pending_decisions": [dict(x) for x in physics_tensor.get("pending_decisions", []) if isinstance(x, dict)],
        "manual_decisions": [dict(x) for x in physics_tensor.get("manual_decisions", []) if isinstance(x, dict)],
        "manual_inbox": [dict(x) for x in physics_tensor.get("manual_decisions", []) if isinstance(x, dict)],
        "auto_decisions": [dict(x) for x in physics_tensor.get("auto_decisions", []) if isinstance(x, dict)]
        or [dict(x) for x in physics_tensor.get("auto_resolutions", []) if isinstance(x, dict)]
        or [dict(x) for x in physics_tensor.get("llm_arbitration_context", []) if isinstance(x, dict)],
        "auto_resolutions": [dict(x) for x in physics_tensor.get("auto_resolutions", []) if isinstance(x, dict)],
        "llm_arbitration_context": [dict(x) for x in physics_tensor.get("llm_arbitration_context", []) if isinstance(x, dict)],
        "decision_brain_state": dict(physics_tensor.get("decision_brain_state") or {}),
        "decision_batches": [dict(x) for x in physics_tensor.get("decision_batches_cache", []) if isinstance(x, dict)],
    }
    return out


async def stream_frames(*, will_proxy: str, payload: Dict[str, Any], run_physics_core) -> AsyncIterator[bytes]:
    orchestrator = VerdictOrchestrator()
    pl = payload if isinstance(payload, dict) else {}
    session_id = str(pl.get("session_id", "")).strip() or "default"
    print(f"[V17-TRACE] Stream Request In: {session_id}", flush=True)

    backend = get_state_backend()
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

    await hydrate_physics_atomically(pl)
    PhysicsService.prime_local_tensor(session_id, pl)
    try:
        orchestrator.assert_six_pillars_physics(pl)
    except DataSovereigntyError:
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
            healed = await self_heal_physics_if_missing(session_id, raw_physics, run_physics_core=run_physics_core, parse_birth_time=_parse_iso_timestamp)
        except DataSovereigntyError:
            healed = False
        if not healed:
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

    if boolish(pl.get("suppress_narrator"), default=False):
        _log.info("[V17-SYNC-ONLY] session=%s suppress_narrator=true", session_id)
        return

    facts = pl.get("facts") if isinstance(pl.get("facts"), list) else []
    dec_raw = pl.get("pending_decisions") if isinstance(pl.get("pending_decisions"), list) else []
    if not dec_raw:
        dec_raw = pl.get("decisions") if isinstance(pl.get("decisions"), list) else []

    decisions_rows: List[Dict[str, Any]] = []
    for x in dec_raw:
        if not isinstance(x, dict):
            continue
        lab = str(x.get("label") or x.get("title") or "").strip()
        if lab:
            decisions_rows.append({"id": str(x.get("id") or "").strip(), "label": lab, "title": str(x.get("title") or "").strip()})
    narrative_role = V17_ROLE_JUDGE if decisions_rows else V17_ROLE_WEAVER

    async with get_state_backend().subscribe_actions(session_id) as queue:
        _log.warning("[Narrator-Start] session=%s causal_anchor=redis_sync", session_id)
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
                yield (json.dumps(_build_will_flash(current_user_message, current_proxy), ensure_ascii=False) + "\n").encode("utf-8")
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


def _parse_iso_timestamp(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    raw = str(value).strip()
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None

