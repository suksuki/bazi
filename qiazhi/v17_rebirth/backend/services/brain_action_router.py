from __future__ import annotations

from typing import Any, Dict, List


def _impact_from_action(action: Dict[str, Any]) -> Dict[str, Any]:
    winners = [str(x).strip() for x in (action.get("winner_claim_ids") or []) if str(x).strip()]
    return {
        "target_god": str(action.get("target_god") or "").strip(),
        "impact_ratio": 0.0,
        "intensity_level": 2,
        "winner_claim_ids": winners,
        "dropped_claim_ids": [str(x).strip() for x in (action.get("dropped_claim_ids") or []) if str(x).strip()],
    }


def _make_row(action: Dict[str, Any], *, arbiter_type: str) -> Dict[str, Any]:
    conflict_id = str(action.get("conflict_id") or "").strip()
    action_type = str(action.get("action_type") or "").strip()
    reason = str(action.get("reason") or "").strip()
    queue = str(action.get("queue") or arbiter_type).strip().lower()
    title = {
        "system_merge_suggestion": "冲突归并建议",
        "manual_escalation": "冲突升级待裁",
        "llm_context_hold": "冲突上下文保留",
    }.get(action_type, "脑动作")
    label = f"{title} · {conflict_id or 'unknown'}"
    return {
        "id": str(action.get("action_id") or f"brain:{conflict_id or action_type}"),
        "source": "brain_action_router",
        "source_label": "BrainAction",
        "plugin_id": "brain_action_router",
        "title": title,
        "label": label,
        "hint": label,
        "priority": float(action.get("confidence", 0.0) or 0.0) + (0.4 if queue == "user" else 0.2),
        "target_god": str(action.get("target_god") or "").strip(),
        "arbiter_type": arbiter_type,
        "brain_action_type": action_type,
        "conflict_id": conflict_id,
        "brain_reason": reason,
        "physical_impact": _impact_from_action(action),
        "arbitration_trace": f"BrainAction -> {action_type or 'unknown'} -> {arbiter_type.upper()}",
    }


def apply_brain_action_queue(
    *,
    arbitration: Dict[str, List[Dict[str, Any]]],
    meta: Dict[str, Any] | None,
) -> Dict[str, List[Dict[str, Any]]]:
    cloned = {
        "manual_decisions": [dict(row) for row in (arbitration.get("manual_decisions") or []) if isinstance(row, dict)],
        "auto_resolutions": [dict(row) for row in (arbitration.get("auto_resolutions") or []) if isinstance(row, dict)],
        "llm_arbitration_context": [dict(row) for row in (arbitration.get("llm_arbitration_context") or []) if isinstance(row, dict)],
        "pending_decisions": [dict(row) for row in (arbitration.get("pending_decisions") or []) if isinstance(row, dict)],
    }
    actions = [dict(row) for row in ((meta or {}).get("brain_action_queue") or []) if isinstance(row, dict)]
    if not actions:
        return cloned

    existing = {
        "manual": {str(row.get("conflict_id") or "").strip() for row in cloned["manual_decisions"] if str(row.get("conflict_id") or "").strip()},
        "system": {str(row.get("conflict_id") or "").strip() for row in cloned["auto_resolutions"] if str(row.get("conflict_id") or "").strip()},
        "llm": {str(row.get("conflict_id") or "").strip() for row in cloned["llm_arbitration_context"] if str(row.get("conflict_id") or "").strip()},
    }

    for action in actions:
        conflict_id = str(action.get("conflict_id") or "").strip()
        queue = str(action.get("queue") or "").strip().lower()
        if queue == "system":
            if conflict_id and conflict_id in existing["system"]:
                continue
            row = _make_row(action, arbiter_type="system")
            cloned["auto_resolutions"].append(row)
            existing["system"].add(conflict_id)
        elif queue == "user":
            if conflict_id and conflict_id in existing["manual"]:
                continue
            row = _make_row(action, arbiter_type="user")
            cloned["manual_decisions"].append(row)
            cloned["pending_decisions"].append(row)
            existing["manual"].add(conflict_id)
        else:
            if conflict_id and conflict_id in existing["llm"]:
                continue
            row = _make_row(action, arbiter_type="llm")
            cloned["llm_arbitration_context"].append(row)
            existing["llm"].add(conflict_id)

    return cloned
