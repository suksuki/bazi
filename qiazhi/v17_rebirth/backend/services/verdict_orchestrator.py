from __future__ import annotations

from dataclasses import dataclass, field
import asyncio
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, AsyncIterator, Dict, List, Optional

from v17_rebirth.backend.adapters.physics_adapter import PhysicsAdapter
from v17_rebirth.backend.logic.L1_atomic_ops.l1_meta_hydration import hydrate_v17_physics_tensor
from v17_rebirth.backend.logic import plugin_discovery as logic_pd
from v17_rebirth.backend.services.auto_scanner import AutoScanner
from v17_rebirth.backend.plugins.spec import V17Fact
from v17_rebirth.backend.plugins.v17_wrappers import (
    collect_pending_decisions_from_specs,
    v17_fact_to_row,
)
from v17_rebirth.backend.services.decision_compiler import compile_decision_arbitration
from v17_rebirth.backend.narrative.pipeline import DialogueLayer, RealtimeNarrativePipeline
from v17_rebirth.backend.narrative.NarrativeMappingEngine import NarrativeMappingEngine
from v17_rebirth.backend.narrative.sanitizer import NarrativeSanitizer
from v17_rebirth.backend.narrative.semantic_fusion import SemanticFusion
from v17_rebirth.infrastructure.llm_bridge import V17_ROLE_JUDGE, V17_ROLE_WEAVER, V17LlmBridge, get_runtime_revision
from v17_rebirth.infrastructure.llm_micro_client import LlmStreamStep, V17MicroLlmClient, _normalize_fuse_role
from v17_rebirth.infrastructure.stream_interrupt import ActionInterruptDuringStream
from v17_rebirth.backend.services.physics_canonical import six_pillars_tensor_complete
from v17_rebirth.backend.services.physics_layers import build_narrative_scores, read_base_scores, read_runtime_scores
from v17_rebirth.backend.services.physics_service import DataSovereigntyError, PhysicsService

_PIPELINE_EPOCH = 0
_PIPELINE_CACHE: RealtimeNarrativePipeline | None = None
_PIPELINE_CACHE_KEY: tuple[int, int] | None = None


