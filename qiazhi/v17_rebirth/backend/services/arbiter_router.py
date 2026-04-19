from __future__ import annotations

from typing import Any, Dict, List

_VALID_ARBITERS = {"system", "llm", "user"}


def _normalized(value: Any) -> str:
    return str(value or "").strip().lower()


def _default_arbiter_for_severity(severity: str) -> str:
    value = str(severity or "").strip().upper()
    if value == "P1":
        return "user"
    if value == "P2":
        return "llm"
    return "system"


def route_conflicts(
    *,
    conflicts: List[Dict[str, Any]],
    knowledge_snapshot: Dict[str, Any] | None = None,
) -> List[Dict[str, Any]]:
    snapshot = knowledge_snapshot if isinstance(knowledge_snapshot, dict) else {}
    conflict_history = snapshot.get("conflict_history") if isinstance(snapshot.get("conflict_history"), dict) else {}
    preferred = conflict_history.get("recommended_arbiters") if isinstance(conflict_history.get("recommended_arbiters"), dict) else {}
    feedback_preference = conflict_history.get("feedback_arbiters") if isinstance(conflict_history.get("feedback_arbiters"), dict) else {}
    feedback_scores = conflict_history.get("feedback_arbiter_scores") if isinstance(conflict_history.get("feedback_arbiter_scores"), dict) else {}

    def _weighted_score(name: str) -> float:
        return (
            float(preferred.get(name) or 0.0)
            + 0.45 * float(feedback_preference.get(name) or 0.0)
            + 0.65 * float(feedback_scores.get(name) or 0.0)
        )

    out: List[Dict[str, Any]] = []
    for row in conflicts:
        cloned = dict(row)
        severity = str(cloned.get("severity") or "").strip().upper()
        explicit = _normalized(cloned.get("recommended_arbiter"))
        explicit = explicit if explicit in _VALID_ARBITERS else ""
        resolved = explicit or _default_arbiter_for_severity(severity)
        try:
            score = float(cloned.get("conflict_score") or 0.0)
        except (TypeError, ValueError):
            score = 0.0

        conflict_type = str(cloned.get("conflict_type") or "").strip().lower()

        if conflict_type == "cross_layer_override" and score >= 0.74:
            resolved = "user"
        elif severity == "P1" and score >= 0.82:
            resolved = "user"
        elif severity == "P2" and score >= 0.80 and resolved != "user":
            resolved = "llm"
        elif severity == "P3" and score >= 0.88 and resolved == "system" and _weighted_score("llm") > 0:
            resolved = "llm"

        if severity == "P3" and _weighted_score("system") >= _weighted_score("llm"):
            resolved = "system"
        elif severity == "P2" and _weighted_score("llm") > _weighted_score("system"):
            resolved = "llm"
        elif severity == "P1":
            resolved = "user"

        cloned["recommended_arbiter"] = resolved
        cloned["routing_reason"] = (
            "基于冲突等级默认路由，并参考当前会话知识快照中的推荐裁决偏好与反馈打分。"
        )
        cloned["routing_policy"] = "severity_plus_session_preference"
        out.append(cloned)
    return out
