from __future__ import annotations

from typing import Any, Dict, List, Mapping, Tuple

from v17_rebirth.backend.logic.L1_atomic_ops.relation_geometry_pairs import pillars_branches_set


SANHE_GROUP_ROWS: Tuple[Tuple[str, str, str, str], ...] = (
    ("寅", "午", "戌", "fire"),
    ("申", "子", "辰", "water"),
    ("亥", "卯", "未", "wood"),
    ("巳", "酉", "丑", "metal"),
)

SANHE_GROUPS: Tuple[frozenset[str], ...] = tuple(
    frozenset({starter, pivot, tomb})
    for starter, pivot, tomb, _element in SANHE_GROUP_ROWS
)

BANHE_SHENGWANG_ROWS: Tuple[Tuple[str, str, str, str], ...] = (
    ("申", "子", "water", "sanhe_water"),
    ("亥", "卯", "wood", "sanhe_wood"),
    ("寅", "午", "fire", "sanhe_fire"),
    ("巳", "酉", "metal", "sanhe_metal"),
)

BANHE_MUWANG_ROWS: Tuple[Tuple[str, str, str, str], ...] = (
    ("子", "辰", "water", "sanhe_water"),
    ("卯", "未", "wood", "sanhe_wood"),
    ("午", "戌", "fire", "sanhe_fire"),
    ("酉", "丑", "metal", "sanhe_metal"),
)

GONGHE_ROWS: Tuple[Tuple[str, str, str, str], ...] = (
    ("申", "辰", "water", "sanhe_water"),
    ("亥", "未", "wood", "sanhe_wood"),
    ("寅", "戌", "fire", "sanhe_fire"),
    ("巳", "丑", "metal", "sanhe_metal"),
)

_SANHE_GROUP_BY_FAMILY: Dict[str, Tuple[str, str, str]] = {}
for _starter, _pivot, _tomb, _element in SANHE_GROUP_ROWS:
    _family = f"sanhe_{_element}"
    _SANHE_GROUP_BY_FAMILY[_family] = (_starter, _pivot, _tomb)

_BANHE_PAIR_META: Dict[frozenset[str], Dict[str, str]] = {}
for _a, _b, _element, _family in BANHE_SHENGWANG_ROWS:
    _starter, _pivot, _tomb = _SANHE_GROUP_BY_FAMILY[_family]
    _BANHE_PAIR_META[frozenset({_a, _b})] = {
        "pair_kind": "shengwang",
        "element": _element,
        "family": _family,
        "starter_branch": _starter,
        "pivot_branch": _pivot,
        "tomb_branch": _tomb,
    }
for _a, _b, _element, _family in BANHE_MUWANG_ROWS:
    _starter, _pivot, _tomb = _SANHE_GROUP_BY_FAMILY[_family]
    _BANHE_PAIR_META[frozenset({_a, _b})] = {
        "pair_kind": "muwang",
        "element": _element,
        "family": _family,
        "starter_branch": _starter,
        "pivot_branch": _pivot,
        "tomb_branch": _tomb,
    }

_GONGHE_PAIR_META: Dict[frozenset[str], Dict[str, str]] = {}
for _a, _b, _element, _family in GONGHE_ROWS:
    _starter, _pivot, _tomb = _SANHE_GROUP_BY_FAMILY[_family]
    _GONGHE_PAIR_META[frozenset({_a, _b})] = {
        "pair_kind": "gonghe",
        "element": _element,
        "family": _family,
        "starter_branch": _starter,
        "pivot_branch": _pivot,
        "tomb_branch": _tomb,
    }


