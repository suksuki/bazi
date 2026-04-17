from __future__ import annotations

from dataclasses import dataclass
import asyncio
from datetime import datetime, timezone
from typing import Any, AsyncIterator, Dict, List, Optional

from v17_rebirth.backend.adapters.physics_adapter import PhysicsAdapter
from v17_rebirth.backend.logic.L1_atomic_ops.l1_meta_hydration import hydrate_v17_physics_tensor
from v17_rebirth.backend.logic import plugin_discovery as logic_pd
from v17_rebirth.backend.services.auto_scanner import AutoScanner
from v17_rebirth.backend.plugins.spec import V17Fact
from v17_rebirth.backend.plugins.v17_wrappers import (
    collect_pending_decisions_from_specs,
    v17_decision_to_row,
    v17_fact_to_row,
)
from v17_rebirth.backend.narrative.pipeline import DialogueLayer, RealtimeNarrativePipeline
from v17_rebirth.backend.narrative.sanitizer import NarrativeSanitizer
from v17_rebirth.backend.narrative.semantic_fusion import SemanticFusion
from v17_rebirth.infrastructure.llm_bridge import V17_ROLE_JUDGE, V17_ROLE_WEAVER, V17LlmBridge, get_runtime_revision
from v17_rebirth.infrastructure.llm_micro_client import LlmStreamStep, V17MicroLlmClient, _normalize_fuse_role
from v17_rebirth.infrastructure.stream_interrupt import ActionInterruptDuringStream
from v17_rebirth.backend.services.physics_canonical import six_pillars_tensor_complete
from v17_rebirth.backend.services.physics_service import DataSovereigntyError, PhysicsService

_PIPELINE_EPOCH = 0
_PIPELINE_CACHE: RealtimeNarrativePipeline | None = None
_PIPELINE_CACHE_KEY: tuple[int, int] | None = None


def _six_pillars_physics_ok(raw_physics: Dict[str, Any]) -> bool:
    """四柱 + 大运 + 流年（委托元数据中心）。"""
    return six_pillars_tensor_complete(raw_physics)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def restart_realtime_pipeline() -> dict[str, int]:
    global _PIPELINE_EPOCH, _PIPELINE_CACHE, _PIPELINE_CACHE_KEY
    _PIPELINE_EPOCH += 1
    _PIPELINE_CACHE = None
    _PIPELINE_CACHE_KEY = None
    return {"pipeline_epoch": _PIPELINE_EPOCH}


def _get_pipeline() -> RealtimeNarrativePipeline:
    global _PIPELINE_CACHE, _PIPELINE_CACHE_KEY
    key = (_PIPELINE_EPOCH, get_runtime_revision())
    if _PIPELINE_CACHE is None or _PIPELINE_CACHE_KEY != key:
        _PIPELINE_CACHE = RealtimeNarrativePipeline(
            sanitizer=NarrativeSanitizer(),
            fusion=SemanticFusion(llm_client=V17MicroLlmClient(bridge=V17LlmBridge())),
            dialogue=DialogueLayer(sanitizer=NarrativeSanitizer()),
        )
        _PIPELINE_CACHE_KEY = key
    return _PIPELINE_CACHE


