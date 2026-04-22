from __future__ import annotations

from typing import Any, Dict, List, Mapping, Optional, Sequence, Set, Tuple

from v17_rebirth.backend.logic.L1_atomic_ops.relation_geometry_pairs import (
    eval_liu_chong_hits,
    eval_liu_hai_hits,
    eval_liu_po_hits,
    sanxing_detect_geometry,
)


def _get_l0_consts() -> Dict[str, Any]:
    from v17_rebirth.backend.logic.configs.manager import get_v17_constants

    return get_v17_constants().get("L0_FOUNDATION", {})


def _get_l0_val(key: str, default: float) -> float:
    return float(_get_l0_consts().get(key, default))


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


def _pillar_keys() -> Tuple[str, ...]:
    return ("year", "month", "day", "hour")


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
