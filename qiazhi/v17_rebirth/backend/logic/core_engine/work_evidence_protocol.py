from __future__ import annotations

from typing import Any, Dict, Iterable, List


WORK_EVIDENCE_KEY = "work_evidence"


def _clean_list(values: Iterable[Any] | None = None) -> List[str]:
    out: List[str] = []
    for value in values or []:
        item = str(value or "").strip()
        if item:
            out.append(item)
    return out


def build_work_evidence(
    *,
    relation_family: str,
    target_god: str,
    members: Iterable[Any] | None = None,
    effect_type: str,
    layer: str = "unknown",
    origin_scope: str = "natal",
    condition_state: str = "",
    impact_ratio: float = 0.0,
    match_ratio: float = 0.0,
    path_strength: float = 0.0,
    targets: Iterable[Any] | None = None,
) -> Dict[str, Any]:
    clean_members = _clean_list(members)
    clean_targets = _clean_list(targets) or ([str(target_god).strip()] if str(target_god).strip() else [])
    return {
        "relation_family": str(relation_family or "").strip(),
        "target_god": str(target_god or "").strip(),
        "targets": clean_targets,
        "members": clean_members,
        "effect_type": str(effect_type or "").strip() or "observe",
        "layer": str(layer or "").strip() or "unknown",
        "origin_scope": str(origin_scope or "").strip() or "natal",
        "condition_state": str(condition_state or "").strip(),
        "impact_ratio": round(float(impact_ratio or 0.0), 4),
        "match_ratio": round(float(match_ratio or 0.0), 4),
        "path_strength": round(max(0.0, float(path_strength or 0.0)), 4),
    }
