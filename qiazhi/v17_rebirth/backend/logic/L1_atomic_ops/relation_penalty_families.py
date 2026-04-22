from __future__ import annotations

from typing import Any, Callable, Dict, List


def collect_penalty_relation_deltas(
    *,
    chong_hits: List[Dict[str, Any]],
    hai_hits: List[Dict[str, Any]],
    po_hits: List[Dict[str, Any]],
    xing_hits: List[Dict[str, Any]],
    branch_scope_totals: Dict[str, float],
    relation_delta_raw: Dict[str, float],
    relation_traces: List[Dict[str, Any]],
    pillars_group_closeness: Callable[[List[str]], float],
    get_penalty_value: Callable[[str, float], float],
    relation_apply_branch_delta: Callable[..., None],
    append_relation_trace: Callable[..., None],
    penalty_chong_default: float,
    penalty_hai_default: float,
    penalty_po_default: float,
    penalty_xing_default: float,
) -> None:
    for kind, hits, cfg_key, default_value in (
        ("chong", chong_hits, "REL_ROOT_PENALTY_CHONG", penalty_chong_default),
        ("hai", hai_hits, "REL_ROOT_PENALTY_HAI", penalty_hai_default),
        ("po", po_hits, "REL_ROOT_PENALTY_PO", penalty_po_default),
    ):
        for hit in hits:
            pair = [str(x) for x in (hit.get("pair") or []) if str(x).strip()]
            if len(pair) != 2:
                continue
            pillars = [str(p) for p in (hit.get("pillars") or []) if str(p).strip()]
            closeness = pillars_group_closeness(pillars)
            intensity = -get_penalty_value(cfg_key, default_value) * closeness
            for branch in pair:
                relation_apply_branch_delta(
                    branch=branch,
                    branch_scope_totals=branch_scope_totals,
                    relation_element="",
                    magnitude=intensity,
                    out=relation_delta_raw,
                )
            append_relation_trace(
                relation_traces,
                kind,
                pair,
                pillars,
                intensity,
                "",
                details={"closeness": round(closeness, 4)},
            )

    for hit in xing_hits:
        members = [str(b) for b in (hit.get("branches") or []) if str(b).strip()]
        if len(members) < 2:
            continue
        pillars = [str(p) for p in (hit.get("edge") or []) if str(p).strip()]
        closeness = pillars_group_closeness(pillars)
        intensity = -get_penalty_value("REL_ROOT_PENALTY_XING", penalty_xing_default) * closeness
        for branch in members:
            relation_apply_branch_delta(
                branch=branch,
                branch_scope_totals=branch_scope_totals,
                relation_element="",
                magnitude=intensity,
                out=relation_delta_raw,
            )
        append_relation_trace(
            relation_traces,
            "xing",
            members,
            pillars,
            intensity,
            "",
            details={"closeness": round(closeness, 4)},
        )
