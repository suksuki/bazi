from __future__ import annotations

from typing import Any, Dict, List, Tuple

from v17_rebirth.backend.logic.L0_physics_fields.ten_gods_engine import (
    BRANCH_ELEMENT,
    BRANCH_HIDDEN,
    STEM_ELEMENT,
    _parse_gz,
    ten_god_from_stems,
)


YANGREN_BRANCH_BY_DAYMASTER: Dict[str, str] = {
    "甲": "卯",
    "乙": "寅",
    "丙": "午",
    "丁": "巳",
    "戊": "午",
    "己": "巳",
    "庚": "酉",
    "辛": "申",
    "壬": "子",
    "癸": "亥",
}


def daymaster_stem(physics_tensor: Dict[str, Any]) -> str:
    four = physics_tensor.get("four_pillars") if isinstance(physics_tensor.get("four_pillars"), dict) else {}
    day_gz = str(four.get("day", "")).strip()
    return day_gz[0] if len(day_gz) >= 2 else ""


def month_branch(physics_tensor: Dict[str, Any]) -> str:
    four = physics_tensor.get("four_pillars") if isinstance(physics_tensor.get("four_pillars"), dict) else {}
    month_gz = str(four.get("month", "")).strip()
    return month_gz[1] if len(month_gz) >= 2 else ""


def branch_scopes_by_branch(physics_tensor: Dict[str, Any]) -> Dict[str, List[str]]:
    four = physics_tensor.get("four_pillars") if isinstance(physics_tensor.get("four_pillars"), dict) else {}
    out: Dict[str, List[str]] = {}
    for scope in ("year", "month", "day", "hour"):
        _stem, branch = _parse_gz(str(four.get(scope, "")).strip())
        if branch:
            out.setdefault(branch, []).append(scope)
    for scope, key in (("luck", "luck_pillar"), ("flow", "flow_pillar")):
        _stem, branch = _parse_gz(str(physics_tensor.get(key, "")).strip())
        if branch:
            out.setdefault(branch, []).append(scope)
    return out


def scope_label(scopes: List[str]) -> str:
    labels = {
        "year": "年支",
        "month": "月支",
        "day": "日支",
        "hour": "时支",
        "luck": "大运",
        "flow": "流年",
    }
    return "、".join(labels.get(scope, scope) for scope in scopes)


def yangren_blade_context(physics_tensor: Dict[str, Any]) -> Dict[str, Any]:
    daymaster = daymaster_stem(physics_tensor)
    blade_branch = YANGREN_BRANCH_BY_DAYMASTER.get(daymaster, "")
    scopes = branch_scopes_by_branch(physics_tensor).get(blade_branch, []) if blade_branch else []
    natal_scopes = [scope for scope in scopes if scope in {"year", "month", "day", "hour"}]
    runtime_scopes = [scope for scope in scopes if scope in {"luck", "flow"}]
    return {
        "daymaster": daymaster,
        "blade_branch": blade_branch,
        "blade_scopes": scopes,
        "natal_blade_scopes": natal_scopes,
        "runtime_blade_scopes": runtime_scopes,
        "blade_scope_label": scope_label(natal_scopes or runtime_scopes),
        "has_natal_blade": bool(natal_scopes),
        "month_is_blade": "month" in scopes,
    }


def pillar_scope_rows(physics_tensor: Dict[str, Any], *, include_runtime: bool = False) -> List[Tuple[str, str, str]]:
    four = physics_tensor.get("four_pillars") if isinstance(physics_tensor.get("four_pillars"), dict) else {}
    rows: List[Tuple[str, str, str]] = []
    for scope in ("year", "month", "day", "hour"):
        stem, branch = _parse_gz(str(four.get(scope, "")).strip())
        rows.append((scope, stem, branch))
    if include_runtime:
        for scope, key in (("luck", "luck_pillar"), ("flow", "flow_pillar")):
            stem, branch = _parse_gz(str(physics_tensor.get(key, "")).strip())
            rows.append((scope, stem, branch))
    return rows


