from __future__ import annotations

from typing import Any, Dict, List, Mapping


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

    return {
        "relation_family": relation_family,
        "relation_members": sorted(relation_members),
        "blockers": blockers,
        "condition_state": "supported" if not blockers else "contested",
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
    }


def relation_effect_multiplier(condition_state: str) -> float:
    state = str(condition_state or "").strip().lower()
    if state in {"supported", "formed"}:
        return 1.0
    if state in {"contested", "stuck"}:
        return 0.65
    return 0.85
