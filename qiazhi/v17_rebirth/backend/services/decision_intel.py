from __future__ import annotations

from typing import Any, Dict, List

from v17_rebirth.backend.logic import plugin_discovery as logic_pd
from v17_rebirth.backend.narrative.sanitizer import NarrativeSanitizer
from v17_rebirth.backend.plugins.spec import V17Fact
from v17_rebirth.backend.plugins.v17_wrappers import collect_pending_decisions_from_specs
from v17_rebirth.backend.services.decision_compiler import compile_decision_arbitration
from v17_rebirth.backend.services.brain_action_router import apply_brain_action_queue


def _sanitize_rows(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    sanitizer = NarrativeSanitizer()
    out: List[Dict[str, Any]] = []
    for d in rows:
        if not isinstance(d, dict):
            continue
        row = dict(d)
        row["label"] = sanitizer.sanitize(str(row.get("label", "") or row.get("hint", "") or row.get("title", "")))
        row["title"] = sanitizer.sanitize(str(row.get("title", "")))
        out.append(row)
    return out


def build_decision_arbitration(
    *,
    raw_physics: Dict[str, Any],
    spec_facts: List[V17Fact] | None = None,
) -> Dict[str, List[Dict[str, Any]]]:
    pt = raw_physics if isinstance(raw_physics, dict) else {}
    if spec_facts is None or not all(isinstance(f, V17Fact) for f in spec_facts):
        spec_facts = logic_pd.collect_all_spec_facts_and_record(pt)

    raw_pending = pt.get("pending_decisions") if isinstance(pt.get("pending_decisions"), list) else []
    arbitration = compile_decision_arbitration(
        facts=spec_facts,
        spec_decisions=collect_pending_decisions_from_specs(spec_facts),
        existing_rows=[dict(item) for item in raw_pending if isinstance(item, dict)],
        physics_tensor=pt,
    )
    arbitration = apply_brain_action_queue(arbitration=arbitration, meta=pt.get("meta") if isinstance(pt.get("meta"), dict) else {})
    for key in ("manual_decisions", "auto_resolutions", "llm_arbitration_context", "pending_decisions"):
        arbitration[key] = _sanitize_rows(arbitration.get(key, []) if isinstance(arbitration.get(key), list) else [])
    return arbitration


def build_auto_decisions(
    *,
    auto_resolutions: List[Dict[str, Any]],
    llm_arbitration_context: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    seen: set[str] = set()

    def _dedupe_key(row: Dict[str, Any]) -> str:
        return "::".join(
            [
                str(row.get("id") or "").strip(),
                str(row.get("source") or row.get("plugin_id") or "").strip(),
                str(row.get("label") or row.get("title") or "").strip(),
                str(row.get("target_god") or (row.get("physical_impact") or {}).get("target_god") or "").strip(),
            ]
        )

    for channel, source_rows in (
        ("system", auto_resolutions),
        ("llm", llm_arbitration_context),
    ):
        for item in source_rows:
            if not isinstance(item, dict):
                continue
            row = dict(item)
            key = _dedupe_key(row)
            if key in seen:
                continue
            seen.add(key)
            row.setdefault("arbitration_mode", "auto")
            row["auto_bucket"] = channel
            rows.append(row)
    return rows[:96]


def build_claim_conflict_graph(raw_physics: Dict[str, Any]) -> Dict[str, Any]:
    def _safe_number(value: Any, default: float = 0.0) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    meta = raw_physics.get("meta") if isinstance(raw_physics.get("meta"), dict) else {}
    claims = [dict(row) for row in (meta.get("plugin_claims") or []) if isinstance(row, dict)]
    conflicts = [dict(row) for row in (meta.get("plugin_conflicts") or []) if isinstance(row, dict)]
    resolutions = [dict(row) for row in (meta.get("plugin_conflict_resolutions") or []) if isinstance(row, dict)]
    resolutions_by_conflict: Dict[str, List[Dict[str, Any]]] = {}
    for row in resolutions:
        cid = str(row.get("conflict_id") or "").strip()
        if cid:
            resolutions_by_conflict.setdefault(cid, []).append(row)

    nodes: List[Dict[str, Any]] = []
    for claim in claims:
        cid = str(claim.get("claim_id") or "").strip()
        if not cid:
            continue
        related_conflicts: List[str] = []
        for conflict in conflicts:
            conf_id = str(conflict.get("conflict_id") or "").strip()
            claim_ids = [str(item).strip() for item in (conflict.get("claims") or []) if str(item).strip()]
            if cid in claim_ids and conf_id:
                related_conflicts.append(conf_id)
        nodes.append(
            {
                "node_id": cid,
                "plugin_id": str(claim.get("plugin_id") or "").strip(),
                "claim_text": str(claim.get("claim_text") or claim.get("label") or "").strip(),
                "target_god": str(claim.get("target_god") or "").strip(),
                "logic_level": str(claim.get("logic_level") or "").strip(),
                "priority": _safe_number(claim.get("priority")),
                "confidence": _safe_number(claim.get("confidence")),
                "conflict_count": len(related_conflicts),
                "conflict_ids": related_conflicts,
            }
        )

    claim_edges: List[Dict[str, Any]] = []
    conflict_rows: List[Dict[str, Any]] = []
    for conflict in conflicts:
        cid = str(conflict.get("conflict_id") or "").strip()
        if not cid:
            continue
        claim_ids = [str(item).strip() for item in (conflict.get("claims") or []) if str(item).strip()]
        if len(claim_ids) < 2:
            continue
        resolved = False
        for row in resolutions_by_conflict.get(cid, []):
            status = str(row.get("status") or "").strip().lower()
            resolved_by = str(row.get("resolved_by") or "").strip().lower()
            if status in {"resolved_system", "approved", "resolved"} or resolved_by in {"system", "llm", "user", "manual"}:
                resolved = True
                break
        conflict_rows.append(
            {
                "conflict_id": cid,
                "conflict_type": str(conflict.get("conflict_type") or "unknown"),
                "severity": str(conflict.get("severity") or "P3"),
                "status": "resolved" if resolved else "open",
                "claims": claim_ids,
                "target_god": str(conflict.get("target_god") or "").strip(),
                "recommended_arbiter": str(conflict.get("recommended_arbiter") or "system").strip(),
                "why_conflict": str(conflict.get("why_conflict") or "").strip(),
                "resolution_count": len(resolutions_by_conflict.get(cid, [])),
                "resolution_ids": [
                    str(row.get("resolution_id") or row.get("action_id") or "").strip()
                    for row in resolutions_by_conflict.get(cid, [])
                ],
            }
        )
        for i, src in enumerate(claim_ids):
            for tgt in claim_ids[i + 1 :]:
                claim_edges.append(
                    {
                        "source_claim_id": src,
                        "target_claim_id": tgt,
                        "conflict_id": cid,
                        "source": "claim_graph",
                        "conflict_type": str(conflict.get("conflict_type") or "unknown"),
                    }
                )

    unresolved_count = sum(1 for row in conflict_rows if row.get("status") != "resolved")
    summary: Dict[str, Any] = {
        "node_count": len(nodes),
        "claim_edge_count": len(claim_edges),
        "conflict_count": len(conflict_rows),
        "open_conflict_count": unresolved_count,
        "resolved_conflict_count": len(conflict_rows) - unresolved_count,
        "conflict_sample_count": min(4, len(conflict_rows)),
    }
    return {
        "graph_version": "v17.claim_graph.1",
        "nodes": nodes,
        "edges": claim_edges,
        "conflicts": conflict_rows,
        "summary": summary,
    }