def visible_god_hits(physics_tensor: Dict[str, Any], *, include_runtime: bool = False) -> List[Dict[str, str]]:
    daymaster = daymaster_stem(physics_tensor)
    if not daymaster:
        return []
    hits: List[Dict[str, str]] = []
    for scope, stem, _branch in pillar_scope_rows(physics_tensor, include_runtime=include_runtime):
        if not stem or scope == "day":
            continue
        hits.append({"scope": scope, "stem": stem, "god": ten_god_from_stems(daymaster, stem)})
    return hits


def month_hidden_god_hits(physics_tensor: Dict[str, Any]) -> List[Dict[str, Any]]:
    daymaster = daymaster_stem(physics_tensor)
    month = month_branch(physics_tensor)
    if not daymaster or not month:
        return []
    hits: List[Dict[str, Any]] = []
    for stem, weight in BRANCH_HIDDEN.get(month, []):
        hits.append(
            {
                "branch": month,
                "stem": stem,
                "god": ten_god_from_stems(daymaster, stem),
                "weight": float(weight),
            }
        )
    return hits


def zaqi_evidence(physics_tensor: Dict[str, Any], candidate_gods: set[str]) -> Dict[str, Any]:
    hidden_hits = [row for row in month_hidden_god_hits(physics_tensor) if row.get("god") in candidate_gods]
    visible_hits = [row for row in visible_god_hits(physics_tensor) if row.get("god") in candidate_gods]
    return {
        "hidden_hits": hidden_hits,
        "visible_hits": visible_hits,
        "has_hidden": bool(hidden_hits),
        "has_visible": bool(visible_hits),
        "hidden_gods": sorted({str(row.get("god") or "") for row in hidden_hits if row.get("god")}),
        "visible_gods": sorted({str(row.get("god") or "") for row in visible_hits if row.get("god")}),
    }


def gods_for_element(daymaster: str, element: str) -> set[str]:
    if not daymaster or not element:
        return set()
    return {
        ten_god_from_stems(daymaster, stem)
        for stem, stem_element in STEM_ELEMENT.items()
        if stem_element == element
    }


def dominant_element_from_ten_gods(scores: Dict[str, float], *, daymaster: str) -> Tuple[str, float, float]:
    element_scores = {"木": 0.0, "火": 0.0, "土": 0.0, "金": 0.0, "水": 0.0}
    if not daymaster:
        return "", 0.0, 0.0
    god_to_element: Dict[str, str] = {}
    for stem, element in STEM_ELEMENT.items():
        god_to_element[ten_god_from_stems(daymaster, stem)] = element
    for god, score in scores.items():
        element = god_to_element.get(str(god))
        if element:
            element_scores[element] += float(score)
    ranked = sorted(element_scores.items(), key=lambda kv: kv[1], reverse=True)
    top_el, top_score = ranked[0]
    second = float(ranked[1][1]) if len(ranked) > 1 else 0.0
    return top_el, float(top_score), second


def element_structure_evidence(physics_tensor: Dict[str, Any], element: str) -> Dict[str, Any]:
    month = month_branch(physics_tensor)
    month_hidden = BRANCH_HIDDEN.get(month, [])
    month_main_element = STEM_ELEMENT.get(month_hidden[0][0], "") if month_hidden else BRANCH_ELEMENT.get(month, "")
    stem_hits: List[Dict[str, str]] = []
    branch_hits: List[Dict[str, Any]] = []
    for scope, stem, branch in pillar_scope_rows(physics_tensor):
        if stem and STEM_ELEMENT.get(stem) == element:
            stem_hits.append({"scope": scope, "stem": stem})
        if not branch:
            continue
        hidden_weights = [
            float(weight)
            for hidden_stem, weight in BRANCH_HIDDEN.get(branch, [])
            if STEM_ELEMENT.get(hidden_stem) == element
        ]
        if BRANCH_ELEMENT.get(branch) == element or hidden_weights:
            branch_hits.append(
                {
                    "scope": scope,
                    "branch": branch,
                    "main_element": BRANCH_ELEMENT.get(branch, ""),
                    "hidden_weight": round(sum(hidden_weights), 3),
                }
            )
    strong_branch_hits = [
        row for row in branch_hits if row.get("main_element") == element or float(row.get("hidden_weight") or 0.0) >= 0.6
    ]
    return {
        "month_branch": month,
        "month_main_element": month_main_element,
        "month_supports_element": month_main_element == element,
        "stem_hits": stem_hits,
        "branch_hits": branch_hits,
        "strong_branch_hits": strong_branch_hits,
    }


