from __future__ import annotations

from typing import Protocol


class MechanismContext(Protocol):
    label: str
    evidence_id: str


def mechanism_method_card(item: MechanismContext) -> dict[str, object]:
    """Return a research checklist, never a professionally admitted conclusion."""

    if "制官杀" in item.label:
        checks = (
            "OUTPUT_SOURCE_AVAILABILITY",
            "OFFICIAL_KILLING_PRESSURE_ACTUALLY_PRESENT",
            "DAY_MASTER_CAPACITY",
            "VISIBLE_HIDDEN_REACHABILITY",
            "SOURCE_AND_TARGET_SAME_LAYER",
            "RESOURCE_OR_OTHER_BLOCKER_INTERFERENCE",
        )
    elif "生财" in item.label:
        checks = (
            "OUTPUT_SOURCE_AVAILABILITY",
            "WEALTH_TARGET_REACHABILITY",
            "DAY_MASTER_CAPACITY",
            "RESOURCE_SUPPRESSION",
            "PEER_COMPETITION",
        )
    else:
        checks = ("SOURCE", "TRANSFORMATION", "TARGET", "CAPACITY", "BLOCKERS")
    return {
        "label": item.label,
        "evidence_id": item.evidence_id,
        "required_checks": checks,
        "status": "COMPETING_HYPOTHESIS_ONLY",
    }
