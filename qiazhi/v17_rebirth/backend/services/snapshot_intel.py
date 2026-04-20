from __future__ import annotations

import json
from typing import Any, Callable, Dict, List

from v17_rebirth.backend.narrative.NarrativeMappingEngine import NarrativeMappingEngine
from v17_rebirth.backend.services.physics_canonical import six_pillars_tensor_complete
from v17_rebirth.backend.services.physics_service import DataSovereigntyError


def _dedupe_decision_rows(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in rows:
        if not isinstance(row, dict):
            continue
        rid = str(row.get("id") or "").strip()
        source = str(row.get("source") or row.get("plugin_id") or "").strip()
        label = str(row.get("label") or row.get("title") or "").strip()
        target = str(
            row.get("target_god")
            or (row.get("physical_impact") or {}).get("target_god")
            or row.get("source_event")
            or ""
        ).strip()
        key = f"{rid}::{source}::{label}::{target}" if (rid or source or label or target) else str(id(row))
        if key in seen:
            continue
        seen.add(key)
        out.append(dict(row))
    return out


def build_snapshot_plan_trace_index(raw_physics: Dict[str, Any]) -> Dict[str, Any]:
    """构建决策计划溯源索引（分页快照最小化版）。"""
    state = raw_physics.get("decision_brain_state") if isinstance(raw_physics, dict) else None
    plans = state.get("plan_queue") if isinstance(state, dict) else None
    if not isinstance(plans, list):
        return {
            "contract": "v17.decision.trace_index.v1",
            "plan_count": 0,
            "items": [],
        }

    rows: list[dict[str, Any]] = []
    for row in plans[:20]:
        if not isinstance(row, dict):
            continue

        plan_id = str(row.get("plan_id") or "").strip()
        if not plan_id:
            continue

        meta = row.get("meta") if isinstance(row.get("meta"), dict) else {}
        raw_trace = meta.get("decision_trace") if isinstance(meta.get("decision_trace"), list) else []
        compact_trace = [
            {
                k: item.get(k)
                for k in ("decision_id", "label", "source", "target_god", "impact_ratio")
                if isinstance(item, dict) and item.get(k) is not None
            }
            for item in raw_trace[:3]
            if isinstance(item, dict)
        ]

        decision_ids = [str(x).strip() for x in row.get("decision_ids") if str(x).strip()] if isinstance(row.get("decision_ids"), list) else []
        if not decision_ids:
            decision_ids = [
                str(item.get("decision_id") or "").strip()
                for item in compact_trace
                if isinstance(item, dict)
                and str(item.get("decision_id") or "").strip()
            ]

        row_out: Dict[str, Any] = {
            "plan_id": plan_id,
            "anchor": str(row.get("anchor") or "").strip() or None,
            "status": str(row.get("status") or "").strip() or None,
            "routing": str(row.get("routing") or "").strip() or None,
            "updated_at": str(row.get("updated_at") or "").strip() or None,
            "decision_count": int(meta.get("decision_count") or len(decision_ids)),
            "decision_ids": decision_ids,
            "batch_ids": [str(x).strip() for x in row.get("batch_ids") if str(x).strip()]
            if isinstance(row.get("batch_ids"), list)
            else [],
            "impact_summary": dict(row.get("impact_summary") or {}),
            "decision_trace_count": len(compact_trace),
            "decision_trace": compact_trace,
            "decision_trace_contract": "v17.decision.trace.v1",
        }

        if str(meta.get("routing_reason") or "").strip():
            row_out["routing_reason"] = str(meta.get("routing_reason") or "").strip()
        if str(meta.get("routing_policy") or "").strip():
            row_out["routing_policy"] = str(meta.get("routing_policy") or "").strip()
        if str(meta.get("llm_review_prompt") or "").strip():
            row_out["llm_prompt_preview"] = True

        rows.append(row_out)

    return {
        "contract": "v17.decision.trace_index.v1",
        "plan_count": len(rows),
        "items": rows,
    }


def build_snapshot_payload(
    raw_physics: Dict[str, Any],
    *,
    ranked: List[tuple[str, float]],
    scores: Dict[str, float],
    base_scores: Dict[str, float],
    narrative_scores: Dict[str, float],
    tension: float,
    total_energy_index: float,
    arbitration: Dict[str, Any],
    decision_batches: Dict[str, Any],
    plugin_rows: List[Dict[str, Any]],
    plugin_hits: List[str],
    plugin_facts: List[str],
    sorted_fact_rows: List[Dict[str, Any]],
    claim_conflict_graph: Dict[str, Any],
    causal_anchor: str,
    trace_index_builder: Callable[[Dict[str, Any]], Dict[str, Any]],
) -> Dict[str, Any]:
    decisions = arbitration.get("manual_decisions", [])
    auto_resolutions = arbitration.get("auto_resolutions", []) if isinstance(arbitration.get("auto_resolutions"), list) else []
    llm_arbitration_context = (
        arbitration.get("llm_arbitration_context", [])
        if isinstance(arbitration.get("llm_arbitration_context"), list)
        else []
    )
    auto_decisions = []
    if isinstance(arbitration, dict):
        # 兼容上游可能直接传入了已展开的 auto_decisions
        auto_decisions = arbitration.get("auto_decisions", [])
    if not auto_decisions:
        from v17_rebirth.backend.services.decision_intel import build_auto_decisions

        auto_decisions = build_auto_decisions(
            auto_resolutions=auto_resolutions,
            llm_arbitration_context=llm_arbitration_context,
        )
    all_decisions = _dedupe_decision_rows([*(decisions if isinstance(decisions, list) else []), *auto_decisions])

    fact_rows = [str(x.get("fact") or "").strip() for x in sorted_fact_rows if str(x.get("fact") or "").strip()][:160]

    ranked_pairs = ranked[:]
    god_of_use = [x[0] for x in ranked_pairs[:2]]
    god_of_taboo = [x[0] for x in ranked_pairs[-2:]] if len(ranked_pairs) >= 2 else []

    pt = raw_physics if isinstance(raw_physics, dict) else {}
    meta = pt.get("meta") or {}
    if not isinstance(meta, dict):
        meta = {}

    inner: Dict[str, Any] = {
        "snapshot_kind": "physics",
        "snapshot_contract": "v17.21_full_physics",
        "causal_anchor": str(causal_anchor or "local_memory"),
        "physics_fingerprint": str(
            abs(hash(json.dumps(pt, ensure_ascii=False, sort_keys=True, default=str)))
        ),
        "physics_validation": {"state": "aligned", "gate": "six_pillars"},
        "render_text": "物理快照已同步。",
        "four_pillars": pt.get("four_pillars", {}),
        "luck_pillar": pt.get("luck_pillar"),
        "flow_pillar": pt.get("flow_pillar"),
        "flow_year": pt.get("flow_year"),
        "ten_gods": pt.get("ten_gods", []),
        "ten_gods_base_l0": base_scores,
        "ten_gods_runtime": scores,
        "ten_gods_narrative": narrative_scores,
        "deity_scores": scores,
        "ten_gods_absolute_intensity": scores,
        "total_energy_index": round(total_energy_index, 2),
        "energy_meta": {k: v for k, v in (pt.get("energy_meta") or {}).items() if k != "ledger"},
        "ten_gods_ledger": pt.get("ten_gods_ledger", {}),
        "flow_topology": pt.get("flow_topology", []),
        "physics_report": NarrativeMappingEngine.build_physics_report_lines(pt),
        "physics_tension": tension,
        "decision_inbox_contract": "v17.decision.inbox.v2",
        "manual_decisions": decisions,
        "manual_inbox": decisions,
        "auto_decisions": auto_decisions,
        "auto_resolutions": auto_resolutions,
        "llm_arbitration_context": llm_arbitration_context,
        "all_decisions": all_decisions,
        "claim_conflict_graph": claim_conflict_graph,
        "decision_batches": decision_batches.get("all", []),
        "decision_prompt_batches": decision_batches.get("prompt_lines", []),
        "pending_decisions": decisions,
        "facts": fact_rows,
        "fact_rows": sorted_fact_rows[:160],
        "plugins": {
            "hits": list(plugin_hits),
            "rows": plugin_rows[:128],
            "statuses": list((meta.get("plugin_execution_status") or []))[:128],
            "claims": list((meta.get("plugin_claims") or []))[:128],
            "conflicts": list((meta.get("plugin_conflicts") or []))[:128],
            "conflict_resolutions": list((meta.get("plugin_conflict_resolutions") or []))[:128],
            "knowledge_snapshot": dict(meta.get("knowledge_snapshot") or {}),
            "brain_action_queue": list((meta.get("brain_action_queue") or []))[:128],
        },
        "decision_brain_state": dict((pt.get("decision_brain_state") or {})),
        "decision_trace_index": trace_index_builder(pt),
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
    gate = {
        "four_pillars": inner.get("four_pillars"),
        "luck_pillar": inner.get("luck_pillar"),
        "flow_pillar": inner.get("flow_pillar"),
    }
    if not six_pillars_tensor_complete(gate):
        raise DataSovereigntyError("physics_incomplete_snapshot_denied")
    return inner
