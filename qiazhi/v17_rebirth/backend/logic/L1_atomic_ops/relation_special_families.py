from __future__ import annotations

from typing import Any, Callable, Dict, List, Tuple


def collect_control_relation_deltas(
    *,
    branches: Dict[str, str],
    branch_element_map: Dict[str, str],
    control_adj_scope_pairs: Tuple[Tuple[str, str], ...],
    branch_scope_totals: Dict[str, float],
    relation_delta_raw: Dict[str, float],
    relation_traces: List[Dict[str, Any]],
    pillar_pair_closeness: Callable[[str, str], float],
    controls_element: Callable[[str, str], bool],
    get_l0_val: Callable[[str, float], float],
    relation_apply_branch_delta: Callable[..., None],
    append_relation_trace: Callable[..., None],
    control_bonus_default: float,
    control_penalty_default: float,
) -> None:
    for p1, p2 in control_adj_scope_pairs:
        b1 = str(branches.get(p1) or "")
        b2 = str(branches.get(p2) or "")
        if not b1 or not b2:
            continue
        e1 = branch_element_map.get(b1, "")
        e2 = branch_element_map.get(b2, "")
        if not e1 or not e2 or e1 == e2:
            continue
        closeness = pillar_pair_closeness(p1, p2)
        bonus = get_l0_val("REL_ROOT_CONTROL_BONUS", control_bonus_default) * closeness
        penalty = get_l0_val("REL_ROOT_CONTROL_PENALTY", control_penalty_default) * closeness
        if controls_element(e1, e2):
            relation_apply_branch_delta(
                branch=b1,
                branch_scope_totals=branch_scope_totals,
                relation_element=e1,
                magnitude=bonus,
                out=relation_delta_raw,
            )
            relation_apply_branch_delta(
                branch=b2,
                branch_scope_totals=branch_scope_totals,
                relation_element=e2,
                magnitude=-penalty,
                out=relation_delta_raw,
            )
            append_relation_trace(
                relation_traces,
                "ke",
                [b1, b2],
                [p1, p2],
                bonus - penalty,
                f"{e1}克{e2}",
                details={"closeness": round(closeness, 4)},
            )
        elif controls_element(e2, e1):
            relation_apply_branch_delta(
                branch=b2,
                branch_scope_totals=branch_scope_totals,
                relation_element=e2,
                magnitude=bonus,
                out=relation_delta_raw,
            )
            relation_apply_branch_delta(
                branch=b1,
                branch_scope_totals=branch_scope_totals,
                relation_element=e1,
                magnitude=-penalty,
                out=relation_delta_raw,
            )
            append_relation_trace(
                relation_traces,
                "ke",
                [b2, b1],
                [p2, p1],
                bonus - penalty,
                f"{e2}克{e1}",
                details={"closeness": round(closeness, 4)},
            )


def collect_stem_fusion_relation_deltas(
    *,
    stems: Dict[str, str],
    branches: Dict[str, str],
    static_rooted: Dict[str, float],
    relation_delta_raw: Dict[str, float],
    relation_traces: List[Dict[str, Any]],
    detect_stem_fusion_cases: Callable[[Dict[str, str], Dict[str, str]], List[Dict[str, Any]]],
    pillars_group_closeness: Callable[[List[str]], float],
    get_l0_val: Callable[[str, float], float],
    relation_apply_stem_element_delta: Callable[..., None],
    append_relation_trace: Callable[..., None],
    element_en_to_cn: Dict[str, str],
    stem_element_map: Dict[str, str],
    bonus_anhe_default: float,
    penalty_po_default: float,
) -> List[Dict[str, Any]]:
    stem_cases = detect_stem_fusion_cases(stems, branches) if stems else []
    for case in stem_cases:
        mode = str(case.get("mode") or "")
        hua_el_en = str(case.get("hua_element") or "")
        rel_element = element_en_to_cn.get(hua_el_en.lower(), "")
        branch_ratio = max(
            0.0,
            min(1.0, float(case.get("branch_root_ratio") if case.get("branch_root_ratio") is not None else case.get("branch_hua_ratio") or 0.0)),
        )
        visible_support = max(0.0, min(1.0, float(case.get("visible_support_strength") or (1.0 if case.get("month_stem_supports") else 0.0))))
        support_score = max(
            0.0,
            min(
                1.0,
                float(
                    case.get("effective_support_score")
                    if case.get("effective_support_score") is not None
                    else case.get("support_score")
                    if case.get("support_score") is not None
                    else visible_support * 0.62 + branch_ratio * 0.38
                ),
            ),
        )
        interference_score = max(0.0, min(1.0, float(case.get("interference_score") or 0.0)))
        manifestation_mode = str(case.get("manifestation_mode") or ("明化" if case.get("month_stem_supports") else "暗化")).strip()
        support_origin = str(case.get("support_origin") or "").strip()
        pillars = [str(p) for p in (case.get("pillars") or []) if str(p).strip()]
        closeness = pillars_group_closeness(pillars)
        stems_pair = [str(s) for s in (case.get("stems") or []) if str(s).strip()]
        efficiency = max(
            0.0,
            min(
                1.0,
                0.14
                + support_score * 0.68
                + visible_support * 0.10
                - interference_score * 0.24
                + (0.06 if manifestation_mode == "明化" else 0.0),
            ),
        )
        if mode == "transformed" and rel_element:
            intensity = get_l0_val("REL_ROOT_BONUS_ANHE", bonus_anhe_default) * efficiency * closeness
            relation_apply_stem_element_delta(
                target_element=rel_element,
                magnitude=intensity,
                rooted_static=static_rooted,
                out=relation_delta_raw,
            )
            append_relation_trace(
                relation_traces,
                "stem_fusion_transform",
                stems_pair,
                pillars,
                intensity,
                rel_element,
                details={
                    "branch_root_ratio": round(branch_ratio, 4),
                    "visible_support_strength": round(visible_support, 4),
                    "support_score": round(support_score, 4),
                    "interference_score": round(interference_score, 4),
                    "manifestation_mode": manifestation_mode,
                    "support_origin": support_origin,
                    "branch_disturbance_score": round(float(case.get("branch_disturbance_score") or 0.0), 4),
                    "stem_competition_score": round(float(case.get("stem_competition_score") or 0.0), 4),
                },
            )
        elif mode == "stuck":
            intensity = -get_l0_val("REL_ROOT_PENALTY_PO", penalty_po_default) * max(0.22, support_score) * (0.84 + interference_score * 0.36) * closeness
            for stem in stems_pair:
                stem_el = stem_element_map.get(stem, "")
                if not stem_el:
                    continue
                relation_apply_stem_element_delta(
                    target_element=stem_el,
                    magnitude=intensity * 0.6,
                    rooted_static=static_rooted,
                    out=relation_delta_raw,
                )
            append_relation_trace(
                relation_traces,
                "stem_fusion_stuck",
                stems_pair,
                pillars,
                intensity,
                "",
                details={
                    "branch_root_ratio": round(branch_ratio, 4),
                    "visible_support_strength": round(visible_support, 4),
                    "support_score": round(support_score, 4),
                    "interference_score": round(interference_score, 4),
                    "manifestation_mode": manifestation_mode,
                    "support_origin": support_origin,
                    "branch_disturbance_score": round(float(case.get("branch_disturbance_score") or 0.0), 4),
                    "stem_competition_score": round(float(case.get("stem_competition_score") or 0.0), 4),
                },
            )
    return stem_cases