@dataclass
class VerdictOrchestrator:
    repo_root: str = "/home/hlsystem/bazi"

    def _six_pillars_physics_ok(self, raw_physics: Any) -> bool:
        pt = raw_physics if isinstance(raw_physics, dict) else {}
        return _six_pillars_physics_ok(pt)

    def assert_six_pillars_physics(self, raw_physics: Any) -> None:
        """物理门控：未对齐则抛 DataSovereigntyError，切断 LLM 通道。"""
        if not self._six_pillars_physics_ok(raw_physics):
            raise DataSovereigntyError("物理因果未对齐")

    def _resolve_pattern(self, deity_scores: Dict[str, float]) -> str:
        if not deity_scores:
            return "未定格"
        top = sorted(deity_scores.items(), key=lambda kv: kv[1], reverse=True)
        name, score = top[0]
        if name == "正官" and score >= 40:
            return "正官格势强"
        if name in {"食神", "伤官"} and score >= 35:
            return "食伤外放格"
        if name in {"偏财", "正财"} and score >= 35:
            return "财星主导格"
        return f"{name}主轴格"

    def _build_fragments(self, deity_scores: Dict[str, float], facts: List[str], pattern: str) -> List[str]:
        ranked = sorted(deity_scores.items(), key=lambda kv: kv[1], reverse=True)
        lead = [f"{k}偏强" for k, _ in ranked[:2]]
        return [
            f"当前格局：{pattern}",
            ("、".join(lead) + "，局势进入再平衡阶段") if lead else "当前能量分布尚在收敛",
            *[str(x) for x in facts[:48]],
        ]

    def _pending_decisions(
        self,
        raw_physics: Dict[str, Any],
        _deity_scores: Dict[str, float],
        *,
        spec_facts: List[V17Fact] | None = None,
    ) -> List[Dict[str, Any]]:
        sanitizer = NarrativeSanitizer()
        if spec_facts is None:
            pt = raw_physics if isinstance(raw_physics, dict) else {}
            spec_facts = logic_pd.collect_all_spec_facts_and_record(pt)
        spec_decisions = [v17_decision_to_row(d) for d in collect_pending_decisions_from_specs(spec_facts)]
        for d in spec_decisions:
            d["label"] = sanitizer.sanitize(str(d.get("label", "")))
            d["title"] = sanitizer.sanitize(str(d.get("title", "")))

        merged: List[Dict[str, Any]] = list(spec_decisions)
        merged.sort(key=lambda x: float(x.get("priority", 0.0)), reverse=True)
        seen: set[str] = set()
        deduped: List[Dict[str, Any]] = []
        for item in merged:
            key = f"{item.get('source','')}|{item.get('label','')}"
            if key in seen:
                continue
            seen.add(key)
            deduped.append(item)
        return deduped[:64]

    def snapshot_frame(self, *, raw_physics: Dict[str, Any], session_id: str = "") -> Dict[str, Any]:
        AutoScanner.ensure_loaded()
        if isinstance(raw_physics, dict):
            hydrate_v17_physics_tensor(raw_physics)
        self.assert_six_pillars_physics(raw_physics)
        adapter = PhysicsAdapter(root=__import__("pathlib").Path(self.repo_root))
        scores = adapter.read_deity_scores(raw_physics)
        ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
        god_of_use = [x[0] for x in ranked[:2]]
        god_of_taboo = [x[0] for x in ranked[-2:]] if len(ranked) >= 2 else []
        pattern = self._resolve_pattern(scores)
        tension = (max(scores.values()) - min(scores.values())) if scores else 0.0
        pt = raw_physics if isinstance(raw_physics, dict) else {}
        if isinstance(pt.get("meta"), dict) and pt["meta"].get("hit_pattern_name"):
            pattern = str(pt["meta"]["hit_pattern_name"])
        spec_facts = logic_pd.collect_all_spec_facts_and_record(pt)
        spec_rows = [v17_fact_to_row(f) for f in spec_facts]
        plugin_rows = spec_rows
        plugin_facts = [str(x.get("fact", "")).strip() for x in plugin_rows if str(x.get("fact", "")).strip()]
        plugin_hits = sorted({str(x.get("plugin", "")).strip() for x in plugin_rows if str(x.get("plugin", "")).strip()})
        decisions = self._pending_decisions(raw_physics, scores, spec_facts=spec_facts)
        fact_list = raw_physics.get("facts") if isinstance(raw_physics.get("facts"), list) else []
        facts_out = [str(x).strip() for x in fact_list if str(x).strip()][:160]
        inner: Dict[str, Any] = {
            "snapshot_kind": "physics",
            "snapshot_contract": "v17.21_full_physics",
            "physics_validation": {"state": "aligned", "gate": "six_pillars"},
            "render_text": f"格局快照已同步：{pattern}",
            "pattern": pattern,
            "four_pillars": raw_physics.get("four_pillars", {}),
            "luck_pillar": raw_physics.get("luck_pillar"),
            "flow_pillar": raw_physics.get("flow_pillar"),
            "flow_year": raw_physics.get("flow_year"),
            "ten_gods": raw_physics.get("ten_gods", []),
            "deity_scores": scores,
            "physics_tension": tension,
            "pending_decisions": decisions,
            "facts": facts_out,
            "plugins": {
                "hits": list(plugin_hits),
                "rows": plugin_rows[:128],
            },
            "debug_trace": {
                "hits": plugin_hits,
                "facts": plugin_facts[:64],
            },
            "god_rings": {
                "god_of_use": god_of_use,
                "god_of_taboo": god_of_taboo,
            },
        }
        sid = str(session_id or "").strip()
        if sid:
            cols = PhysicsService.get_current_pillars(sid)
            fp = cols.get("four_pillars") if isinstance(cols.get("four_pillars"), dict) else {}
            inner["four_pillars"] = dict(fp)
            inner["luck_pillar"] = cols.get("luck_pillar")
            inner["flow_pillar"] = cols.get("flow_pillar")
            if cols.get("flow_year") is not None:
                inner["flow_year"] = cols.get("flow_year")
        inner["pillars"] = {
            "four_pillars": dict(inner.get("four_pillars") or {}),
            "luck_pillar": inner.get("luck_pillar"),
            "flow_pillar": inner.get("flow_pillar"),
            "flow_year": inner.get("flow_year"),
        }
        _gate = {
            "four_pillars": inner.get("four_pillars"),
            "luck_pillar": inner.get("luck_pillar"),
            "flow_pillar": inner.get("flow_pillar"),
        }
        if not six_pillars_tensor_complete(_gate):
            raise DataSovereigntyError("physics_incomplete_snapshot_denied")
        return {"timestamp": _now_iso(), "layer": "SNAPSHOT", "payload": inner}

    async def narrator_frames(
        self,
        *,
        raw_physics: Dict[str, Any],
        facts: List[str],
        will_proxy: str,
        user_message: str = "",
        action_signal: bool = False,
        decision_anchor: str = "",
        action_queue: Optional[asyncio.Queue[Dict[str, Any]]] = None,
        role_style: str = V17_ROLE_WEAVER,
        decisions: Optional[List[Dict[str, Any]]] = None,
        session_id: str = "",
    ) -> AsyncIterator[Dict[str, Any]]:
        if isinstance(raw_physics, dict):
            hydrate_v17_physics_tensor(raw_physics)
        self.assert_six_pillars_physics(raw_physics)
        await PhysicsService.ensure_stability(str(session_id or "").strip() or "default")
        adapter = PhysicsAdapter(root=__import__("pathlib").Path(self.repo_root))
        scores = adapter.read_deity_scores(raw_physics)
        ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
        god_of_use = [x[0] for x in ranked[:2]]
        god_of_taboo = [x[0] for x in ranked[-2:]] if len(ranked) >= 2 else []
        pattern = self._resolve_pattern(scores)
        if isinstance(raw_physics, dict):
            meta = raw_physics.get("meta") if isinstance(raw_physics.get("meta"), dict) else {}
            if meta.get("hit_pattern_name"):
                pattern = str(meta["hit_pattern_name"])

        def _merge_rows() -> List[Dict[str, Any]]:
            pt = raw_physics if isinstance(raw_physics, dict) else {}
            return [v17_fact_to_row(f) for f in logic_pd.collect_all_spec_facts_and_record(pt)]

        plugin_rows = await asyncio.to_thread(_merge_rows)
        plugin_facts = [str(x.get("fact", "")).strip() for x in plugin_rows if str(x.get("fact", "")).strip()]
        fragments = self._build_fragments(scores, [*facts, *plugin_facts], pattern)
        rid = _normalize_fuse_role(str(role_style or V17_ROLE_WEAVER))
        if rid == V17_ROLE_JUDGE:
            for d in (decisions or [])[:32]:
                if not isinstance(d, dict):
                    continue
                lab = str(d.get("label") or d.get("title") or "").strip()
                if lab:
                    fragments.append(f"圣殿裁决线索（已入账）：{lab}")
        pipeline = _get_pipeline()
        partial_q: asyncio.Queue[str | LlmStreamStep] = asyncio.Queue()
        try:
            _model_hint = str(V17LlmBridge().resolve().get("model") or "").strip()
        except Exception:
            _model_hint = ""

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

        def _frame_dispatched(data: Any) -> Dict[str, Any]:
            return {
                "timestamp": _now_iso(),
                "layer": "SNAPSHOT",
                "payload": {
                    "snapshot_kind": "AUDIT_PREVIEW",
                    "render_text": "叙事引擎已离埠，请求正渡上游。",
                    "will_proxy": str(will_proxy or "stable"),
                    "god_rings": {"god_of_use": god_of_use, "god_of_taboo": god_of_taboo},
                    "llm_meta": {
                        "audit_preview": True,
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

        async def _run_pipeline() -> Dict[str, Any]:
            # Action 队列仅在下方「并发监听」中消费；勿传入 fuse，避免与 LLM 推理争用同一 Queue。
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
                role_style=rid,
                status_callback=_on_llm_status,
            )

        audit_blob = pipeline.compute_llm_audit_preview(
            fact_fragments=fragments,
            physics_tensor=raw_physics if isinstance(raw_physics, dict) else None,
            session_id=str(session_id or ""),
            will_proxy=will_proxy,
            user_message=user_message,
            action_signal=action_signal,
            decision_anchor=decision_anchor,
            role_style=rid,
        )
        fpt = audit_blob.get("full_prompt_trace") if isinstance(audit_blob.get("full_prompt_trace"), dict) else {}
        # 预发审计帧：在 await pipeline.run() 启动之前下发，前端可先见 full_prompt_trace（LLM 失败亦有据可查）。
        yield {
            "timestamp": _now_iso(),
            "layer": "SNAPSHOT",
            "payload": {
                "snapshot_kind": "llm_audit_preview",
                "render_text": "引擎正在思考以下事实…",
                **audit_blob,
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
                },
            },
        }
        await asyncio.sleep(0)

        llm_task = asyncio.create_task(_run_pipeline())
        streamed = False
        while not llm_task.done():
            if action_queue is None:
                try:
                    item = await asyncio.wait_for(partial_q.get(), timeout=0.05)
                except asyncio.TimeoutError:
                    await asyncio.sleep(0.003)
                    continue
                if isinstance(item, LlmStreamStep):
                    streamed = True
                    if item.kind == "dispatched":
                        yield _frame_dispatched(item.data)
                    elif item.kind == "connected":
                        yield _frame_connected(item.data)
                    continue
                chunk = str(item)
            else:
                # 并发：叙事 partial 与 Action 队列；先完成的一侧获胜，ACTION 则 cancel LLM。
                p_task = asyncio.create_task(partial_q.get())
                a_task = asyncio.create_task(action_queue.get())
                done_set, _pend = await asyncio.wait(
                    {p_task, a_task}, timeout=0.05, return_when=asyncio.FIRST_COMPLETED
                )
                if a_task in done_set and a_task.done():
                    ev = a_task.result()
                    if p_task not in done_set or not p_task.done():
                        p_task.cancel()
                        try:
                            await p_task
                        except asyncio.CancelledError:
                            pass
                    else:
                        try:
                            p_task.result()
                        except Exception:
                            pass
                    llm_task.cancel()
                    try:
                        await llm_task
                    except asyncio.CancelledError:
                        pass
                    except Exception:
                        pass
                    raise ActionInterruptDuringStream(ev)
                if p_task in done_set and p_task.done():
                    item = p_task.result()
                    if isinstance(item, LlmStreamStep):
                        if not a_task.done():
                            a_task.cancel()
                            try:
                                await a_task
                            except asyncio.CancelledError:
                                pass
                        streamed = True
                        if item.kind == "dispatched":
                            yield _frame_dispatched(item.data)
                        elif item.kind == "connected":
                            yield _frame_connected(item.data)
                        continue
                    chunk = str(item)
                    if not a_task.done():
                        a_task.cancel()
                        try:
                            await a_task
                        except asyncio.CancelledError:
                            pass
                    else:
                        ev = a_task.result()
                        llm_task.cancel()
                        try:
                            await llm_task
                        except asyncio.CancelledError:
                            pass
                        except Exception:
                            pass
                        raise ActionInterruptDuringStream(ev)
                else:
                    for p in (p_task, a_task):
                        if not p.done():
                            p.cancel()
                        try:
                            await p
                        except asyncio.CancelledError:
                            pass
                    await asyncio.sleep(0.003)
                    continue
            streamed = True
            yield {
                "timestamp": _now_iso(),
                "layer": "NARRATOR",
                "payload": {
                    "render_text": chunk,
                    "will_proxy": str(will_proxy or "stable"),
                    "llm_meta": {"stream_partial": True, "model": _model_hint},
                    "source_facts": [],
                    "god_rings": {"god_of_use": god_of_use, "god_of_taboo": god_of_taboo},
                },
            }
        while True:
            try:
                item = partial_q.get_nowait()
            except asyncio.QueueEmpty:
                break
            if isinstance(item, LlmStreamStep):
                streamed = True
                if item.kind == "dispatched":
                    yield _frame_dispatched(item.data)
                elif item.kind == "connected":
                    yield _frame_connected(item.data)
                continue
            chunk = str(item)
            streamed = True
            yield {
                "timestamp": _now_iso(),
                "layer": "NARRATOR",
                "payload": {
                    "render_text": chunk,
                    "will_proxy": str(will_proxy or "stable"),
                    "llm_meta": {"stream_partial": True, "model": _model_hint},
                    "source_facts": [],
                    "god_rings": {"god_of_use": god_of_use, "god_of_taboo": god_of_taboo},
                },
            }
        exc = llm_task.exception()
        if exc is not None:
            raise exc
        frame = llm_task.result()
        text = str((((frame.get("payload") or {}).get("render_text")) or "")).strip()
        llm_meta = (frame.get("payload") or {}).get("llm_meta", {})
        source_facts = (frame.get("payload") or {}).get("source_facts", [])
        if not text:
            # 此前静默 return：前端永远停在「连接叙事引擎」，因果面板 LLM 正文也为空。
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
                    "llm_meta": llm_meta if isinstance(llm_meta, dict) else {},
                    "source_facts": source_facts if isinstance(source_facts, list) else [],
                    "god_rings": {"god_of_use": god_of_use, "god_of_taboo": god_of_taboo},
                },
            }
