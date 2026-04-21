from __future__ import annotations

from collections import Counter
from typing import Any, Dict, List
from typing import Iterable


def _clamp(value: float, min_value: float, max_value: float) -> float:
    return max(min_value, min(max_value, value))


def _normalized(value: Any) -> str:
    return str(value or "").strip()


def _to_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _feedback_decay_weight(index: int, half_life: float = 24.0) -> float:
    # 最近事件权重更高：每经过 half_life 条反馈衰减一半。
    # index=0 -> 1.0, index=half_life -> 0.5, index=2*half_life -> 0.25
    return 2.0 ** (-index / max(half_life, 1.0))


def _feedback_quality(residual: float) -> float:
    # residual in [-1, 1] yields factor in [0.4, 1.6], preserving baseline preference while encoding quality.
    return 1.0 + 0.6 * _clamp(float(residual), -1.0, 1.0)


def build_knowledge_snapshot(
    *,
    claims: List[Dict[str, Any]],
    conflicts: List[Dict[str, Any]],
    conflict_resolutions: List[Dict[str, Any]],
    feedback_rows: Iterable[Dict[str, Any]] | None = None,
    current_authority: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    claim_types = Counter()
    conflict_types = Counter()
    arbiter_preferences = Counter()
    target_gods = Counter()
    feedback_arbiters = Counter()
    feedback_scores = Counter()

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

    for idx, item in enumerate(feedback_rows or []):
        residual = _to_float(item.get("residual_correction"))
        status = _normalized(item.get("status")).lower()
        if status in {"system", "llm", "user", "resolved_system", "resolved_user", "queued_llm", "queued_user"}:
            if status.startswith("resolved_"):
                status = status[len("resolved_") :]
            if status.startswith("queued_"):
                status = status[len("queued_") :]
            feedback_arbiters[status] += 1
            feed_weight = _feedback_decay_weight(idx, half_life=12.0)
            feedback_scores[status] += feed_weight * _feedback_quality(residual)

    top_targets = [
        {"target_god": target, "count": count}
        for target, count in target_gods.most_common(8)
    ]

    authority = current_authority if isinstance(current_authority, dict) else {}
    effect_scores = authority.get("effect_scores") if isinstance(authority.get("effect_scores"), dict) else {}
    current_targets: Dict[str, Dict[str, float]] = {}
    for god, raw in effect_scores.items():
        row = raw if isinstance(raw, dict) else {}
        name = _normalized(god)
        if not name:
            continue
        current_targets[name] = {
            "flux_tension_load": round(_to_float(row.get("flux_tension_load")), 4),
            "flux_reinforce_load": round(_to_float(row.get("flux_reinforce_load")), 4),
            "contest_pressure": round(_to_float(row.get("contest_pressure")), 4),
            "harm_score": round(_to_float(row.get("harm_score")), 4),
            "resolved_utility_flux": round(_to_float(row.get("resolved_utility_flux", row.get("resolved_utility"))), 4),
        }

    return {
        "claim_history": {
            "total_claims": len(claims),
            "by_type": dict(claim_types),
            "top_targets": top_targets,
            "current_targets": current_targets,
        },
        "conflict_history": {
            "total_conflicts": len(conflicts),
            "by_type": dict(conflict_types),
            "recommended_arbiters": dict(arbiter_preferences),
            "feedback_arbiters": dict(feedback_arbiters),
            "feedback_arbiter_scores": {key: round(value, 4) for key, value in feedback_scores.items()},
        },
        "resolution_preview": {
            "total_suggestions": len(conflict_resolutions),
            "resolved_by": dict(resolution_preview),
        },
    }
