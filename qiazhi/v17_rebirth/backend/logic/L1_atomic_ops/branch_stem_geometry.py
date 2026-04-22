"""
V17.13：从备份 `sub_branch_condition_eval.py` / `op_stem_fusion.py` 搬运的纯判定表与几何检测（无 Abs 副作用）。
供 L1 manifest hydration 与 Facts 显影使用。
"""
from __future__ import annotations

from typing import Any, Dict, List, Mapping, Optional, Sequence, Set, Tuple


def _get_l0_consts() -> Dict[str, Any]:
    from v17_rebirth.backend.logic.configs.manager import get_v17_constants

    return get_v17_constants().get("L0_FOUNDATION", {})


def _get_l0_val(key: str, default: float) -> float:
    return float(_get_l0_consts().get(key, default))

# --- 与备份 `SANHE_GROUPS` / `SANXING_EDGES` / 六冲六害六破表一致 ---

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

SANXING_EDGES: Tuple[Tuple[str, str], ...] = (
    ("寅", "巳"),
    ("巳", "申"),
    ("寅", "申"),
    ("丑", "戌"),
    ("戌", "未"),
    ("丑", "未"),
    ("子", "卯"),
)

LIUHE_PAIRS: Tuple[Tuple[str, str], ...] = (
    ("子", "丑"),
    ("寅", "亥"),
    ("卯", "戌"),
    ("辰", "酉"),
    ("巳", "申"),
    ("午", "未"),
)

ANHE_PAIR_SETS: Tuple[frozenset[str], ...] = (
    frozenset({"子", "巳"}),
    frozenset({"丑", "午"}),
    frozenset({"寅", "未"}),
    frozenset({"卯", "申"}),
    frozenset({"亥", "午"}),
)

LIU_CHONG_PAIRS: Tuple[Tuple[str, str], ...] = (
    ("子", "午"),
    ("丑", "未"),
    ("寅", "申"),
    ("卯", "酉"),
    ("辰", "戌"),
    ("巳", "亥"),
)

LIU_HAI_PAIRS: Tuple[Tuple[str, str], ...] = (
    ("子", "未"),
    ("丑", "午"),
    ("寅", "巳"),
    ("卯", "辰"),
    ("申", "亥"),
    ("酉", "戌"),
)

