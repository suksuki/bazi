from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def apply_conflict_resolution(*, meta: Dict[str, Any], conflict_id: str, arbiter: str) -> Dict[str, Any]:
    cloned = dict(meta or {})
    conflicts = [dict(row) for row in (cloned.get("plugin_conflicts") or []) if isinstance(row, dict)]
    resolutions = [dict(row) for row in (cloned.get("plugin_conflict_resolutions") or []) if isinstance(row, dict)]

    normalized_conflict = str(conflict_id or "").strip()
    normalized_arbiter = str(arbiter or "").strip().lower() or "system"
    if not normalized_conflict:
        return cloned

    found_conflict = None
    for row in conflicts:
        if str(row.get("conflict_id") or "").strip() != normalized_conflict:
            continue
        row["resolution_status"] = (
            "approved" if normalized_arbiter == "system" else f"queued_{normalized_arbiter}"
        )
        row["resolved_by"] = normalized_arbiter
        row["resolved_at"] = _now_iso()
        found_conflict = row
        break

    matched_resolution = False
    for row in resolutions:
        if str(row.get("conflict_id") or "").strip() != normalized_conflict:
            continue
        row["status"] = "approved" if normalized_arbiter == "system" else f"queued_{normalized_arbiter}"
        row["resolved_by"] = normalized_arbiter
        row["applied_to_settlement"] = normalized_arbiter == "system"
        row["resolved_at"] = _now_iso()
        matched_resolution = True

    if not matched_resolution and found_conflict is not None:
        resolutions.append(
            {
                "resolution_id": f"manual:{normalized_conflict}",
                "conflict_id": normalized_conflict,
                "conflict_type": str(found_conflict.get("conflict_type") or "").strip(),
                "status": "approved" if normalized_arbiter == "system" else f"queued_{normalized_arbiter}",
                "resolved_by": normalized_arbiter,
                "applied_to_settlement": normalized_arbiter == "system",
                "reason": "由仲裁入口显式提交的冲突裁决。",
                "policy": "explicit_conflict_resolution",
                "resolved_at": _now_iso(),
            }
        )

    cloned["plugin_conflicts"] = conflicts
    cloned["plugin_conflict_resolutions"] = resolutions
    return cloned
