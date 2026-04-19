from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping


_NATAL_PILLARS = {"year", "month", "day", "hour"}
_RUNTIME_PILLARS = {"luck", "flow"}


def detect_relation_origin_type(pillars: List[str] | None) -> str:
    scoped = {str(x).strip().lower() for x in (pillars or []) if str(x).strip()}
    has_natal = bool(scoped & _NATAL_PILLARS)
    has_luck = "luck" in scoped
    has_flow = "flow" in scoped
    if has_natal and has_luck and has_flow:
        return "mixed"
    if has_natal and has_luck:
        return "luck_background"
    if has_natal and has_flow:
        return "flow_trigger"
    if has_luck and has_flow:
        return "runtime_pair"
    if has_luck:
        return "luck_only"
    if has_flow:
        return "flow_only"
    if has_natal:
        return "natal"
    return "unknown"


def relation_origin_multiplier(origin_type: str) -> float:
    value = str(origin_type or "").strip().lower()
    if value == "luck_background":
        return 1.08
    if value == "mixed":
        return 1.03
    if value == "natal":
        return 1.0
    if value == "runtime_pair":
        return 0.94
    if value == "flow_trigger":
        return 0.9
    if value == "luck_only":
        return 0.88
    if value == "flow_only":
        return 0.78
    return 0.9


def choose_dominant_origin_type(origins: Iterable[str]) -> str:
    cleaned = [str(item or "").strip().lower() for item in origins if str(item or "").strip()]
    if not cleaned:
        return "unknown"
    return sorted(cleaned, key=lambda item: relation_origin_multiplier(item), reverse=True)[0]


def collect_origin_types_from_rows(
    rows: List[Dict[str, Any]],
    *,
    member_key: str,
    members: Iterable[str] | None = None,
) -> List[str]:
    member_filter = {str(item) for item in (members or []) if str(item).strip()}
    origins: List[str] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        row_members = {str(item) for item in (row.get(member_key) or []) if str(item).strip()}
        if member_filter and not (member_filter & row_members):
            continue
        origin = str(row.get("origin_type") or "").strip()
        if origin:
            origins.append(origin)
            continue
        pillars = row.get("pillars") if isinstance(row.get("pillars"), list) else []
        inferred = detect_relation_origin_type(pillars)
        if inferred != "unknown":
            origins.append(inferred)
    return origins


def summarize_relation_conditions(
    *,
    relation_family: str,
    pair_or_group: List[str],
    interaction_v2: Mapping[str, Any],
) -> Dict[str, Any]:
    liu_chong = interaction_v2.get("liu_chong") if isinstance(interaction_v2.get("liu_chong"), list) else []
    liu_hai = interaction_v2.get("liu_hai") if isinstance(interaction_v2.get("liu_hai"), list) else []
    liu_po = interaction_v2.get("liu_po") if isinstance(interaction_v2.get("liu_po"), list) else []
    sanxing = interaction_v2.get("sanxing") if isinstance(interaction_v2.get("sanxing"), list) else []

    relation_members = {str(x) for x in pair_or_group if str(x).strip()}

    origin_type = "unknown"
    for rows, key in ((interaction_v2.get(relation_family), "pair"),):
        _ = rows, key

    def _touches(rows: List[Dict[str, Any]], key: str) -> bool:
        for row in rows:
            if not isinstance(row, dict):
                continue
            members = {str(x) for x in (row.get(key) or []) if str(x).strip()}
            if relation_members & members:
                return True
        return False

    blockers: List[str] = []
    if relation_family in {"sanhe", "liuhe", "stem_fusion", "muku"} and _touches(liu_chong, "pair"):
        blockers.append("liu_chong")
    if relation_family in {"sanhe", "liuhe"} and _touches(liu_hai, "pair"):
        blockers.append("liu_hai")
    if relation_family in {"sanhe", "liuhe"} and _touches(liu_po, "pair"):
        blockers.append("liu_po")
    if relation_family in {"sanhe", "muku"} and _touches(sanxing, "branches"):
        blockers.append("sanxing")

    origin_candidates: List[str] = []
    relation_keys = {
        "liu_chong": ("liu_chong", "pair"),
        "liuhai": ("liu_hai", "pair"),
        "liu_po": ("liu_po", "pair"),
        "liuhe": ("liu_he", "pair"),
        "sanhe": ("san_he", "group"),
        "banhe": ("ban_he", "pair"),
        "muku": ("liu_chong", "pair"),
    }
    v2_key, member_key = relation_keys.get(relation_family, ("", "pair"))
    rows = interaction_v2.get(v2_key) if v2_key and isinstance(interaction_v2.get(v2_key), list) else []
    for row in rows:
        if not isinstance(row, dict):
            continue
        members = {str(x) for x in (row.get(member_key) or []) if str(x).strip()}
        if relation_members and not (relation_members & members):
            continue
        origin_candidates.append(detect_relation_origin_type(row.get("pillars") if isinstance(row.get("pillars"), list) else []))
    if origin_candidates:
        origin_type = choose_dominant_origin_type(origin_candidates)

    return {
        "relation_family": relation_family,
        "relation_members": sorted(relation_members),
        "blockers": blockers,
        "condition_state": "supported" if not blockers else "contested",
        "origin_type": origin_type,
        "origin_multiplier": relation_origin_multiplier(origin_type),
    }


def summarize_stem_fusion_conditions(case: Mapping[str, Any]) -> Dict[str, Any]:
    month_supports = bool(case.get("month_stem_supports"))
    branch_hua_ratio = float(case.get("branch_hua_ratio") or 0.0)
    mode = str(case.get("mode") or "").strip()
    if mode == "transformed":
        if month_supports:
            trigger = "month_support"
        else:
            trigger = "branch_support"
    else:
        trigger = "insufficient_support"
    return {
        "condition_state": "formed" if mode == "transformed" else "stuck",
        "condition_trigger": trigger,
        "month_supports": month_supports,
        "branch_hua_ratio": round(branch_hua_ratio, 4),
        "origin_type": detect_relation_origin_type(case.get("pillars") if isinstance(case.get("pillars"), list) else []),
        "origin_multiplier": relation_origin_multiplier(
            detect_relation_origin_type(case.get("pillars") if isinstance(case.get("pillars"), list) else [])
        ),
    }


def relation_effect_multiplier(condition_state: str) -> float:
    state = str(condition_state or "").strip().lower()
    if state in {"supported", "formed"}:
        return 1.0
    if state in {"contested", "stuck"}:
        return 0.65
    return 0.85
