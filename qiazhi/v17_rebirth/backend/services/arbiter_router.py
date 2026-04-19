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

    out: List[Dict[str, Any]] = []
    for row in conflicts:
        cloned = dict(row)
        severity = str(cloned.get("severity") or "").strip().upper()
        explicit = _normalized(cloned.get("recommended_arbiter"))
        explicit = explicit if explicit in _VALID_ARBITERS else ""
        resolved = explicit or _default_arbiter_for_severity(severity)

        if severity == "P3" and int(preferred.get("system", 0) or 0) >= int(preferred.get("llm", 0) or 0):
            resolved = "system"
        elif severity == "P2" and int(preferred.get("llm", 0) or 0) > 0:
            resolved = "llm"
        elif severity == "P1":
            resolved = "user"

        cloned["recommended_arbiter"] = resolved
        cloned["routing_reason"] = (
            "基于冲突等级默认路由，并参考当前会话知识快照中的推荐裁决偏好。"
        )
        cloned["routing_policy"] = "severity_plus_session_preference"
        out.append(cloned)
    return out
