from __future__ import annotations

from typing import Any, Callable, Dict, List, Tuple


def build_runtime_stems(
    four_pillars: Dict[str, str],
    luck_pillar: str,
    flow_pillar: str,
    *,
    parse_gz: Callable[[str], Tuple[str, str]],
) -> Dict[str, str]:
    stems: Dict[str, str] = {}
    for key in ("year", "month", "day", "hour"):
        stem, _ = parse_gz(str(four_pillars.get(key, "")).strip())
        if stem:
            stems[key] = stem
    for key, gz in (("luck", luck_pillar), ("flow", flow_pillar)):
        stem, _ = parse_gz(str(gz or "").strip())
        if stem:
            stems[key] = stem
    return stems


def finalize_root_dynamic_state(
    *,
    branch_rows: List[Tuple[str, str]],
    relation_traces: List[Dict[str, Any]],
    branch_hidden_base_strengths: Dict[Tuple[str, str, str], float],
    static_rooted: Dict[str, float],
    relation_delta_raw: Dict[str, float],
    stem_cases: List[Dict[str, Any]],
    build_relation_source_retention_plan: Callable[..., Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]],
    build_stem_fusion_source_retention_plan: Callable[..., List[Dict[str, Any]]],
) -> Tuple[Dict[str, float], Dict[str, Any]]:
    branch_source_retention: List[Dict[str, Any]] = []
    stem_source_retention: List[Dict[str, Any]] = []
    if branch_rows and relation_traces:
        branch_source_retention, source_attenuation_summary = build_relation_source_retention_plan(
            branch_rows=branch_rows,
            relation_traces=relation_traces,
        )
        for row in branch_source_retention:
            scope = str(row.get("scope") or "")
            branch = str(row.get("branch") or "")
            hidden_stem = str(row.get("hidden_stem") or "")
            retention = max(0.0, min(1.0, float(row.get("retention") or 1.0)))
            base_strength = float(branch_hidden_base_strengths.get((scope, branch, hidden_stem), 0.0))
            if base_strength <= 0.0 or retention >= 0.999:
                continue
            static_rooted[hidden_stem] = max(0.0, float(static_rooted.get(hidden_stem, 0.0)) - base_strength * (1.0 - retention))
    else:
        source_attenuation_summary = []

    if stem_cases:
        stem_source_retention = build_stem_fusion_source_retention_plan(stem_cases=stem_cases)

    rooted = dict(static_rooted)
    relation_delta_applied: Dict[str, float] = {}
    for stem, raw_delta in relation_delta_raw.items():
        base = max(0.0, float(static_rooted.get(stem, 0.0)))
        cap_plus = max(0.2, base * 0.55)
        cap_minus = max(0.16, base * 0.45)
        applied = max(-cap_minus, min(cap_plus, float(raw_delta)))
        if abs(applied) <= 1e-9:
            continue
        relation_delta_applied[stem] = applied
        rooted[stem] = max(0.0, rooted.get(stem, 0.0) + applied)

    relation_counts: Dict[str, int] = {}
    for trace in relation_traces:
        kind = str(trace.get("kind") or "")
        relation_counts[kind] = relation_counts.get(kind, 0) + 1

    return rooted, {
        "hits": relation_counts,
        "dynamic_raw": {stem: round(v, 4) for stem, v in sorted(relation_delta_raw.items()) if abs(v) > 1e-9},
        "dynamic_applied": {stem: round(v, 4) for stem, v in sorted(relation_delta_applied.items()) if abs(v) > 1e-9},
        "branch_source_retention": branch_source_retention,
        "stem_source_retention": stem_source_retention,
        "source_attenuation_summary": source_attenuation_summary,
        "traces": relation_traces[:48],
    }
