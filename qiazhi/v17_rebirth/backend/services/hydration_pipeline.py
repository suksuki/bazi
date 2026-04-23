from __future__ import annotations

from collections import Counter
from typing import Any

from v17_rebirth.backend.services.plugin_governance import classify_plugin_governance


HYDRATION_PIPELINE_PROTOCOL = "v17.hydration_pipeline.v1"


def build_plugin_governance_manifest(specs: list[Any]) -> dict[str, Any]:
    profiles: list[dict[str, Any]] = []
    for spec in specs or []:
        pid = str(getattr(spec, "plugin_id", "") or "").strip()
        if not pid:
            continue
        profiles.append(
            classify_plugin_governance(
                plugin_id=pid,
                layer=_layer_from_tier(int(getattr(spec, "causal_tier", 3) or 3)),
                causal_tier=int(getattr(spec, "causal_tier", 3) or 3),
                manifest={},
            )
        )
    class_counts = Counter(str(row.get("governance_class") or "") for row in profiles)
    authority_counts = Counter(str(row.get("authority_level") or "") for row in profiles)
    return {
        "protocol": HYDRATION_PIPELINE_PROTOCOL,
        "plugin_count": len(profiles),
        "governance_class_counts": dict(class_counts),
        "authority_level_counts": dict(authority_counts),
        "profiles": profiles,
    }


def bucket_decision_records(decisions: list[dict[str, Any]]) -> dict[str, Any]:
    rows = [dict(row) for row in decisions or [] if isinstance(row, dict)]
    manual = [d for d in rows if str(d.get("arbiter_type") or "user") == "user"]
    system = [d for d in rows if str(d.get("arbiter_type") or "") == "system"]
    llm = [d for d in rows if str(d.get("arbiter_type") or "") == "llm"]
    return {
        "protocol": HYDRATION_PIPELINE_PROTOCOL,
        "manual_decisions": manual,
        "auto_resolutions": system,
        "llm_arbitration_context": llm,
        "manual_inbox": list(manual),
        "auto_decisions": [*system, *llm],
        "decision_inbox_contract": "v17.decision.inbox.v2",
        "bucket_counts": {
            "manual": len(manual),
            "system": len(system),
            "llm": len(llm),
            "total": len(rows),
        },
    }


def _layer_from_tier(causal_tier: int) -> str:
    # This is a fallback for specs without module metadata; plugin_id rules remain primary.
    if causal_tier >= 5:
        return "L0"
    if causal_tier == 4:
        return "L1"
    if causal_tier == 3:
        return "L2"
    if causal_tier == 2:
        return "L3"
    return "L4"