def daymaster_root_profile(physics_tensor: Dict[str, Any]) -> Dict[str, Any]:
    daymaster = daymaster_stem(physics_tensor)
    dm_element = STEM_ELEMENT.get(daymaster, "")
    roots: List[Dict[str, Any]] = []
    same_visible: List[Dict[str, str]] = []
    if not daymaster or not dm_element:
        return {"daymaster": daymaster, "root_weight": 0.0, "roots": roots, "same_visible": same_visible}
    scope_weight = {"year": 0.45, "month": 1.1, "day": 0.85, "hour": 0.5, "luck": 0.32, "flow": 0.18}
    for scope, stem, branch in pillar_scope_rows(physics_tensor, include_runtime=True):
        if scope != "day" and stem and STEM_ELEMENT.get(stem) == dm_element:
            same_visible.append({"scope": scope, "stem": stem})
        for hidden_stem, weight in BRANCH_HIDDEN.get(branch, []):
            if STEM_ELEMENT.get(hidden_stem) != dm_element:
                continue
            roots.append(
                {
                    "scope": scope,
                    "branch": branch,
                    "stem": hidden_stem,
                    "weight": round(float(weight) * scope_weight.get(scope, 0.2), 3),
                }
            )
    root_weight = round(sum(float(row.get("weight") or 0.0) for row in roots), 3)
    return {
        "daymaster": daymaster,
        "daymaster_element": dm_element,
        "root_weight": root_weight,
        "roots": roots,
        "same_visible": same_visible,
    }


def _score_sum(scores: Dict[str, float], *names: str) -> float:
    return sum(float(scores.get(name, 0.0)) for name in names)


def is_followable_weak_body(physics_tensor: Dict[str, Any], scores: Dict[str, float], *, max_support: float) -> Tuple[bool, Dict[str, Any]]:
    profile = daymaster_root_profile(physics_tensor)
    peer = _score_sum(scores, "比肩", "劫财")
    seal = _score_sum(scores, "正印", "偏印")
    support_score = peer + seal + float(profile.get("root_weight") or 0.0) * 8.0 + len(profile.get("same_visible") or []) * 3.0
    evidence = {
        **profile,
        "peer_score": round(peer, 3),
        "seal_score": round(seal, 3),
        "self_support_score": round(support_score, 3),
        "self_support_limit": round(max_support, 3),
    }
    return support_score <= max_support, evidence


def is_self_party_strong(physics_tensor: Dict[str, Any], scores: Dict[str, float], *, min_support: float) -> Tuple[bool, Dict[str, Any]]:
    profile = daymaster_root_profile(physics_tensor)
    peer = _score_sum(scores, "比肩", "劫财")
    seal = _score_sum(scores, "正印", "偏印")
    support_score = peer + seal + float(profile.get("root_weight") or 0.0) * 6.0 + len(profile.get("same_visible") or []) * 2.0
    evidence = {
        **profile,
        "peer_score": round(peer, 3),
        "seal_score": round(seal, 3),
        "self_support_score": round(support_score, 3),
        "self_support_required": round(min_support, 3),
    }
    return support_score >= min_support and float(profile.get("root_weight") or 0.0) >= 0.8, evidence


def branch_main_god(daymaster: str, branch: str, fallback: str = "劫财") -> str:
    hidden = BRANCH_HIDDEN.get(branch) or []
    if not daymaster or not hidden:
        return fallback
    return ten_god_from_stems(daymaster, hidden[0][0]) or fallback
