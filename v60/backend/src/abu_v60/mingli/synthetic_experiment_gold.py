from __future__ import annotations

from typing import Final

from abu_v60.mingli.synthetic_experiment_catalog import (
    FIRST_SYNTHETIC_EXPERIMENT_REF,
)
from abu_v60.provenance import content_hash

# DEV Gold is physically absent from Agent packet construction and Provider prompts.
SYNTHETIC_EXPERIMENT_DEV_GOLD_VERSION: Final = (
    "v60.mingli-synthetic-experiment-dev-gold.001"
)
FIRST_SYNTHETIC_EXPERIMENT_DEV_GOLD: Final = {
    "gold_version": SYNTHETIC_EXPERIMENT_DEV_GOLD_VERSION,
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
