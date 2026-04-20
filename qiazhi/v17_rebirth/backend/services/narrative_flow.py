from __future__ import annotations

import asyncio
import re
from datetime import datetime, timezone
from typing import Any, AsyncIterator, Awaitable, Callable, Dict, List, Optional

from v17_rebirth.backend.narrative.NarrativeMappingEngine import NarrativeMappingEngine
from v17_rebirth.backend.narrative.pipeline import RealtimeNarrativePipeline
from v17_rebirth.backend.services.narrative_pipeline_cache import get_realtime_pipeline
from v17_rebirth.infrastructure.stream_interrupt import ActionInterruptDuringStream
from v17_rebirth.infrastructure.llm_micro_client import LlmStreamStep
from v17_rebirth.infrastructure.llm_bridge import V17LlmBridge


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


async def run_narrator_frames(
    *,
    raw_physics: Dict[str, Any],
    fragments: List[str],
    narrative_scores: Dict[str, float],
    decision_batches: Dict[str, Any],
    will_proxy: str,
    god_of_use: List[str],
    god_of_taboo: List[str],
    decision_anchor: str,
    user_message: str,
    action_signal: bool,
    role_style: str,
    session_id: str,
    causal_anchor: str,
    action_queue: Optional[asyncio.Queue[Dict[str, Any]]],
    stability_checked: bool = False,
    on_feedback_proposal: Optional[
        Callable[[str, str, str], Awaitable[None]]
    ] = None,
    model_hint: str = "",
    pipeline: RealtimeNarrativePipeline | None = None,
) -> AsyncIterator[Dict[str, Any]]:
    del stability_checked
    pipeline = get_realtime_pipeline() if pipeline is None else pipeline

    p_trace = {
        "causal_anchor": str(causal_anchor or "redis_sync"),
        "physics_fingerprint": "0",
    }
    try:
        import json

        p_trace["physics_fingerprint"] = str(
            abs(hash(json.dumps(raw_physics, ensure_ascii=False, sort_keys=True, default=str)))
        )
    except Exception:
        p_trace["physics_fingerprint"] = "0"

    partial_q: asyncio.Queue[str | LlmStreamStep] = asyncio.Queue()
    try:
        _model_hint = model_hint or str(V17LlmBridge().resolve().get("model") or "").strip()
    except Exception:
        _model_hint = model_hint

    async def on_partial(t: str) -> None:
        await partial_q.put(t)

    async def _on_llm_status(ev: Dict[str, Any]) -> None:
        st = str(ev.get("status") or "")
        if st == "dispatched":
            await partial_q.put(LlmStreamStep("dispatched", ev.get("payload")))
        elif st == "connected":
            await partial_q.put(
                LlmStreamStep("connected", {"latency_ms": int(ev.get("latency") or 0)}),
            )
        elif st == "streaming":
            ch = str(ev.get("chunk") or "")
            if ch:
                await partial_q.put(ch)

    async def _run_pipeline() -> Dict[str, Any]:
        return await pipeline.run(
            fact_fragments=fragments,
            physics_tensor=raw_physics if isinstance(raw_physics, dict) else None,
            session_id=str(session_id or ""),
            will_proxy=will_proxy,
            user_message=user_message,
            action_signal=action_signal,
            decision_anchor=decision_anchor,
            god_of_use=god_of_use,
            god_of_taboo=god_of_taboo,
            action_queue=None,
            on_llm_partial=on_partial,
            role_style=role_style,
            status_callback=_on_llm_status,
        )

    def _frame_dispatched(data: Any) -> Dict[str, Any]:
        return {
            "timestamp": _now_iso(),
            "layer": "SNAPSHOT",
            "payload": {
                "snapshot_kind": "llm_audit_dispatch",
                **p_trace,
                "render_text": "叙事引擎已离埠，请求正渡上游。",
                "will_proxy": str(will_proxy or "stable"),
                "ten_gods_narrative": narrative_scores,
                "god_rings": {"god_of_use": god_of_use, "god_of_taboo": god_of_taboo},
                "llm_meta": {
                    "audit_preview": True,
                    "engine_state": "dispatching",
                    "叙事节拍": "已派发",
                    "llm_request_messages": (data or {}).get("messages") or [],
                },
            },
        }

    def _frame_connected(payload: Any) -> Dict[str, Any]:
        p = payload if isinstance(payload, dict) else {}
        ms = int(p.get("latency_ms") or p.get("elapsed_ms") or 0)
        return {
            "timestamp": _now_iso(),
            "layer": "NARRATOR",
            "payload": {
                "render_text": f"上游已握手（{ms} 毫秒）。",
                "will_proxy": str(will_proxy or "stable"),
                "ten_gods_narrative": narrative_scores,
                "llm_meta": {
                    "stream_partial": True,
                    "叙事节拍": "已联通",
                    "毫秒": ms,
                    "model": _model_hint,
                },
                "source_facts": [],
                "god_rings": {"god_of_use": god_of_use, "god_of_taboo": god_of_taboo},
            },
        }

    audit_blob = pipeline.compute_llm_audit_preview(
        fact_fragments=fragments,
        physics_tensor=raw_physics if isinstance(raw_physics, dict) else None,
        session_id=str(session_id or ""),
        will_proxy=will_proxy,
        user_message=user_message,
        action_signal=action_signal,
        decision_anchor=decision_anchor,
        role_style=role_style,
    )
    try:
        _audit_rows = len(audit_blob.get("llm_request_messages") or [])
    except Exception:
        _audit_rows = 0
    print(
        f"[V17-NARRATOR] session={session_id or 'default'} audit_preview_ready role={role_style} facts={len(fragments)} messages={_audit_rows}",
        flush=True,
    )

    fpt = audit_blob.get("full_prompt_trace") if isinstance(audit_blob.get("full_prompt_trace"), dict) else {}
    fpt = {**fpt, **p_trace}
    yield {
        "timestamp": _now_iso(),
        "layer": "SNAPSHOT",
        "payload": {
            "snapshot_kind": "llm_audit_preview",
            **p_trace,
            "render_text": "引擎正在思考以下事实…",
            **audit_blob,
            "physics_report": NarrativeMappingEngine.build_physics_report_lines(raw_physics),
            "decision_batches": decision_batches.get("all", []),
            "decision_prompt_batches": decision_batches.get("prompt_lines", []),
            "ten_gods_narrative": narrative_scores,
            "full_prompt_trace": fpt,
            "will_proxy": str(will_proxy or "stable"),
            "god_rings": {"god_of_use": god_of_use, "god_of_taboo": god_of_taboo},
            "llm_meta": {
                "llm_audit_preview": True,
                "engine_state": "llm_audit_preview",
                "full_prompt_trace": fpt,
                "llm_system_prompt": str(audit_blob.get("llm_system_prompt") or ""),
                "llm_user_prompt": str(audit_blob.get("llm_user_prompt") or ""),
                "llm_request_messages": audit_blob.get("llm_request_messages") or [],
                **p_trace,
            },
        },
    }
    await asyncio.sleep(0)

    llm_task = asyncio.create_task(_run_pipeline())
    print(
        f"[V17-NARRATOR] session={session_id or 'default'} llm_task_started role={role_style} will={will_proxy}",
        flush=True,
    )
    streamed = False
    p_task: asyncio.Task | None = None
    a_task: asyncio.Task | None = None
    try:
        while not llm_task.done():
            if p_task is None:
                p_task = asyncio.create_task(partial_q.get())
            if a_task is None and action_queue is not None:
                a_task = asyncio.create_task(action_queue.get())

            wait_set = {p_task}
            if a_task:
                wait_set.add(a_task)
            done, _ = await asyncio.wait(wait_set, timeout=0.6, return_when=asyncio.FIRST_COMPLETED)

            for t in done:
                res = t.result()
                if t == p_task:
                    p_task = None
                    if isinstance(res, LlmStreamStep):
                        if res.kind == "dispatched":
                            print(f"[V17-NARRATOR] session={session_id or 'default'} step=dispatched", flush=True)
                            yield _frame_dispatched(res.data)
                        elif res.kind == "connected":
                            print(f"[V17-NARRATOR] session={session_id or 'default'} step=connected", flush=True)
                            yield _frame_connected(res.data)
                        continue
                    chunk = str(res)
                    if chunk:
                        print(
                            f"[V17-NARRATOR] session={session_id or 'default'} step=streaming chars={len(chunk)}",
                            flush=True,
                        )
                        streamed = True
                        if "[" in chunk and "]" in chunk:
                            m = re.search(r"\[(INTENSIFY|WEAKEN):([a-zA-Z\u4e00-\u9fa5]{1,2})\]", chunk)
                            if m and on_feedback_proposal is not None:
                                at, el = m.groups()
                                await on_feedback_proposal(at, el, f"叙事洞察: {el}势态变化")
                        yield {
                            "timestamp": _now_iso(), "layer": "NARRATOR",
                            "payload": {
                                "render_text": chunk, "will_proxy": str(will_proxy or "stable"),
                                "ten_gods_narrative": narrative_scores,
                                "llm_meta": {"stream_partial": True, "model": _model_hint},
                                "source_facts": [],
                                "god_rings": {"god_of_use": god_of_use, "god_of_taboo": god_of_taboo},
                            },
                        }
                elif t == a_task:
                    a_task = None
                    if isinstance(res, dict) and res.get("signal") in {"PHYSICS_UPDATE", "PHYSICS_SYNC"}:
                        yield {
                            "timestamp": _now_iso(), "layer": "SNAPSHOT",
                            "payload": {
                                "render_text": "物理同步中…", "type": "PHYSICS_SYNC",
                                **(res.get("payload") if isinstance(res, dict) else {}),
                            },
                        }
                    else:
                        llm_task.cancel()
                        raise ActionInterruptDuringStream(res)
    finally:
        if p_task:
            p_task.cancel()
        if a_task:
            a_task.cancel()
        if not llm_task.done():
            llm_task.cancel()
        try:
            await llm_task
        except Exception:
            pass

    while not partial_q.empty():
        try:
            res = partial_q.get_nowait()
            if isinstance(res, LlmStreamStep):
                if res.kind == "dispatched":
                    yield _frame_dispatched(res.data)
                elif res.kind == "connected":
                    yield _frame_connected(res.data)
                continue
            chunk = str(res)
            if chunk:
                streamed = True
                yield {
                    "timestamp": _now_iso(),
                    "layer": "NARRATOR",
                    "payload": {
                        "render_text": chunk, "will_proxy": str(will_proxy or "stable"),
                        "ten_gods_narrative": narrative_scores,
                        "llm_meta": {"stream_partial": True, "model": _model_hint},
                        "source_facts": [],
                        "god_rings": {"god_of_use": god_of_use, "god_of_taboo": god_of_taboo},
                    },
                }
        except Exception:
            break

    exc = llm_task.exception()
    if exc is not None:
        print(f"[V17-NARRATOR] session={session_id or 'default'} llm_task_exception={type(exc).__name__}", flush=True)
        raise exc
    frame = llm_task.result()
    print(f"[V17-NARRATOR] session={session_id or 'default'} llm_task_done streamed={streamed}", flush=True)
    text = str(((frame.get("payload") or {}).get("render_text") or "")).strip()
    llm_meta = (frame.get("payload") or {}).get("llm_meta", {})
    source_facts = (frame.get("payload") or {}).get("source_facts", [])
    if not text:
        err = str((llm_meta or {}).get("error") or "").strip()
        eid = str((llm_meta or {}).get("error_id") or "").strip()
        hint = (
            "[叙事织机未产出可见正文] "
            + (f"上游：{err} " if err else "")
            + (f"[{eid}] " if eid else "")
            + "请确认本机 Ollama/LLM 已启动、模型已拉取，且 `llm_node.json` 或环境变量中的 base_url、model 正确。"
        ).strip()
        yield {
            "timestamp": _now_iso(),
            "layer": "NARRATOR",
            "payload": {
                "render_text": hint,
                "will_proxy": str(will_proxy or "stable"),
                "ten_gods_narrative": narrative_scores,
                "llm_meta": {
                    **(llm_meta if isinstance(llm_meta, dict) else {}),
                    "ok": False,
                    "engine_state": str((llm_meta or {}).get("engine_state") or "empty_render"),
                    "empty_pipeline_render": True,
                },
                "source_facts": source_facts if isinstance(source_facts, list) else [],
                "god_rings": {"god_of_use": god_of_use, "god_of_taboo": god_of_taboo},
            },
        }
        return
    if streamed:
        yield {
            "timestamp": _now_iso(),
            "layer": "NARRATOR",
            "payload": {
                "render_text": text,
                "will_proxy": str(will_proxy or "stable"),
                "ten_gods_narrative": narrative_scores,
                "llm_meta": llm_meta if isinstance(llm_meta, dict) else {},
                "source_facts": source_facts if isinstance(source_facts, list) else [],
                "god_rings": {"god_of_use": god_of_use, "god_of_taboo": god_of_taboo},
            },
        }
        return
    step = max(6, min(14, len(text) // 4 if len(text) > 24 else 8))
    for i in range(step, len(text) + step, step):
        yield {
            "timestamp": _now_iso(),
            "layer": "NARRATOR",
            "payload": {
                "render_text": text[: min(i, len(text))],
                "will_proxy": str(will_proxy or "stable"),
                "ten_gods_narrative": narrative_scores,
                "llm_meta": llm_meta if isinstance(llm_meta, dict) else {},
                "source_facts": source_facts if isinstance(source_facts, list) else [],
                "god_rings": {"god_of_use": god_of_use, "god_of_taboo": god_of_taboo},
            },
        }
