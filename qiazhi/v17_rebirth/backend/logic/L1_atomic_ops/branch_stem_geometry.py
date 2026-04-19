"""
V17.13：从备份 `sub_branch_condition_eval.py` / `op_stem_fusion.py` 搬运的纯判定表与几何检测（无 Abs 副作用）。
供 L1 manifest hydration 与 Facts 显影使用。
"""
from __future__ import annotations

from typing import Any, Dict, List, Mapping, Optional, Sequence, Set, Tuple

# --- 与备份 `SANHE_GROUPS` / `SANXING_EDGES` / 六冲六害六破表一致 ---

SANHE_GROUPS: Tuple[frozenset[str], ...] = (
    frozenset({"寅", "午", "戌"}),
    frozenset({"申", "子", "辰"}),
    frozenset({"亥", "卯", "未"}),
    frozenset({"巳", "酉", "丑"}),
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

BANHE_TRIPLE: Tuple[Tuple[str, str, str], ...] = (
    ("申", "子", "water"),
    ("子", "辰", "water"),
    ("亥", "卯", "wood"),
    ("卯", "未", "wood"),
    ("寅", "午", "fire"),
    ("午", "戌", "fire"),
    ("巳", "酉", "metal"),
    ("酉", "丑", "metal"),
)

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
    for group in SANHE_GROUPS:
        if not set(group).issubset(present):
            continue
        matched = [(p, br) for p, br in branches.items() if br in group]
        pillars = [p for p, _br in matched]
        matched_branches = [br for _p, br in matched]
        branch_counts: Dict[str, int] = {}
        for br in matched_branches:
            branch_counts[br] = branch_counts.get(br, 0) + 1
        mid_branches = [br for br in group if br in {"子", "午", "卯", "酉"}]
        mid_branch = mid_branches[0] if mid_branches else group[0]
        pivot_factor = max(
            [float(scope_weights.get(p, 0.9)) for p, br in matched if br == mid_branch] or [0.9]
        )
        duplicate_count = max(0, len(matched_branches) - len(set(group)))
        strength = round(1.0 + 0.16 * duplicate_count + 0.14 * max(0.0, pivot_factor - 0.9), 3)
        hits.append(
            {
                "group": sorted(group),
                "pillars": pillars,
                "matched_branches": matched_branches,
                "branch_counts": branch_counts,
                "mid_branch": mid_branch,
                "duplicate_count": duplicate_count,
                "pivot_factor": round(pivot_factor, 3),
                "strength": strength,
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
    for a, b, _el in BANHE_TRIPLE:
        if a not in present or b not in present:
            continue
        if sanhe_group_complete_for_pair(a, b, present):
            continue
        pa = next((p for p, br in branches.items() if br == a), "")
        pb = next((p for p, br in branches.items() if br == b), "")
        if pa and pb and pa != pb:
            hits.append({"pair": sorted([a, b]), "pillars": sorted([pa, pb])})
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


def detect_stem_fusion_cases(
    stems: Mapping[str, str],
    branches: Mapping[str, str],
    *,
    branch_support_ratio: float = 0.26,
) -> List[Dict[str, Any]]:
    """
    自备份 `apply_op_stem_fusion`：邻柱五合是否化真 / 羁绊（无张量改写，仅结构化结果）。
    """
    thr = max(0.15, min(0.85, float(branch_support_ratio)))
    month_stem = str(stems.get("month") or "")
    cases: List[Dict[str, Any]] = []
    for pa, pb in _ADJ_PILLARS:
        sa, sb = str(stems.get(pa) or ""), str(stems.get(pb) or "")
        row = _fusion_row(sa, sb)
        if not row:
            continue
        _, _, hua_el = row
        month_el = STEM_TO_ELEMENT.get(month_stem, "")
        branch_ratio = _branch_hua_ratio(branches, hua_el)
        month_supports = month_el == hua_el
        transform_ok = month_supports or branch_ratio >= thr
        cases.append(
            {
                "pillars": [pa, pb],
                "stems": [sa, sb],
                "mode": "transformed" if transform_ok else "stuck",
                "hua_element": hua_el,
                "month_stem_supports": month_supports,
                "branch_hua_ratio": round(branch_ratio, 4),
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
