from __future__ import annotations

from dataclasses import dataclass, field
import asyncio
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, AsyncIterator, Dict, List, Optional

from v17_rebirth.backend.adapters.physics_adapter import PhysicsAdapter
from v17_rebirth.backend.logic.L1_atomic_ops.l1_meta_hydration import hydrate_v17_physics_tensor
from v17_rebirth.backend.logic import plugin_discovery as logic_pd
from v17_rebirth.backend.services.auto_scanner import AutoScanner
from v17_rebirth.backend.plugins.spec import V17Fact
from v17_rebirth.backend.plugins.v17_wrappers import v17_fact_to_row
from v17_rebirth.backend.services.decision_intel import (
    build_claim_conflict_graph,
    build_decision_arbitration,
)
from v17_rebirth.backend.services.decision_batches import build_decision_batches
from v17_rebirth.backend.services.evidence_bundle import build_evidence_bundle
from v17_rebirth.backend.services.god_ring_authority import resolve_god_ring_authority
from v17_rebirth.backend.services.narrative_intel import (
    build_fact_fragments,
    sorted_fact_rows,
)
from v17_rebirth.backend.services.narrative_flow import run_narrator_frames
from v17_rebirth.backend.services.snapshot_intel import (
    build_snapshot_payload,
    build_snapshot_plan_trace_index,
)
from v17_rebirth.backend.services.narrative_pipeline_cache import (
    get_realtime_pipeline,
    restart_pipeline_cache,
)
from v17_rebirth.infrastructure.llm_bridge import V17_ROLE_JUDGE, V17_ROLE_WEAVER, V17LlmBridge
from v17_rebirth.infrastructure.llm_micro_client import _normalize_fuse_role
from v17_rebirth.backend.services.physics_canonical import six_pillars_tensor_complete
from v17_rebirth.backend.services.physics_layers import build_narrative_scores, read_base_scores, read_runtime_scores
from v17_rebirth.backend.services.physics_service import DataSovereigntyError, PhysicsService

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
    return restart_pipeline_cache()


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

    def _sorted_fact_rows(self, facts: List[Any]) -> List[Dict[str, Any]]:
        return sorted_fact_rows(facts)

    def _build_fragments(
        self,
        deity_scores: Dict[str, float],
        facts: List[Any],
        *,
        total_energy_index: float = 0.0,
    ) -> List[str]:
        return build_fact_fragments(deity_scores, facts, total_energy_index=total_energy_index)

    def _decision_arbitration(
        self,
        raw_physics: Dict[str, Any],
        _deity_scores: Dict[str, float],
        *,
        spec_facts: List[Any] | None = None,
    ) -> Dict[str, Any]:
        del _deity_scores
        return build_decision_arbitration(raw_physics=raw_physics, spec_facts=spec_facts if isinstance(spec_facts, list) else None)

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
        tension = (max(scores.values()) - min(scores.values())) if scores else 0.0
        total_energy_index = float(raw_physics.get("total_energy_index") or sum(scores.values()) or 0.0)
        pt = raw_physics if isinstance(raw_physics, dict) else {}
        spec_facts = logic_pd.collect_all_spec_facts_and_record(pt)
        plugin_rows = sorted([v17_fact_to_row(f) for f in spec_facts], key=lambda row: float(row.get("weight", 0.0)), reverse=True)
        evidence_bundle = build_evidence_bundle(spec_facts, physics_tensor=pt)
        plugin_facts = [str(x.get("fact", "")).strip() for x in plugin_rows if str(x.get("fact", "")).strip()]
        plugin_hits = sorted({str(x.get("plugin", "")).strip() for x in plugin_rows if str(x.get("plugin", "")).strip()})
        arbitration = build_decision_arbitration(raw_physics=raw_physics, spec_facts=spec_facts)
        decision_batches = build_decision_batches(arbitration=arbitration)
        claim_conflict_graph = build_claim_conflict_graph(raw_physics=raw_physics)
        fact_list = raw_physics.get("facts") if isinstance(raw_physics.get("facts"), list) else []
        sorted_fact_rows = self._sorted_fact_rows(fact_list)
        inner = build_snapshot_payload(
            raw_physics=pt,
            ranked=ranked,
            scores=scores,
            base_scores=base_scores,
            narrative_scores=narrative_scores,
            tension=tension,
            total_energy_index=total_energy_index,
            arbitration=arbitration,
            decision_batches=decision_batches,
            plugin_rows=plugin_rows,
            plugin_hits=list(plugin_hits),
            plugin_facts=plugin_facts,
            evidence_bundle=evidence_bundle,
            sorted_fact_rows=sorted_fact_rows,
            claim_conflict_graph=claim_conflict_graph,
            causal_anchor=causal_anchor,
            trace_index_builder=build_snapshot_plan_trace_index,
        )
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
        god_ring_authority = resolve_god_ring_authority(raw_physics=raw_physics, ranked_pairs=ranked)
        god_of_use = list(god_ring_authority.get("god_of_use") or [])
        god_of_taboo = list(god_ring_authority.get("god_of_taboo") or [])
        tongguan_gods = list(god_ring_authority.get("tongguan_gods") or [])
        total_energy_index = float(raw_physics.get("total_energy_index") or sum(scores.values()) or 0.0)

        def _merge_rows() -> List[Dict[str, Any]]:
            pt = raw_physics if isinstance(raw_physics, dict) else {}
            return [v17_fact_to_row(f) for f in logic_pd.collect_all_spec_facts_and_record(pt)]

        plugin_rows = await asyncio.to_thread(_merge_rows)
        plugin_rows.sort(key=lambda row: float(row.get("weight", 0.0)), reverse=True)
        plugin_facts = [str(x.get("fact", "")).strip() for x in plugin_rows if str(x.get("fact", "")).strip()]
        fragments = self._build_fragments(
            scores,
            [*facts, *plugin_rows],
            total_energy_index=total_energy_index,
        )
        arbitration = build_decision_arbitration(
            raw_physics=raw_physics,
            spec_facts=facts if all(isinstance(f, V17Fact) for f in facts) else None,
        )
        decision_batches = build_decision_batches(arbitration=arbitration)
        fragments.extend([str(x).strip() for x in decision_batches.get("prompt_lines", []) if str(x).strip()])
        rid = _normalize_fuse_role(str(role_style or V17_ROLE_WEAVER))
        if rid == V17_ROLE_JUDGE:
            for d in (decisions or [])[:32]:
                if not isinstance(d, dict):
                    continue
                lab = str(d.get("label") or d.get("title") or "").strip()
                if lab:
                    fragments.append(f"圣殿裁决线索（已入账）：{lab}")
        pipeline = get_realtime_pipeline()
        async def _on_feedback(tag: str, el: str, reason: str) -> None:
            await _queue_llm_feedback_proposal(
                session_id=str(session_id),
                raw_physics=raw_physics if isinstance(raw_physics, dict) else {},
                tag=tag,
                element_or_god=el,
                reason=reason,
            )

        async for frame in run_narrator_frames(
            raw_physics=raw_physics if isinstance(raw_physics, dict) else {},
            fragments=fragments,
            narrative_scores=narrative_scores,
            decision_batches=decision_batches,
            will_proxy=will_proxy,
            god_of_use=god_of_use,
            god_of_taboo=god_of_taboo,
            tongguan_gods=tongguan_gods,
            decision_anchor=decision_anchor,
            user_message=user_message,
            action_signal=action_signal,
            role_style=rid,
            session_id=str(session_id),
            causal_anchor=causal_anchor,
            action_queue=action_queue,
            on_feedback_proposal=_on_feedback,
            model_hint=str(V17LlmBridge().resolve().get("model") or "").strip(),
            pipeline=pipeline,
        ):
            yield frame
