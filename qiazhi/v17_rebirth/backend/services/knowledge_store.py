from __future__ import annotations

from collections import Counter
from typing import Any, Dict, List


def _normalized(value: Any) -> str:
    return str(value or "").strip()


def build_knowledge_snapshot(
    *,
    claims: List[Dict[str, Any]],
    conflicts: List[Dict[str, Any]],
    conflict_resolutions: List[Dict[str, Any]],
) -> Dict[str, Any]:
    claim_types = Counter()
    conflict_types = Counter()
    arbiter_preferences = Counter()
    target_gods = Counter()

    for claim in claims:
        claim_types[_normalized(claim.get("claim_type")) or "unknown"] += 1
        target = _normalized(claim.get("target_god"))
        if target:
            target_gods[target] += 1

    for conflict in conflicts:
        conflict_types[_normalized(conflict.get("conflict_type")) or "unknown"] += 1
        arbiter_preferences[_normalized(conflict.get("recommended_arbiter")) or "unknown"] += 1

    resolution_preview = Counter()
    for row in conflict_resolutions:
        resolution_preview[_normalized(row.get("resolved_by")) or "unknown"] += 1

    top_targets = [
        {"target_god": target, "count": count}
        for target, count in target_gods.most_common(8)
    ]

    return {
        "claim_history": {
            "total_claims": len(claims),
            "by_type": dict(claim_types),
            "top_targets": top_targets,
        },
        "conflict_history": {
            "total_conflicts": len(conflicts),
            "by_type": dict(conflict_types),
            "recommended_arbiters": dict(arbiter_preferences),
        },
        "resolution_preview": {
            "total_suggestions": len(conflict_resolutions),
            "resolved_by": dict(resolution_preview),
        },
    }