def eval_sanhe_hits(branches: Mapping[str, str]) -> List[Dict[str, Any]]:
    present = pillars_branches_set(branches)
    hits: List[Dict[str, Any]] = []
    scope_weights = {
        "year": 0.88,
        "month": 1.15,
        "day": 0.95,
        "hour": 1.0,
        "luck": 1.05,
        "flow": 0.78,
    }
    role_duplicate_bonus = {"pivot": 0.30, "tomb": 0.18, "starter": 0.10}
    for starter, pivot, tomb, element in SANHE_GROUP_ROWS:
        group = frozenset({starter, pivot, tomb})
        if not set(group).issubset(present):
            continue
        matched = [(p, br) for p, br in branches.items() if br in group]
        pillars = [p for p, _br in matched]
        matched_branches = [br for _p, br in matched]
        branch_counts: Dict[str, int] = {}
        for br in matched_branches:
            branch_counts[br] = branch_counts.get(br, 0) + 1
        pivot_factor = max(
            [float(scope_weights.get(p, 0.9)) for p, br in matched if br == pivot] or [0.9]
        )
        duplicate_count = max(0, len(matched_branches) - len(set(group)))
        duplicate_roles: Dict[str, Dict[str, Any]] = {}
        duplicate_bonus = 0.0
        role_map = {starter: "starter", pivot: "pivot", tomb: "tomb"}
        for br, count in branch_counts.items():
            extra_count = max(0, int(count) - 1)
            if extra_count <= 0:
                continue
            role = role_map.get(br, "starter")
            bonus = float(role_duplicate_bonus.get(role, 0.10)) * extra_count
            duplicate_bonus += bonus
            duplicate_roles[br] = {
                "role": role,
                "extra_count": extra_count,
                "bonus": round(bonus, 3),
            }
        strength = round(1.0 + duplicate_bonus + 0.14 * max(0.0, pivot_factor - 0.9), 3)
        hits.append(
            {
                "group": sorted(group),
                "ordered_group": [starter, pivot, tomb],
                "pillars": pillars,
                "matched_branches": matched_branches,
                "branch_counts": branch_counts,
                "mid_branch": pivot,
                "pivot_branch": pivot,
                "tomb_branch": tomb,
                "duplicate_count": duplicate_count,
                "duplicate_bonus": round(duplicate_bonus, 3),
                "duplicate_roles": duplicate_roles,
                "role_map": role_map,
                "pivot_factor": round(pivot_factor, 3),
                "strength": strength,
                "element": element,
            }
        )
    return hits


def sanhe_group_complete_for_pair(br1: str, br2: str, present: set[str]) -> bool:
    for g in SANHE_GROUPS:
        if br1 in g and br2 in g:
            return set(g).issubset(present)
    return False


def eval_banhe_hits(branches: Mapping[str, str]) -> List[Dict[str, Any]]:
    present = set(branches.values())
    hits: List[Dict[str, Any]] = []
    for pair_meta in _BANHE_PAIR_META.values():
        a = str(pair_meta.get("starter_branch") or "")
        b = str(pair_meta.get("pivot_branch") or "")
        if pair_meta.get("pair_kind") == "muwang":
            a = str(pair_meta.get("pivot_branch") or "")
            b = str(pair_meta.get("tomb_branch") or "")
        if a not in present or b not in present:
            continue
        if sanhe_group_complete_for_pair(a, b, present):
            continue
        matched = [(p, br) for p, br in branches.items() if br in {a, b}]
        pillars = [p for p, _br in matched]
        branch_counts: Dict[str, int] = {}
        for _pillar, branch in matched:
            branch_counts[branch] = branch_counts.get(branch, 0) + 1
        role_map = {
            a: "starter" if pair_meta.get("pair_kind") == "shengwang" else "pivot",
            b: "pivot" if pair_meta.get("pair_kind") == "shengwang" else "tomb",
        }
        if len(set(pillars)) >= 2:
            hits.append(
                {
                    "pair": sorted([a, b]),
                    "ordered_pair": [a, b],
                    "pillars": pillars,
                    "matched_branches": [br for _p, br in matched],
                    "branch_counts": branch_counts,
                    "pair_kind": str(pair_meta.get("pair_kind") or "banhe"),
                    "element": str(pair_meta.get("element") or ""),
                    "family": str(pair_meta.get("family") or ""),
                    "starter_branch": str(pair_meta.get("starter_branch") or ""),
                    "pivot_branch": str(pair_meta.get("pivot_branch") or ""),
                    "tomb_branch": str(pair_meta.get("tomb_branch") or ""),
                    "role_map": role_map,
                }
            )
    return hits


def eval_gonghe_hits(branches: Mapping[str, str]) -> List[Dict[str, Any]]:
    present = set(branches.values())
    hits: List[Dict[str, Any]] = []
    for pair, pair_meta in _GONGHE_PAIR_META.items():
        a, b = sorted(pair)
        if a not in present or b not in present:
            continue
        if sanhe_group_complete_for_pair(a, b, present):
            continue
        matched = [(p, br) for p, br in branches.items() if br in pair]
        pillars = [p for p, _br in matched]
        branch_counts: Dict[str, int] = {}
        for _pillar, branch in matched:
            branch_counts[branch] = branch_counts.get(branch, 0) + 1
        if len(set(pillars)) < 2:
            continue
        hits.append(
            {
                "pair": [a, b],
                "ordered_pair": [a, b],
                "pillars": pillars,
                "matched_branches": [br for _p, br in matched],
                "branch_counts": branch_counts,
                "pair_kind": "gonghe",
                "element": str(pair_meta.get("element") or ""),
                "family": str(pair_meta.get("family") or ""),
                "starter_branch": str(pair_meta.get("starter_branch") or ""),
                "pivot_branch": str(pair_meta.get("pivot_branch") or ""),
                "tomb_branch": str(pair_meta.get("tomb_branch") or ""),
                "role_map": {a: "starter", b: "tomb"},
            }
        )
    return hits
