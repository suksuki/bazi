from __future__ import annotations

from typing import Final

from abu_v60.mingli.synthetic_experiment_catalog import (
    FIRST_SYNTHETIC_EXPERIMENT_REF,
    ROOT_IDENTITY_SYNTHETIC_EXPERIMENT_REF,
)
from abu_v60.provenance import content_hash

# DEV Gold is physically absent from Agent packet construction and Provider prompts.
FIRST_SYNTHETIC_EXPERIMENT_DEV_GOLD_VERSION: Final = (
    "v60.mingli-synthetic-experiment-dev-gold.001"
)
FIRST_SYNTHETIC_EXPERIMENT_DEV_GOLD: Final = {
    "gold_version": FIRST_SYNTHETIC_EXPERIMENT_DEV_GOLD_VERSION,
    "experiment_ref": FIRST_SYNTHETIC_EXPERIMENT_REF,
    "B_effective_root_status": "PRESENT",
    "B_effective_root_coordinates": ("hour支藏甲",),
    "B_regime_classification": "ORDINARY_WEAK",
    "B_required_day_master_state": "WEAK",
    "A_allowed_regime_classifications": ("FOLLOW_TREND", "UNRESOLVED"),
    "must_hold": (
        "FIRST_THREE_PILLARS",
        "DAY_MASTER",
        "MONTH_COMMAND",
        "VISIBLE_PEERS",
        "RESOURCE_SUPPORT",
        "MECHANISM_PATTERN_SET",
        "TIMING_COORDINATES",
    ),
    "qualification_effect": "DEV_EVIDENCE_ONLY_NOT_METHOD_QUALIFICATION",
}
FIRST_SYNTHETIC_EXPERIMENT_DEV_GOLD_HASH: Final = content_hash(
    FIRST_SYNTHETIC_EXPERIMENT_DEV_GOLD
)

ROOT_IDENTITY_SYNTHETIC_EXPERIMENT_DEV_GOLD: Final = {
    "gold_version": "v60.mingli-synthetic-experiment-dev-gold.003",
    "experiment_ref": ROOT_IDENTITY_SYNTHETIC_EXPERIMENT_REF,
    "A_candidate_coordinate": "hour支藏乙",
    "A_candidate_identity": "SAME_ELEMENT_DIFFERENT_STEM",
    "A_minimum_anti_follow_gate": "NOT_DETERMINED",
    "A_allowed_effective_root_statuses": ("PRESENT", "UNRESOLVED"),
    "A_allowed_regime_classifications": ("ORDINARY_WEAK", "UNRESOLVED"),
    "B_candidate_coordinate": "hour支藏甲",
    "B_candidate_identity": "EXACT_DAY_MASTER",
    "B_minimum_anti_follow_gate": "PRESENT",
    "B_effective_root_status": "PRESENT",
    "B_effective_root_coordinates": ("hour支藏甲",),
    "B_allowed_regime_classifications": ("ORDINARY_WEAK", "UNRESOLVED"),
    "must_hold": (
        "FIRST_THREE_PILLARS",
        "DAY_MASTER",
        "MONTH_COMMAND",
        "VISIBLE_PEERS",
        "RESOURCE_SUPPORT",
    ),
    "qualification_effect": "DEV_EVIDENCE_ONLY_NOT_METHOD_QUALIFICATION",
}
ROOT_IDENTITY_SYNTHETIC_EXPERIMENT_DEV_GOLD_HASH: Final = content_hash(
    ROOT_IDENTITY_SYNTHETIC_EXPERIMENT_DEV_GOLD
)

SYNTHETIC_EXPERIMENT_DEV_GOLD_BY_REF: Final = {
    FIRST_SYNTHETIC_EXPERIMENT_REF: (
        FIRST_SYNTHETIC_EXPERIMENT_DEV_GOLD,
        FIRST_SYNTHETIC_EXPERIMENT_DEV_GOLD_HASH,
    ),
    ROOT_IDENTITY_SYNTHETIC_EXPERIMENT_REF: (
        ROOT_IDENTITY_SYNTHETIC_EXPERIMENT_DEV_GOLD,
        ROOT_IDENTITY_SYNTHETIC_EXPERIMENT_DEV_GOLD_HASH,
    ),
}


def synthetic_experiment_dev_gold(
    experiment_ref: str,
) -> tuple[dict[str, object], str]:
    try:
        return SYNTHETIC_EXPERIMENT_DEV_GOLD_BY_REF[experiment_ref]
    except KeyError as exc:
        raise ValueError("mingli_synthetic_experiment_gold_not_found") from exc