LIU_PO_PAIRS: Tuple[Tuple[str, str], ...] = (
    ("子", "酉"),
    ("午", "卯"),
    ("寅", "亥"),
    ("巳", "申"),
    ("辰", "丑"),
    ("戌", "未"),
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

_SANHE_ROLE_BY_BRANCH: Dict[str, str] = {}
_SANHE_GROUP_BY_FAMILY: Dict[str, Tuple[str, str, str]] = {}
_SANHE_ELEMENT_BY_FAMILY: Dict[str, str] = {}
for _starter, _pivot, _tomb, _element in SANHE_GROUP_ROWS:
    _family = f"sanhe_{_element}"
    _SANHE_GROUP_BY_FAMILY[_family] = (_starter, _pivot, _tomb)
    _SANHE_ELEMENT_BY_FAMILY[_family] = _element
    _SANHE_ROLE_BY_BRANCH[_starter] = "starter"
    _SANHE_ROLE_BY_BRANCH[_pivot] = "pivot"
    _SANHE_ROLE_BY_BRANCH[_tomb] = "tomb"

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

_FUSION_ROWS: Tuple[Tuple[str, str, str], ...] = (
    ("甲", "己", "earth"),
    ("乙", "庚", "metal"),
    ("丙", "辛", "water"),
    ("丁", "壬", "wood"),
    ("戊", "癸", "fire"),
)

_ADJ_PILLARS: Tuple[Tuple[str, str], ...] = (
    ("year", "month"),
    ("month", "day"),
    ("day", "hour"),
    ("month", "luck"),
    ("luck", "flow"),
)

_BRANCH_DOMINANT_ELEMENT: Dict[str, str] = {
    "子": "water",
    "丑": "earth",
    "寅": "wood",
    "卯": "wood",
    "辰": "earth",
    "巳": "fire",
    "午": "fire",
    "未": "earth",
    "申": "metal",
    "酉": "metal",
    "戌": "earth",
    "亥": "water",
}

STEM_TO_ELEMENT: Dict[str, str] = {
    "甲": "wood",
    "乙": "wood",
    "丙": "fire",
    "丁": "fire",
    "戊": "earth",
    "己": "earth",
    "庚": "metal",
    "辛": "metal",
    "壬": "water",
    "癸": "water",
}

BRANCH_HIDDEN_STEMS: Dict[str, Tuple[Tuple[str, float], ...]] = {
    "子": (("癸", 1.00),),
    "丑": (("己", 0.60), ("癸", 0.20), ("辛", 0.20)),
    "寅": (("甲", 0.70), ("丙", 0.20), ("戊", 0.10)),
    "卯": (("乙", 1.00),),
    "辰": (("戊", 0.60), ("乙", 0.20), ("癸", 0.20)),
    "巳": (("丙", 0.70), ("庚", 0.20), ("戊", 0.10)),
    "午": (("丁", 0.70), ("己", 0.30)),
    "未": (("己", 0.60), ("丁", 0.20), ("乙", 0.20)),
    "申": (("庚", 0.70), ("壬", 0.20), ("戊", 0.10)),
    "酉": (("辛", 1.00),),
    "戌": (("戊", 0.60), ("辛", 0.20), ("丁", 0.20)),
    "亥": (("壬", 0.70), ("甲", 0.30)),
}

STEM_FUSION_VISIBLE_SUPPORT_MONTH: float = 1.00
STEM_FUSION_VISIBLE_SUPPORT_DAY: float = 0.82
STEM_FUSION_VISIBLE_SUPPORT_HOUR: float = 0.66
STEM_FUSION_VISIBLE_SUPPORT_YEAR: float = 0.52
STEM_FUSION_VISIBLE_SUPPORT_LUCK: float = 0.72
STEM_FUSION_VISIBLE_SUPPORT_FLOW: float = 0.48
STEM_FUSION_BRANCH_ROOT_MONTH: float = 1.00
STEM_FUSION_BRANCH_ROOT_DAY: float = 0.84
STEM_FUSION_BRANCH_ROOT_HOUR: float = 0.68
STEM_FUSION_BRANCH_ROOT_YEAR: float = 0.56
STEM_FUSION_BRANCH_ROOT_LUCK: float = 0.86
STEM_FUSION_BRANCH_ROOT_FLOW: float = 0.60
STEM_FUSION_SUPPORT_VISIBLE_WEIGHT: float = 0.62
STEM_FUSION_SUPPORT_BRANCH_WEIGHT: float = 0.38
STEM_FUSION_INTERFERENCE_BRANCH_WEIGHT: float = 0.72
STEM_FUSION_INTERFERENCE_STEM_WEIGHT: float = 0.45
STEM_FUSION_EFFECTIVE_THRESHOLD: float = 0.26

_STEM_FUSION_VISIBLE_SUPPORT_WEIGHTS: Dict[str, str] = {
    "year": "STEM_FUSION_VISIBLE_SUPPORT_YEAR",
    "month": "STEM_FUSION_VISIBLE_SUPPORT_MONTH",
    "day": "STEM_FUSION_VISIBLE_SUPPORT_DAY",
    "hour": "STEM_FUSION_VISIBLE_SUPPORT_HOUR",
    "luck": "STEM_FUSION_VISIBLE_SUPPORT_LUCK",
    "flow": "STEM_FUSION_VISIBLE_SUPPORT_FLOW",
}

_STEM_FUSION_VISIBLE_SUPPORT_DEFAULTS: Dict[str, float] = {
    "year": STEM_FUSION_VISIBLE_SUPPORT_YEAR,
    "month": STEM_FUSION_VISIBLE_SUPPORT_MONTH,
    "day": STEM_FUSION_VISIBLE_SUPPORT_DAY,
    "hour": STEM_FUSION_VISIBLE_SUPPORT_HOUR,
    "luck": STEM_FUSION_VISIBLE_SUPPORT_LUCK,
    "flow": STEM_FUSION_VISIBLE_SUPPORT_FLOW,
}

_STEM_FUSION_BRANCH_ROOT_WEIGHTS: Dict[str, str] = {
    "year": "STEM_FUSION_BRANCH_ROOT_YEAR",
    "month": "STEM_FUSION_BRANCH_ROOT_MONTH",
    "day": "STEM_FUSION_BRANCH_ROOT_DAY",
    "hour": "STEM_FUSION_BRANCH_ROOT_HOUR",
    "luck": "STEM_FUSION_BRANCH_ROOT_LUCK",
    "flow": "STEM_FUSION_BRANCH_ROOT_FLOW",
}

_STEM_FUSION_BRANCH_ROOT_DEFAULTS: Dict[str, float] = {
    "year": STEM_FUSION_BRANCH_ROOT_YEAR,
    "month": STEM_FUSION_BRANCH_ROOT_MONTH,
    "day": STEM_FUSION_BRANCH_ROOT_DAY,
    "hour": STEM_FUSION_BRANCH_ROOT_HOUR,
    "luck": STEM_FUSION_BRANCH_ROOT_LUCK,
    "flow": STEM_FUSION_BRANCH_ROOT_FLOW,
}


def pillars_branches_set(branches: Mapping[str, str]) -> Set[str]:
    return {str(v) for v in branches.values() if v}


def _pillar_keys() -> Tuple[str, ...]:
    return ("year", "month", "day", "hour")


def _extended_pillar_keys() -> Tuple[str, ...]:
    return ("year", "month", "day", "hour", "luck", "flow")


def eval_branch_pair_hits(
    branches: Mapping[str, str],
    pairs: Tuple[Tuple[str, str], ...],
) -> List[Dict[str, Any]]:
    present = pillars_branches_set(branches)
    hits: List[Dict[str, Any]] = []
    for a, b in pairs:
        if a not in present or b not in present:
            continue
        pa = next((p for p, br in branches.items() if br == a), "")
        pb = next((p for p, br in branches.items() if br == b), "")
        if pa and pb and pa != pb:
            hits.append({"pair": sorted([a, b]), "pillars": sorted([pa, pb])})
    return hits


def eval_liuhe_hits(branches: Mapping[str, str]) -> List[Dict[str, Any]]:
    present = pillars_branches_set(branches)
    hits: List[Dict[str, Any]] = []
    for a, b in LIUHE_PAIRS:
        if a not in present or b not in present:
            continue
        pa = next((p for p, br in branches.items() if br == a), "")
        pb = next((p for p, br in branches.items() if br == b), "")
        if pa and pb and pa != pb:
            hits.append({"pair": [a, b], "pillars": sorted([pa, pb])})
    return hits


def eval_anhe_hits(branches: Mapping[str, str]) -> List[Dict[str, Any]]:
    present = pillars_branches_set(branches)
    hits: List[Dict[str, Any]] = []
    for pair in ANHE_PAIR_SETS:
        if not pair.issubset(present):
            continue
        a, b = sorted(pair)
        pa = next((p for p, br in branches.items() if br == a), "")
        pb = next((p for p, br in branches.items() if br == b), "")
        if pa and pb and pa != pb:
            hits.append({"pair": [a, b], "pillars": sorted([pa, pb])})
    return hits


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


def sanhe_group_complete_for_pair(br1: str, br2: str, present: Set[str]) -> bool:
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


def eval_liu_chong_hits(branches: Mapping[str, str]) -> List[Dict[str, Any]]:
    return eval_branch_pair_hits(branches, LIU_CHONG_PAIRS)


def eval_liu_hai_hits(branches: Mapping[str, str]) -> List[Dict[str, Any]]:
    return eval_branch_pair_hits(branches, LIU_HAI_PAIRS)


def eval_liu_po_hits(branches: Mapping[str, str]) -> List[Dict[str, Any]]:
    return eval_branch_pair_hits(branches, LIU_PO_PAIRS)


def sanxing_detect_geometry(branches: Mapping[str, str]) -> List[Dict[str, Any]]:
    present = pillars_branches_set(branches)
    hits: List[Dict[str, Any]] = []
    seen: Set[Tuple[str, str]] = set()
    for b1, b2 in SANXING_EDGES:
        if b1 not in present or b2 not in present:
            continue
        key = tuple(sorted((b1, b2)))
        if key in seen:
            continue
        seen.add(key)
        pa = next((p for p, br in branches.items() if br == b1), "")
        pb = next((p for p, br in branches.items() if br == b2), "")
        if pa and pb and pa != pb:
            hits.append({"edge": sorted([pa, pb]), "branches": sorted([b1, b2])})
    return hits


def _fusion_row(a: str, b: str) -> Optional[Tuple[str, str, str]]:
    if not a or not b:
        return None
    s = frozenset({a, b})
    for x, y, hua in _FUSION_ROWS:
        if s == frozenset({x, y}):
            return (x, y, hua)
    return None


def _branch_hua_ratio(branches: Mapping[str, str], hua_el: str) -> float:
    if not branches:
        return 0.0
    n = 0
    hit = 0
    for br in branches.values():
        if not br:
            continue
        n += 1
        if _BRANCH_DOMINANT_ELEMENT.get(str(br), "") == hua_el:
            hit += 1
    return hit / max(1, n)


def _stem_fusion_visible_weight(scope: str) -> float:
    key = _STEM_FUSION_VISIBLE_SUPPORT_WEIGHTS.get(str(scope or "").strip(), "")
    default = _STEM_FUSION_VISIBLE_SUPPORT_DEFAULTS.get(str(scope or "").strip(), STEM_FUSION_VISIBLE_SUPPORT_YEAR)
    return _get_l0_val(key, default) if key else float(default)


def _stem_fusion_branch_weight(scope: str) -> float:
    key = _STEM_FUSION_BRANCH_ROOT_WEIGHTS.get(str(scope or "").strip(), "")
    default = _STEM_FUSION_BRANCH_ROOT_DEFAULTS.get(str(scope or "").strip(), STEM_FUSION_BRANCH_ROOT_YEAR)
    return _get_l0_val(key, default) if key else float(default)


def _branch_hidden_element_weight(branch: str, hua_el: str) -> float:
    total = 0.0
    for hidden_stem, weight in BRANCH_HIDDEN_STEMS.get(str(branch or "").strip(), ()):
        if STEM_TO_ELEMENT.get(hidden_stem, "") == hua_el:
            total += float(weight)
    return total


def _branch_root_support_ratio(branches: Mapping[str, str], hua_el: str) -> float:
    if not branches or not hua_el:
        return 0.0
    support = 0.0
    scope_total = 0.0
    for scope, branch in branches.items():
        if not branch:
            continue
        scope_weight = _stem_fusion_branch_weight(scope)
        scope_total += scope_weight
        support += scope_weight * _branch_hidden_element_weight(str(branch), hua_el)
    if scope_total <= 0.0:
        return 0.0
    return max(0.0, min(1.0, support / scope_total))


def _visible_support_snapshot(
    stems: Mapping[str, str],
    *,
    hua_el: str,
) -> Tuple[float, str]:
    support_rows: List[Tuple[float, str]] = []
    for scope, stem in stems.items():
        if not stem or STEM_TO_ELEMENT.get(str(stem), "") != hua_el:
            continue
        support_rows.append((_stem_fusion_visible_weight(str(scope)), str(scope)))
    if not support_rows:
        return 0.0, ""
    support_rows.sort(key=lambda item: item[0], reverse=True)
    top_weight, top_scope = support_rows[0]
    tail_weight = sum(weight for weight, _scope in support_rows[1:])
    strength = min(1.0, top_weight + tail_weight * 0.28)
    return round(strength, 4), top_scope


def _stem_fusion_branch_disturbance(
    branches: Mapping[str, str],
    *,
    pair_pillars: Sequence[str],
) -> float:
    active_pillars = {str(item).strip() for item in pair_pillars if str(item).strip()}
    if not active_pillars:
        return 0.0
    severity_sum = 0.0
    scored: Set[Tuple[str, Tuple[str, ...]]] = set()
    families: Sequence[Tuple[str, List[Dict[str, Any]], str]] = (
        ("chong", eval_liu_chong_hits(branches), "pillars"),
        ("hai", eval_liu_hai_hits(branches), "pillars"),
        ("po", eval_liu_po_hits(branches), "pillars"),
        ("xing", sanxing_detect_geometry(branches), "edge"),
    )
    severity_weights = {
        "chong": 0.34,
        "xing": 0.28,
        "hai": 0.22,
        "po": 0.18,
    }
    for family, hits, pillar_key in families:
        for row in hits:
            pillars = tuple(sorted(str(item).strip() for item in (row.get(pillar_key) or []) if str(item).strip()))
            if not pillars or not (active_pillars & set(pillars)):
                continue
            sig = (family, pillars)
            if sig in scored:
                continue
            scored.add(sig)
            touched = len(active_pillars & set(pillars))
            severity_sum += severity_weights.get(family, 0.2) * (0.72 + 0.28 * touched / max(1, len(active_pillars)))
    return max(0.0, min(1.0, severity_sum / max(1.0, len(active_pillars))))


def _stem_fusion_stem_competition(
    stems: Mapping[str, str],
    *,
    pair_pillars: Sequence[str],
    pair_stems: Sequence[str],
) -> float:
    active_pillars = {str(item).strip() for item in pair_pillars if str(item).strip()}
    active_stems = [str(item).strip() for item in pair_stems if str(item).strip()]
    if not active_stems:
        return 0.0
    competition = 0.0
    for scope, stem in stems.items():
        if str(scope).strip() in active_pillars:
            continue
        if str(stem).strip() in active_stems:
            competition += 0.26
    return max(0.0, min(1.0, competition))


def detect_stem_fusion_cases(
    stems: Mapping[str, str],
    branches: Mapping[str, str],
    *,
    branch_support_ratio: float = 0.26,
) -> List[Dict[str, Any]]:
    """
    自备份 `apply_op_stem_fusion`：邻柱五合是否化真 / 羁绊（无张量改写，仅结构化结果）。
    """
    thr = max(
        0.15,
        min(
            0.85,
            max(
                float(branch_support_ratio),
                _get_l0_val("STEM_FUSION_EFFECTIVE_THRESHOLD", STEM_FUSION_EFFECTIVE_THRESHOLD),
            ),
        ),
    )
    cases: List[Dict[str, Any]] = []
    for pa, pb in _ADJ_PILLARS:
        sa, sb = str(stems.get(pa) or ""), str(stems.get(pb) or "")
        row = _fusion_row(sa, sb)
        if not row:
            continue
        _, _, hua_el = row
        visible_support_strength, visible_support_scope = _visible_support_snapshot(stems, hua_el=hua_el)
        branch_ratio = _branch_root_support_ratio(branches, hua_el)
        legacy_branch_ratio = _branch_hua_ratio(branches, hua_el)
        branch_disturbance_score = _stem_fusion_branch_disturbance(branches, pair_pillars=[pa, pb])
        stem_competition_score = _stem_fusion_stem_competition(
            stems,
            pair_pillars=[pa, pb],
            pair_stems=[sa, sb],
        )
        support_visible_weight = _get_l0_val("STEM_FUSION_SUPPORT_VISIBLE_WEIGHT", STEM_FUSION_SUPPORT_VISIBLE_WEIGHT)
        support_branch_weight = _get_l0_val("STEM_FUSION_SUPPORT_BRANCH_WEIGHT", STEM_FUSION_SUPPORT_BRANCH_WEIGHT)
        interference_branch_weight = _get_l0_val(
            "STEM_FUSION_INTERFERENCE_BRANCH_WEIGHT",
            STEM_FUSION_INTERFERENCE_BRANCH_WEIGHT,
        )
        interference_stem_weight = _get_l0_val(
            "STEM_FUSION_INTERFERENCE_STEM_WEIGHT",
            STEM_FUSION_INTERFERENCE_STEM_WEIGHT,
        )
        support_score = max(
            0.0,
            min(
                1.0,
                visible_support_strength * support_visible_weight + branch_ratio * support_branch_weight,
            ),
        )
        interference_score = max(
            0.0,
            min(
                1.0,
                branch_disturbance_score * interference_branch_weight + stem_competition_score * interference_stem_weight,
            ),
        )
        effective_support_score = max(
            0.0,
            min(1.0, support_score * (1.0 - interference_score * 0.58)),
        )
        month_supports = visible_support_scope == "month"
        manifestation_mode = "明化" if visible_support_strength >= 0.16 else "暗化"
        if visible_support_scope:
            support_origin = f"{visible_support_scope}_visible"
        elif branch_ratio >= thr:
            support_origin = "branch_root"
        else:
            support_origin = "insufficient_support"
        transform_ok = effective_support_score >= thr or (month_supports and support_score >= max(0.18, thr * 0.82))
        cases.append(
            {
                "pillars": [pa, pb],
                "stems": [sa, sb],
                "mode": "transformed" if transform_ok else "stuck",
                "hua_element": hua_el,
                "month_stem_supports": month_supports,
                "branch_hua_ratio": round(branch_ratio if branch_ratio > 0.0 else legacy_branch_ratio, 4),
                "branch_root_ratio": round(branch_ratio, 4),
                "visible_support_strength": round(visible_support_strength, 4),
                "visible_support_scope": visible_support_scope,
                "support_score": round(support_score, 4),
                "effective_support_score": round(effective_support_score, 4),
                "branch_disturbance_score": round(branch_disturbance_score, 4),
                "stem_competition_score": round(stem_competition_score, 4),
                "interference_score": round(interference_score, 4),
                "manifestation_mode": manifestation_mode,
                "support_origin": support_origin,
            }
        )
    return cases


def parse_ganzhi_pillar(gz: str) -> Tuple[str, str]:
    s = str(gz or "").strip()
    if len(s) < 2:
        return "", ""
    return s[0], s[1]


def branches_and_stems_from_four_pillars(four: Any) -> Tuple[Dict[str, str], Dict[str, str]]:
    out_b: Dict[str, str] = {}
    out_s: Dict[str, str] = {}
    if not isinstance(four, dict):
        return out_b, out_s
    for key in _pillar_keys():
        raw = four.get(key)
        if raw is None:
            continue
        if isinstance(raw, str):
            st, br = parse_ganzhi_pillar(raw)
        elif isinstance(raw, dict):
            st, br = str(raw.get("stem") or ""), str(raw.get("branch") or "")
        else:
            st, br = "", ""
        if br:
            out_b[key] = br
        if st:
            out_s[key] = st
    return out_b, out_s


def branches_and_stems_from_runtime_pillars(
    four: Any,
    *,
    luck_pillar: Any = None,
    flow_pillar: Any = None,
) -> Tuple[Dict[str, str], Dict[str, str]]:
    out_b, out_s = branches_and_stems_from_four_pillars(four)
    runtime_rows = {
        "luck": luck_pillar,
        "flow": flow_pillar,
    }
    for key in ("luck", "flow"):
        raw = runtime_rows.get(key)
        if raw is None:
            continue
        if isinstance(raw, str):
            st, br = parse_ganzhi_pillar(raw)
        elif isinstance(raw, dict):
            st, br = str(raw.get("stem") or ""), str(raw.get("branch") or "")
        else:
            st, br = "", ""
        if br:
            out_b[key] = br
        if st:
            out_s[key] = st
    return out_b, out_s


def summarize_sanxing_branches(hits: Sequence[Dict[str, Any]]) -> str:
    """无恩三刑等：合并边涉及的支名，去重排序。"""
    bag: Set[str] = set()
    for h in hits:
        for b in h.get("branches") or []:
            bag.add(str(b))
    return "".join(sorted(bag))