async def _queue_llm_feedback_proposal(
    *,
    session_id: str,
    raw_physics: Dict[str, Any],
    tag: str,
    element_or_god: str,
    reason: str,
) -> None:
    from v17_rebirth.infrastructure.state_backend import get_state_backend

    pt = raw_physics if isinstance(raw_physics, dict) else {}
    queue = pt.get("pending_proposals")
    if not isinstance(queue, list):
        queue = []
        pt["pending_proposals"] = queue
    proposal = {
        "id": f"llm_feedback_{tag.lower()}_{element_or_god}_{len(queue)}",
        "source": "llm_feedback",
        "arbiter_type": "llm",
        "status": "pending",
        "tag": str(tag).strip().upper(),
        "target_node": str(element_or_god).strip(),
        "reason": str(reason).strip(),
        "weight": 0.0,
    }
    queue.append(proposal)
    if str(session_id or "").strip():
        try:
            await get_state_backend().set_physics(str(session_id), pt)
        except Exception:
            pass


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
    repo_root: str = field(default_factory=lambda: str(Path(__file__).resolve().parents[3]))

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

    def _fact_row(self, item: Any) -> Dict[str, Any]:
        if isinstance(item, dict):
            text = str(item.get("fact") or item.get("text") or "").strip()
            try:
                weight = float(item.get("weight", item.get("salience_weight", 0.5)) or 0.5)
            except (TypeError, ValueError):
                weight = 0.5
            return {"fact": text, "weight": max(0.0, min(1.0, weight))}
        text = str(item or "").strip()
        return {"fact": text, "weight": 0.5 if text else 0.0}

    def _sorted_fact_rows(self, facts: List[Any]) -> List[Dict[str, Any]]:
        rows = [self._fact_row(x) for x in facts]
        rows = [r for r in rows if r.get("fact")]
        rows.sort(key=lambda x: float(x.get("weight", 0.0)), reverse=True)
        return rows[:80] if len(rows) > 100 else rows

    def _build_fragments(
        self,
        deity_scores: Dict[str, float],
        facts: List[Any],
        pattern: str,
        *,
        total_energy_index: float = 0.0,
    ) -> List[str]:
        ranked = sorted(deity_scores.items(), key=lambda kv: kv[1], reverse=True)
        lead = [f"{k}偏强" for k, _ in ranked[:2]]
        sorted_rows = self._sorted_fact_rows(facts)
        top10 = [str(x.get("fact") or "") for x in sorted_rows[:10] if str(x.get("fact") or "").strip()]
        tail_anchor = [str(x.get("fact") or "") for x in sorted_rows[:3] if str(x.get("fact") or "").strip()]
        middle = [str(x.get("fact") or "") for x in sorted_rows[10:] if str(x.get("fact") or "").strip()]
        tail_anchor = [x for x in tail_anchor if x not in top10 and x not in middle]
        energy_hint = (
            f"当前十神能量为绝对物理强度，Total Energy Index={total_energy_index:.2f}。"
            "若总能量偏低，应偏向漂泊、谨慎；若总能量偏高，应偏向刚毅、掌控。"
        )
        return [
            "以下提供的 160 条事实已按显著性（Salience）降序排列。排序越靠前的事实对命局的影响越具决定性。请务必优先回应前 10 条核心事实，将其作为你裁决的第一物理支点。",
            f"当前格局：{pattern}",
            energy_hint,
            ("、".join(lead) + "，局势进入再平衡阶段") if lead else "当前能量分布尚在收敛",
            *top10,
            *middle,
            *tail_anchor,
        ]

    def _physics_trace(self, raw_physics: Dict[str, Any], *, causal_anchor: str) -> Dict[str, Any]:
        pt = raw_physics if isinstance(raw_physics, dict) else {}
        try:
            fingerprint = str(abs(hash(json.dumps(pt, ensure_ascii=False, sort_keys=True, default=str))))
        except Exception:
            fingerprint = "0"
        return {
            "causal_anchor": str(causal_anchor or "local_memory"),
            "physics_fingerprint": fingerprint,
        }

    def _decision_arbitration(
        self,
        raw_physics: Dict[str, Any],
        _deity_scores: Dict[str, float],
        *,
        spec_facts: List[V17Fact] | None = None,
    ) -> Dict[str, List[Dict[str, Any]]]:
        sanitizer = NarrativeSanitizer()
        if spec_facts is None:
            pt = raw_physics if isinstance(raw_physics, dict) else {}
            spec_facts = logic_pd.collect_all_spec_facts_and_record(pt)
        raw_pending = raw_physics.get("pending_decisions") if isinstance(raw_physics.get("pending_decisions"), list) else []
        arbitration = compile_decision_arbitration(
            facts=spec_facts,
            spec_decisions=collect_pending_decisions_from_specs(spec_facts),
            existing_rows=[dict(item) for item in raw_pending if isinstance(item, dict)],
            physics_tensor=raw_physics,
        )
        for key in ("manual_decisions", "auto_resolutions", "llm_arbitration_context", "pending_decisions"):
            items = arbitration.get(key) if isinstance(arbitration.get(key), list) else []
            for d in items:
                title = sanitizer.sanitize(str(d.get("title", "")))
                label = sanitizer.sanitize(str(d.get("label", "") or d.get("hint", "") or d.get("title", "")))
                d["label"] = label
                d["title"] = title
        return arbitration

    def snapshot_frame(
        self,
        *,
        raw_physics: Dict[str, Any],
        session_id: str = "",
        causal_anchor: str = "local_memory",
    ) -> Dict[str, Any]:
        AutoScanner.ensure_loaded()
        original_scores = read_runtime_scores(raw_physics) if isinstance(raw_physics, dict) else {}
        if isinstance(raw_physics, dict):
            hydrate_v17_physics_tensor(raw_physics)
        self.assert_six_pillars_physics(raw_physics)
        adapter = PhysicsAdapter(root=__import__("pathlib").Path(self.repo_root))
        scores = adapter.read_deity_scores(raw_physics)
        if not scores and original_scores:
            scores = {str(k): float(v) for k, v in original_scores.items()}
        base_scores = read_base_scores(raw_physics) if isinstance(raw_physics, dict) else {}
        narrative_scores = build_narrative_scores(scores, str(raw_physics.get("will_proxy") or "stable")) if isinstance(raw_physics, dict) else {}
        ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
        god_of_use = [x[0] for x in ranked[:2]]
        god_of_taboo = [x[0] for x in ranked[-2:]] if len(ranked) >= 2 else []
        pattern = self._resolve_pattern(scores)
        tension = (max(scores.values()) - min(scores.values())) if scores else 0.0
        total_energy_index = float(raw_physics.get("total_energy_index") or sum(scores.values()) or 0.0)
        pt = raw_physics if isinstance(raw_physics, dict) else {}
        if isinstance(pt.get("meta"), dict) and pt["meta"].get("hit_pattern_name"):
            pattern = str(pt["meta"]["hit_pattern_name"])
        spec_facts = logic_pd.collect_all_spec_facts_and_record(pt)
        spec_rows = [v17_fact_to_row(f) for f in spec_facts]
        spec_rows.sort(key=lambda row: float(row.get("weight", 0.0)), reverse=True)
        plugin_rows = spec_rows
        plugin_facts = [str(x.get("fact", "")).strip() for x in plugin_rows if str(x.get("fact", "")).strip()]
        plugin_hits = sorted({str(x.get("plugin", "")).strip() for x in plugin_rows if str(x.get("plugin", "")).strip()})
        arbitration = self._decision_arbitration(raw_physics, scores, spec_facts=spec_facts)
        decisions = arbitration.get("manual_decisions", [])
        fact_list = raw_physics.get("facts") if isinstance(raw_physics.get("facts"), list) else []
        sorted_fact_rows = self._sorted_fact_rows(fact_list)
        facts_out = [str(x.get("fact") or "").strip() for x in sorted_fact_rows if str(x.get("fact") or "").strip()][:160]
        inner: Dict[str, Any] = {
            "snapshot_kind": "physics",
            "snapshot_contract": "v17.21_full_physics",
            **self._physics_trace(raw_physics, causal_anchor=causal_anchor),
            "physics_validation": {"state": "aligned", "gate": "six_pillars"},
            "render_text": f"格局快照已同步：{pattern}",
            "pattern": pattern,
            "four_pillars": raw_physics.get("four_pillars", {}),
            "luck_pillar": raw_physics.get("luck_pillar"),
            "flow_pillar": raw_physics.get("flow_pillar"),
            "flow_year": raw_physics.get("flow_year"),
            "ten_gods": raw_physics.get("ten_gods", []),
            "ten_gods_base_l0": base_scores,
            "ten_gods_runtime": scores,
            "ten_gods_narrative": narrative_scores,
            "deity_scores": scores,
            "ten_gods_absolute_intensity": scores,
            "total_energy_index": round(total_energy_index, 2),
            # V17.35: 彻底剥离非 JSON 对象的 ledger。由于顶层已有 ten_gods_ledger，此处直接剔除以绝后患
            "energy_meta": {k: v for k, v in (raw_physics.get("energy_meta") or {}).items() if k != "ledger"},
            "ten_gods_ledger": raw_physics.get("ten_gods_ledger", {}),
            "flow_topology": raw_physics.get("flow_topology", []),
            "physics_report": NarrativeMappingEngine.build_physics_report_lines(raw_physics),
            "physics_tension": tension,
            "manual_decisions": decisions,
            "auto_resolutions": arbitration.get("auto_resolutions", []),
            "llm_arbitration_context": arbitration.get("llm_arbitration_context", []),
            "pending_decisions": decisions,
            "facts": facts_out,
            "fact_rows": sorted_fact_rows[:160],
            "plugins": {
                "hits": list(plugin_hits),
                "rows": plugin_rows[:128],
                "statuses": list(((pt.get("meta") or {}).get("plugin_execution_status") or []))[:128],
                "claims": list(((pt.get("meta") or {}).get("plugin_claims") or []))[:128],
                "conflicts": list(((pt.get("meta") or {}).get("plugin_conflicts") or []))[:128],
                "conflict_resolutions": list(((pt.get("meta") or {}).get("plugin_conflict_resolutions") or []))[:128],
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
        facts: List[Any],
        will_proxy: str,
        user_message: str = "",
        action_signal: bool = False,
        decision_anchor: str = "",
        action_queue: Optional[asyncio.Queue[Dict[str, Any]]] = None,
        role_style: str = V17_ROLE_WEAVER,
        decisions: Optional[List[Dict[str, Any]]] = None,
        session_id: str = "",
        causal_anchor: str = "redis_sync",
        stability_checked: bool = False,
    ) -> AsyncIterator[Dict[str, Any]]:
        if isinstance(raw_physics, dict):
            hydrate_v17_physics_tensor(raw_physics)
        self.assert_six_pillars_physics(raw_physics)
        if not stability_checked:
            await PhysicsService.ensure_stability(
                str(session_id or "").strip() or "default",
                local_physics=raw_physics if isinstance(raw_physics, dict) else None,
            )
        adapter = PhysicsAdapter(root=__import__("pathlib").Path(self.repo_root))
        scores = adapter.read_deity_scores(raw_physics)
        narrative_scores = build_narrative_scores(scores, will_proxy)
        ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
        god_of_use = [x[0] for x in ranked[:2]]
        god_of_taboo = [x[0] for x in ranked[-2:]] if len(ranked) >= 2 else []
        pattern = self._resolve_pattern(scores)
        total_energy_index = float(raw_physics.get("total_energy_index") or sum(scores.values()) or 0.0)
        if isinstance(raw_physics, dict):
            meta = raw_physics.get("meta") if isinstance(raw_physics.get("meta"), dict) else {}
            if meta.get("hit_pattern_name"):
                pattern = str(meta["hit_pattern_name"])

        def _merge_rows() -> List[Dict[str, Any]]:
            pt = raw_physics if isinstance(raw_physics, dict) else {}
            return [v17_fact_to_row(f) for f in logic_pd.collect_all_spec_facts_and_record(pt)]

        plugin_rows = await asyncio.to_thread(_merge_rows)
        plugin_rows.sort(key=lambda row: float(row.get("weight", 0.0)), reverse=True)
        plugin_facts = [str(x.get("fact", "")).strip() for x in plugin_rows if str(x.get("fact", "")).strip()]
        fragments = self._build_fragments(
            scores,
            [*facts, *plugin_rows],
            pattern,
            total_energy_index=total_energy_index,
        )
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
                    "snapshot_kind": "llm_audit_dispatch",
                    **self._physics_trace(raw_physics, causal_anchor=causal_anchor),
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
        try:
            _audit_rows = len(audit_blob.get("llm_request_messages") or [])
        except Exception:
            _audit_rows = 0
        print(
            f"[V17-NARRATOR] session={session_id or 'default'} audit_preview_ready role={rid} facts={len(fragments)} messages={_audit_rows}",
            flush=True,
        )
        fpt = audit_blob.get("full_prompt_trace") if isinstance(audit_blob.get("full_prompt_trace"), dict) else {}
        fpt = {**fpt, **self._physics_trace(raw_physics, causal_anchor=causal_anchor)}
        # 预发审计帧：在 await pipeline.run() 启动之前下发，前端可先见 full_prompt_trace（LLM 失败亦有据可查）。
        yield {
            "timestamp": _now_iso(),
            "layer": "SNAPSHOT",
            "payload": {
                "snapshot_kind": "llm_audit_preview",
                **self._physics_trace(raw_physics, causal_anchor=causal_anchor),
                "render_text": "引擎正在思考以下事实…",
                **audit_blob,
                "physics_report": NarrativeMappingEngine.build_physics_report_lines(raw_physics),
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
                    **self._physics_trace(raw_physics, causal_anchor=causal_anchor),
                },
            },
        }
        await asyncio.sleep(0)

        llm_task = asyncio.create_task(_run_pipeline())
        print(
            f"[V17-NARRATOR] session={session_id or 'default'} llm_task_started role={rid} will={will_proxy}",
            flush=True,
        )
        streamed = False
        p_task = None
        a_task = None
        try:
            while not llm_task.done():
                if p_task is None: p_task = asyncio.create_task(partial_q.get())
                if a_task is None and action_queue is not None: a_task = asyncio.create_task(action_queue.get())
                
                wait_set = {p_task}
                if a_task: wait_set.add(a_task)
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
                                import re
                                m = re.search(r"\[(INTENSIFY|WEAKEN):([a-zA-Z\u4e00-\u9fa5]{1,2})\]", chunk)
                                if m:
                                    at, el = m.groups()
                                    await _queue_llm_feedback_proposal(
                                        session_id=str(session_id),
                                        raw_physics=raw_physics if isinstance(raw_physics, dict) else {},
                                        tag=at,
                                        element_or_god=el,
                                        reason=f"叙事洞察: {el}势态变化",
                                    )
                            yield {
                                "timestamp": _now_iso(), "layer": "NARRATOR",
                                "payload": {
                                    "render_text": chunk, "will_proxy": str(will_proxy or "stable"),
                                    "ten_gods_narrative": narrative_scores,
                                    "llm_meta": {"stream_partial": True, "model": _model_hint},
                                    "source_facts": [], "god_rings": {"god_of_use": god_of_use, "god_of_taboo": god_of_taboo},
                                }
                            }
                    elif t == a_task:
                        a_task = None
                        if isinstance(res, dict) and res.get("signal") in {"PHYSICS_UPDATE", "PHYSICS_SYNC"}:
                            yield {
                                "timestamp": _now_iso(), "layer": "SNAPSHOT",
                                "payload": {
                                    "render_text": "物理同步中…", "type": "PHYSICS_SYNC",
                                    **res.get("payload", {})
                                }
                            }
                        else:
                            llm_task.cancel()
                            raise ActionInterruptDuringStream(res)
        finally:
            if p_task: p_task.cancel()
            if a_task: a_task.cancel()
            if not llm_task.done(): llm_task.cancel()
            try: await llm_task
            except: pass

        # 处理滞后 tokens
        while not partial_q.empty():
            try:
                res = partial_q.get_nowait()
                if isinstance(res, LlmStreamStep):
                    if res.kind == "dispatched": yield _frame_dispatched(res.data)
                    elif res.kind == "connected": yield _frame_connected(res.data)
                    continue
                chunk = str(res)
                if chunk:
                    streamed = True
                    yield {
                        "timestamp": _now_iso(), "layer": "NARRATOR",
                        "payload": {
                            "render_text": chunk, "will_proxy": str(will_proxy or "stable"),
                            "ten_gods_narrative": narrative_scores,
                            "llm_meta": {"stream_partial": True, "model": _model_hint},
                            "source_facts": [], "god_rings": {"god_of_use": god_of_use, "god_of_taboo": god_of_taboo},
                        }
                    }
            except: break

        exc = llm_task.exception()
        if exc is not None:
            print(f"[V17-NARRATOR] session={session_id or 'default'} llm_task_exception={type(exc).__name__}", flush=True)
            raise exc
        frame = llm_task.result()
        print(
            f"[V17-NARRATOR] session={session_id or 'default'} llm_task_done streamed={streamed}",
            flush=True,
        )
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
