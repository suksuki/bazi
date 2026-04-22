from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Set, Tuple


def collect_structured_relation_family_deltas(
    *,
    sanhe_hits: List[Dict[str, Any]],
    sanhui_hits: List[Dict[str, Any]],
    banhe_hits: List[Dict[str, Any]],
    gonghe_hits: List[Dict[str, Any]],
    liuhe_hits: List[Dict[str, Any]],
    anhe_hits: List[Dict[str, Any]],
    conflicted_branches: Set[str],
    conflict_events: Optional[List[Set[str]]],
    four_pillars: Dict[str, str],
    luck_pillar: str,
    flow_pillar: str,
    branch_scope_totals: Dict[str, float],
    relation_delta_raw: Dict[str, float],
    relation_traces: List[Dict[str, Any]],
    branch_hidden: Dict[str, List[Tuple[str, float]]],
    stem_element_map: Dict[str, str],
    banhe_pair_to_element: Dict[frozenset[str], str],
    gonghe_pair_to_element: Dict[frozenset[str], str],
    liuhe_pair_to_element: Dict[frozenset[str], str],
    pillars_group_closeness: Callable[[List[str]], float],
    relation_factor_bundle: Callable[..., Dict[str, Any]],
    relation_conflict_damping: Callable[..., float],
    relation_root_intensity: Callable[..., float],
    relation_duplicate_bonus: Callable[[Dict[str, Any], Dict[str, Any]], Tuple[float, Dict[str, Dict[str, Any]]]],
    relation_duplicate_role_bonus: Callable[[str], float],
    relation_apply_branch_delta: Callable[..., None],
    relation_dominant_hidden_stem: Callable[..., str],
    append_relation_trace: Callable[..., None],
) -> None:
    for hit in sanhe_hits:
        members = [str(b) for b in (hit.get("matched_branches") or hit.get("group") or []) if str(b).strip()]
        if not members:
            continue
        pillars = [str(p) for p in (hit.get("pillars") or []) if str(p).strip()]
        closeness = pillars_group_closeness(pillars)
        strength = float(hit.get("strength") or 1.0)
        role_map = hit.get("role_map") if isinstance(hit.get("role_map"), dict) else {}
        duplicate_bonus = max(0.0, float(hit.get("duplicate_bonus") or 0.0))
        mid_branch = str(hit.get("pivot_branch") or hit.get("mid_branch") or "")
        rel_element = ""
        dominant_hidden_stem = ""
        if mid_branch and branch_hidden.get(mid_branch):
            dominant_hidden_stem = branch_hidden[mid_branch][0][0]
            rel_element = stem_element_map.get(dominant_hidden_stem, "")
        factor_bundle = relation_factor_bundle(
            family_key="sanhe",
            relation_element=rel_element,
            members=members,
            dominant_hidden_stem=dominant_hidden_stem,
            four_pillars=four_pillars,
            luck_pillar=luck_pillar,
            flow_pillar=flow_pillar,
        )
        conflict_damping = relation_conflict_damping(
            members=members,
            family_key="sanhe",
            conflicted_branches=conflicted_branches,
            conflict_events=conflict_events,
        )
        intensity = relation_root_intensity(
            family_key="sanhe",
            closeness=closeness,
            strength=strength,
            duplicate_bonus=duplicate_bonus,
            conflict_damping=conflict_damping,
            family_factor=float(factor_bundle.get("effective_family_factor") or 0.0),
        )
        counts = hit.get("branch_counts") or {}
        for branch in set(members):
            extra_count = max(0, int((counts.get(branch) or 1) - 1))
            dup_factor = 1.0 + relation_duplicate_role_bonus(str(role_map.get(branch) or "starter")) * extra_count
            relation_apply_branch_delta(
                branch=branch,
                branch_scope_totals=branch_scope_totals,
                relation_element=rel_element,
                magnitude=intensity * dup_factor,
                out=relation_delta_raw,
            )
        append_relation_trace(
            relation_traces,
            "sanhe",
            members,
            pillars,
            intensity,
            rel_element,
            family_key="sanhe",
            duplicate_bonus=duplicate_bonus,
            conflict_damping=conflict_damping,
            details={
                "ordered_group": list(hit.get("ordered_group") or hit.get("group") or []),
                "pivot_branch": str(hit.get("pivot_branch") or hit.get("mid_branch") or ""),
                "tomb_branch": str(hit.get("tomb_branch") or ""),
                "closeness": round(closeness, 4),
                "strength": round(strength, 4),
                **factor_bundle,
                "role_map": role_map,
                "branch_counts": counts,
            },
        )

    for hit in sanhui_hits:
        members = [str(b) for b in (hit.get("matched_branches") or hit.get("group") or []) if str(b).strip()]
        if not members:
            continue
        pillars = [str(p) for p in (hit.get("pillars") or []) if str(p).strip()]
        closeness = pillars_group_closeness(pillars)
        completion = max(0.0, min(1.0, float(hit.get("completion") or 0.0)))
        strength = max(0.0, float(hit.get("strength") or 0.0))
        role_map = hit.get("role_map") if isinstance(hit.get("role_map"), dict) else {}
        duplicate_bonus = max(0.0, float(hit.get("duplicate_bonus") or 0.0))
        rel_element = str(hit.get("element") or "")
        dominant_hidden_stem = relation_dominant_hidden_stem(
            relation_element=rel_element,
            members=members,
            four_pillars=four_pillars,
            luck_pillar=luck_pillar,
            flow_pillar=flow_pillar,
        )
        factor_bundle = relation_factor_bundle(
            family_key="sanhui",
            relation_element=rel_element,
            members=members,
            dominant_hidden_stem=dominant_hidden_stem,
            four_pillars=four_pillars,
            luck_pillar=luck_pillar,
            flow_pillar=flow_pillar,
        )
        conflict_damping = relation_conflict_damping(
            members=members,
            family_key="sanhui",
            conflicted_branches=conflicted_branches,
            conflict_events=conflict_events,
        )
        intensity = relation_root_intensity(
            family_key="sanhui",
            closeness=closeness,
            strength=strength,
            completion=completion,
            duplicate_bonus=duplicate_bonus,
            conflict_damping=conflict_damping,
            family_factor=float(factor_bundle.get("effective_family_factor") or 0.0),
        )
        counts = hit.get("branch_counts") or {}
        for branch in set(members):
            extra_count = max(0, int((counts.get(branch) or 1) - 1))
            dup_factor = 1.0 + relation_duplicate_role_bonus(str(role_map.get(branch) or "starter")) * extra_count
            relation_apply_branch_delta(
                branch=branch,
                branch_scope_totals=branch_scope_totals,
                relation_element=rel_element,
                magnitude=intensity * dup_factor,
                out=relation_delta_raw,
            )
        append_relation_trace(
            relation_traces,
            "sanhui",
            members,
            pillars,
            intensity,
            rel_element,
            family_key="sanhui",
            duplicate_bonus=duplicate_bonus,
            conflict_damping=conflict_damping,
            completion=completion,
            details={
                "ordered_group": list(hit.get("ordered_group") or hit.get("group") or []),
                "pivot_branch": str(hit.get("pivot_branch") or ""),
                "tomb_branch": str(hit.get("tomb_branch") or ""),
                "closeness": round(closeness, 4),
                "strength": round(strength, 4),
                **factor_bundle,
                "role_map": role_map,
                "branch_counts": counts,
            },
        )

    for hit in banhe_hits:
        pair = [str(x) for x in (hit.get("pair") or []) if str(x).strip()]
        if len(pair) != 2:
            continue
        pillars = [str(p) for p in (hit.get("pillars") or []) if str(p).strip()]
        closeness = pillars_group_closeness(pillars)
        pair_kind = str(hit.get("pair_kind") or "banhe")
        family_key = "banhe_shengwang" if pair_kind == "shengwang" else "banhe_muwang"
        role_map = hit.get("role_map") if isinstance(hit.get("role_map"), dict) else {}
        counts = hit.get("branch_counts") or {}
        duplicate_bonus, _duplicate_roles = relation_duplicate_bonus(counts, role_map)
        rel_element = str(hit.get("element") or banhe_pair_to_element.get(frozenset(pair), ""))
        effective_members = [str(x) for x in (hit.get("matched_branches") or pair) if str(x).strip()]
        dominant_hidden_stem = relation_dominant_hidden_stem(
            relation_element=rel_element,
            members=effective_members,
            four_pillars=four_pillars,
            luck_pillar=luck_pillar,
            flow_pillar=flow_pillar,
        )
        factor_bundle = relation_factor_bundle(
            family_key=family_key,
            relation_element=rel_element,
            members=effective_members,
            dominant_hidden_stem=dominant_hidden_stem,
            four_pillars=four_pillars,
            luck_pillar=luck_pillar,
            flow_pillar=flow_pillar,
        )
        conflict_damping = relation_conflict_damping(
            members=effective_members,
            family_key=family_key,
            conflicted_branches=conflicted_branches,
            conflict_events=conflict_events,
        )
        intensity = relation_root_intensity(
            family_key=family_key,
            closeness=closeness,
            strength=1.0,
            duplicate_bonus=duplicate_bonus,
            conflict_damping=conflict_damping,
            family_factor=float(factor_bundle.get("effective_family_factor") or 0.0),
        )
        for branch in set(effective_members):
            extra_count = max(0, int((counts.get(branch) or 1) - 1))
            dup_factor = 1.0 + relation_duplicate_role_bonus(str(role_map.get(branch) or "starter")) * extra_count
            relation_apply_branch_delta(
                branch=branch,
                branch_scope_totals=branch_scope_totals,
                relation_element=rel_element,
                magnitude=intensity * dup_factor,
                out=relation_delta_raw,
            )
        append_relation_trace(
            relation_traces,
            "banhe",
            pair,
            pillars,
            intensity,
            rel_element,
            family_key=family_key,
            duplicate_bonus=duplicate_bonus,
            conflict_damping=conflict_damping,
            details={
                "pair_kind": pair_kind,
                "ordered_group": list(pair),
                "closeness": round(closeness, 4),
                "strength": 1.0,
                **factor_bundle,
                "role_map": role_map,
                "branch_counts": counts,
            },
        )

    for hit in gonghe_hits:
        pair = [str(x) for x in (hit.get("pair") or []) if str(x).strip()]
        if len(pair) != 2:
            continue
        pillars = [str(p) for p in (hit.get("pillars") or []) if str(p).strip()]
        closeness = pillars_group_closeness(pillars)
        role_map = hit.get("role_map") if isinstance(hit.get("role_map"), dict) else {}
        counts = hit.get("branch_counts") or {}
        duplicate_bonus, _duplicate_roles = relation_duplicate_bonus(counts, role_map)
        rel_element = str(hit.get("element") or gonghe_pair_to_element.get(frozenset(pair), ""))
        effective_members = [str(x) for x in (hit.get("matched_branches") or pair) if str(x).strip()]
        dominant_hidden_stem = relation_dominant_hidden_stem(
            relation_element=rel_element,
            members=effective_members,
            four_pillars=four_pillars,
            luck_pillar=luck_pillar,
            flow_pillar=flow_pillar,
        )
        factor_bundle = relation_factor_bundle(
            family_key="gonghe",
            relation_element=rel_element,
            members=effective_members,
            dominant_hidden_stem=dominant_hidden_stem,
            four_pillars=four_pillars,
            luck_pillar=luck_pillar,
            flow_pillar=flow_pillar,
        )
        conflict_damping = relation_conflict_damping(
            members=effective_members,
            family_key="gonghe",
            conflicted_branches=conflicted_branches,
            conflict_events=conflict_events,
        )
        intensity = relation_root_intensity(
            family_key="gonghe",
            closeness=closeness,
            strength=0.92,
            duplicate_bonus=duplicate_bonus,
            conflict_damping=conflict_damping,
            family_factor=float(factor_bundle.get("effective_family_factor") or 0.0),
        )
        for branch in set(effective_members):
            extra_count = max(0, int((counts.get(branch) or 1) - 1))
            dup_factor = 1.0 + relation_duplicate_role_bonus(str(role_map.get(branch) or "starter")) * extra_count
            relation_apply_branch_delta(
                branch=branch,
                branch_scope_totals=branch_scope_totals,
                relation_element=rel_element,
                magnitude=intensity * dup_factor,
                out=relation_delta_raw,
            )
        append_relation_trace(
            relation_traces,
            "gonghe",
            pair,
            pillars,
            intensity,
            rel_element,
            family_key="gonghe",
            duplicate_bonus=duplicate_bonus,
            conflict_damping=conflict_damping,
            details={
                "pair_kind": "gonghe",
                "ordered_group": list(pair),
                "closeness": round(closeness, 4),
                "strength": 0.92,
                **factor_bundle,
                "role_map": role_map,
                "branch_counts": counts,
            },
        )

    for hit in liuhe_hits:
        pair = [str(x) for x in (hit.get("pair") or []) if str(x).strip()]
        if len(pair) != 2:
            continue
        pillars = [str(p) for p in (hit.get("pillars") or []) if str(p).strip()]
        closeness = pillars_group_closeness(pillars)
        rel_element = liuhe_pair_to_element.get(frozenset(pair), "")
        dominant_hidden_stem = relation_dominant_hidden_stem(
            relation_element=rel_element,
            members=pair,
            four_pillars=four_pillars,
            luck_pillar=luck_pillar,
            flow_pillar=flow_pillar,
        )
        factor_bundle = relation_factor_bundle(
            family_key="liuhe",
            relation_element=rel_element,
            members=pair,
            dominant_hidden_stem=dominant_hidden_stem,
            four_pillars=four_pillars,
            luck_pillar=luck_pillar,
            flow_pillar=flow_pillar,
        )
        conflict_damping = relation_conflict_damping(
            members=pair,
            family_key="liuhe",
            conflicted_branches=conflicted_branches,
            conflict_events=conflict_events,
        )
        intensity = relation_root_intensity(
            family_key="liuhe",
            closeness=closeness,
            strength=0.96,
            conflict_damping=conflict_damping,
            family_factor=float(factor_bundle.get("effective_family_factor") or 0.0),
        )
        for branch in pair:
            relation_apply_branch_delta(
                branch=branch,
                branch_scope_totals=branch_scope_totals,
                relation_element=rel_element,
                magnitude=intensity,
                out=relation_delta_raw,
            )
        append_relation_trace(
            relation_traces,
            "liuhe",
            pair,
            pillars,
            intensity,
            rel_element,
            family_key="liuhe",
            conflict_damping=conflict_damping,
            details={
                "ordered_group": list(pair),
                "closeness": round(closeness, 4),
                "strength": 0.96,
                **factor_bundle,
            },
        )

    for hit in anhe_hits:
        pair = [str(x) for x in (hit.get("pair") or []) if str(x).strip()]
        if len(pair) != 2:
            continue
        pillars = [str(p) for p in (hit.get("pillars") or []) if str(p).strip()]
        closeness = pillars_group_closeness(pillars)
        conflict_damping = relation_conflict_damping(
            members=pair,
            family_key="anhe",
            conflicted_branches=conflicted_branches,
            conflict_events=conflict_events,
        )
        intensity = relation_root_intensity(
            family_key="anhe",
            closeness=closeness,
            strength=0.92,
            conflict_damping=conflict_damping,
        )
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
            "anhe",
            pair,
            pillars,
            intensity,
            "",
            family_key="anhe",
            conflict_damping=conflict_damping,
            details={
                "ordered_group": list(pair),
                "closeness": round(closeness, 4),
                "strength": 0.92,
            },
        )
