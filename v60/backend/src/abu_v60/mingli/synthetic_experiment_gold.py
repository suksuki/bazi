from __future__ import annotations

from typing import Final

from abu_v60.mingli.synthetic_experiment_catalog import (
    CANDIDATE_PARTITION_FALSIFIER_GENERALIZATION_EXPERIMENT_REF,
    FIRST_SYNTHETIC_EXPERIMENT_REF,
    HIDDEN_RANK_CROSS_DAY_MASTER_GENERALIZATION_EXPERIMENT_REF,
    HIDDEN_RANK_PRIMARY_SECONDARY_EXPERIMENT_REF,
    HIDDEN_RANK_SECONDARY_TERTIARY_EXPERIMENT_REF,
    REGIME_WORK_PATH_GENERALIZATION_EXPERIMENT_REF,
    ROOT_IDENTITY_SYNTHETIC_EXPERIMENT_REF,
)
from abu_v60.provenance import content_hash

# DEV Gold is physically absent from Agent packet construction and Provider prompts.
FIRST_SYNTHETIC_EXPERIMENT_DEV_GOLD_VERSION: Final = "v60.mingli-synthetic-experiment-dev-gold.001"
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
FIRST_SYNTHETIC_EXPERIMENT_DEV_GOLD_HASH: Final = content_hash(FIRST_SYNTHETIC_EXPERIMENT_DEV_GOLD)

ROOT_IDENTITY_SYNTHETIC_EXPERIMENT_DEV_GOLD: Final = {
    "gold_version": "v60.mingli-synthetic-experiment-dev-gold.005",
    "experiment_ref": ROOT_IDENTITY_SYNTHETIC_EXPERIMENT_REF,
    "A_candidate_coordinate": "hour支藏乙",
    "A_candidate_identity": "SAME_ELEMENT_DIFFERENT_STEM",
    "A_minimum_anti_follow_gate": "NOT_DETERMINED",
    "A_allowed_effective_root_statuses": ("PRESENT", "UNRESOLVED"),
    "A_allowed_regime_classifications": (
        "NON_WEAK_OUTSIDE_SCOPE",
        "ORDINARY_WEAK",
        "UNRESOLVED",
    ),
    "B_candidate_coordinate": "hour支藏甲",
    "B_candidate_identity": "EXACT_DAY_MASTER",
    "B_minimum_anti_follow_gate": "PRESENT",
    "B_effective_root_status": "PRESENT",
    "B_effective_root_coordinates": ("hour支藏甲",),
    "B_allowed_regime_classifications": (
        "NON_WEAK_OUTSIDE_SCOPE",
        "ORDINARY_WEAK",
        "UNRESOLVED",
    ),
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

HIDDEN_RANK_PRIMARY_SECONDARY_DEV_GOLD: Final = {
    "gold_version": "v60.mingli-synthetic-experiment-dev-gold.005",
    "experiment_ref": HIDDEN_RANK_PRIMARY_SECONDARY_EXPERIMENT_REF,
    "A_candidate_coordinate": "hour支藏乙",
    "A_branch": "卯",
    "A_hidden_order": 1,
    "A_hidden_rank": "PRIMARY_QI",
    "A_minimum_anti_follow_gate": "PRESENT",
    "A_hour_fact": ("己卯", "偏财", ("乙",), ("比肩",)),
    "A_required_effective_root_status": "PRESENT",
    "A_allowed_regime_classifications": (
        "NON_WEAK_OUTSIDE_SCOPE",
        "ORDINARY_WEAK",
        "UNRESOLVED",
    ),
    "B_candidate_coordinate": "hour支藏乙",
    "B_branch": "辰",
    "B_hidden_order": 2,
    "B_hidden_rank": "SECONDARY_QI",
    "B_minimum_anti_follow_gate": "NOT_DETERMINED",
    "B_hour_fact": ("庚辰", "正官", ("戊", "乙", "癸"), ("正财", "比肩", "偏印")),
    "B_allowed_effective_root_statuses": ("PRESENT", "UNRESOLVED"),
    "B_allowed_regime_classifications": (
        "NON_WEAK_OUTSIDE_SCOPE",
        "ORDINARY_WEAK",
        "UNRESOLVED",
    ),
    "must_hold": (
        "FIRST_THREE_PILLARS",
        "DAY_MASTER",
        "MONTH_COMMAND",
        "VISIBLE_PEERS",
    ),
    "qualification_effect": "DEV_EVIDENCE_ONLY_NOT_METHOD_QUALIFICATION",
}
HIDDEN_RANK_PRIMARY_SECONDARY_DEV_GOLD_HASH: Final = content_hash(
    HIDDEN_RANK_PRIMARY_SECONDARY_DEV_GOLD
)

HIDDEN_RANK_SECONDARY_TERTIARY_DEV_GOLD: Final = {
    "gold_version": "v60.mingli-synthetic-experiment-dev-gold.005",
    "experiment_ref": HIDDEN_RANK_SECONDARY_TERTIARY_EXPERIMENT_REF,
    "A_candidate_coordinate": "hour支藏乙",
    "A_branch": "辰",
    "A_hidden_order": 2,
    "A_hidden_rank": "SECONDARY_QI",
    "A_minimum_anti_follow_gate": "NOT_DETERMINED",
    "A_hour_fact": ("庚辰", "正官", ("戊", "乙", "癸"), ("正财", "比肩", "偏印")),
    "A_allowed_effective_root_statuses": ("PRESENT", "UNRESOLVED"),
    "A_allowed_regime_classifications": (
        "NON_WEAK_OUTSIDE_SCOPE",
        "ORDINARY_WEAK",
        "UNRESOLVED",
    ),
    "B_candidate_coordinate": "hour支藏乙",
    "B_branch": "未",
    "B_hidden_order": 3,
    "B_hidden_rank": "TERTIARY_QI",
    "B_minimum_anti_follow_gate": "NOT_DETERMINED",
    "B_hour_fact": ("癸未", "偏印", ("己", "丁", "乙"), ("偏财", "食神", "比肩")),
    "B_allowed_effective_root_statuses": ("PRESENT", "UNRESOLVED"),
    "B_allowed_regime_classifications": (
        "NON_WEAK_OUTSIDE_SCOPE",
        "ORDINARY_WEAK",
        "UNRESOLVED",
    ),
    "must_hold": (
        "FIRST_THREE_PILLARS",
        "DAY_MASTER",
        "MONTH_COMMAND",
        "VISIBLE_PEERS",
    ),
    "qualification_effect": "DEV_EVIDENCE_ONLY_NOT_METHOD_QUALIFICATION",
}
HIDDEN_RANK_SECONDARY_TERTIARY_DEV_GOLD_HASH: Final = content_hash(
    HIDDEN_RANK_SECONDARY_TERTIARY_DEV_GOLD
)

HIDDEN_RANK_CROSS_DAY_MASTER_GENERALIZATION_DEV_GOLD: Final = {
    "gold_version": "v60.mingli-synthetic-experiment-dev-gold.005",
    "experiment_ref": HIDDEN_RANK_CROSS_DAY_MASTER_GENERALIZATION_EXPERIMENT_REF,
    "A_candidate_coordinate": "hour支藏丙",
    "A_branch": "巳",
    "A_hidden_order": 1,
    "A_hidden_rank": "PRIMARY_QI",
    "A_minimum_anti_follow_gate": "PRESENT",
    "A_hour_fact": ("癸巳", "正官", ("丙", "戊", "庚"), ("比肩", "食神", "偏财")),
    "A_required_effective_root_status": "PRESENT",
    "A_allowed_regime_classifications": (
        "NON_WEAK_OUTSIDE_SCOPE",
        "ORDINARY_WEAK",
        "UNRESOLVED",
    ),
    "B_candidate_coordinate": "hour支藏丙",
    "B_branch": "寅",
    "B_hidden_order": 2,
    "B_hidden_rank": "SECONDARY_QI",
    "B_minimum_anti_follow_gate": "NOT_DETERMINED",
    "B_hour_fact": ("庚寅", "偏财", ("甲", "丙", "戊"), ("偏印", "比肩", "食神")),
    "B_allowed_effective_root_statuses": ("PRESENT", "UNRESOLVED"),
    "B_allowed_regime_classifications": (
        "NON_WEAK_OUTSIDE_SCOPE",
        "ORDINARY_WEAK",
        "UNRESOLVED",
    ),
    "must_hold": (
        "FIRST_THREE_PILLARS",
        "DAY_MASTER",
        "MONTH_COMMAND",
        "VISIBLE_PEERS",
    ),
    "qualification_effect": "DEV_EVIDENCE_ONLY_NOT_METHOD_QUALIFICATION",
}
HIDDEN_RANK_CROSS_DAY_MASTER_GENERALIZATION_DEV_GOLD_HASH: Final = content_hash(
    HIDDEN_RANK_CROSS_DAY_MASTER_GENERALIZATION_DEV_GOLD
)

REGIME_WORK_PATH_GENERALIZATION_DEV_GOLD: Final = {
    "gold_version": "v60.mingli-synthetic-experiment-dev-gold.005",
    "experiment_ref": REGIME_WORK_PATH_GENERALIZATION_EXPERIMENT_REF,
    "A_hour_fact": ("辛酉", "伤官", ("辛",), ("伤官",)),
    "A_required_effective_root_status": "ABSENT",
    "A_allowed_regime_classifications": ("FOLLOW_TREND", "UNRESOLVED"),
    "A_expected_pattern_refs": (
        "bazi.mechanism.output-to-wealth@1",
        "bazi.mechanism.output-to-pressure@1",
        "bazi.mechanism.wealth-to-pressure@1",
    ),
    "B_hour_fact": (
        "壬戌",
        "偏财",
        ("戊", "辛", "丁"),
        ("比肩", "伤官", "正印"),
    ),
    "B_candidate_coordinate": "hour支藏戊",
    "B_candidate_identity": "EXACT_DAY_MASTER",
    "B_hidden_rank": "PRIMARY_QI",
    "B_minimum_anti_follow_gate": "PRESENT",
    "B_required_effective_root_status": "PRESENT",
    "B_allowed_regime_classifications": (
        "ORDINARY_WEAK",
        "UNRESOLVED",
    ),
    "B_expected_pattern_refs": (
        "bazi.mechanism.wealth-to-pressure@1",
        "bazi.mechanism.pressure-resource-self@1",
    ),
    "must_hold": (
        "FIRST_THREE_PILLARS",
        "DAY_MASTER",
        "MONTH_COMMAND",
        "VISIBLE_PEERS",
    ),
    "qualification_effect": "DEV_EVIDENCE_ONLY_NOT_METHOD_QUALIFICATION",
}
REGIME_WORK_PATH_GENERALIZATION_DEV_GOLD_HASH: Final = content_hash(
    REGIME_WORK_PATH_GENERALIZATION_DEV_GOLD
)

CANDIDATE_PARTITION_FALSIFIER_GENERALIZATION_DEV_GOLD: Final = {
    "gold_version": "v60.mingli-synthetic-experiment-dev-gold.005",
    "experiment_ref": CANDIDATE_PARTITION_FALSIFIER_GENERALIZATION_EXPERIMENT_REF,
    "A_hour_fact": (
        "壬午",
        "食神",
        ("丁", "己"),
        ("正官", "正印"),
    ),
    "A_required_effective_root_status": "ABSENT",
    "A_required_effective_root_coordinates": (),
    "A_required_rooted_visible_support_status": "ABSENT",
    "A_expected_visible_peer_coordinates": (),
    "A_expected_resource_coordinates": (
        "month支藏己(正印)",
        "day支藏戊(偏印)",
        "hour支藏己(正印)",
    ),
    "A_required_competition_kinds": ("HIDDEN_RESOURCE",),
    "A_allowed_regime_classifications": (
        "FALSE_FOLLOW_COMPETITION",
        "UNRESOLVED",
    ),
    "A_expected_pattern_refs": (
        "bazi.mechanism.output-to-wealth@1",
        "bazi.mechanism.output-to-pressure@1",
        "bazi.mechanism.wealth-to-pressure@1",
    ),
    "B_hour_fact": (
        "甲申",
        "偏财",
        ("庚", "壬", "戊"),
        ("比肩", "食神", "偏印"),
    ),
    "B_candidate_coordinate": "hour支藏庚",
    "B_candidate_branch": "申",
    "B_candidate_identity": "EXACT_DAY_MASTER",
    "B_hidden_order": 1,
    "B_hidden_rank": "PRIMARY_QI",
    "B_minimum_anti_follow_gate": "PRESENT",
    "B_required_effective_root_status": "PRESENT",
    "B_required_effective_root_coordinates": ("hour支藏庚",),
    "B_required_rooted_visible_support_status": "ABSENT",
    "B_expected_visible_peer_coordinates": (),
    "B_expected_resource_coordinates": (
        "month支藏己(正印)",
        "day支藏戊(偏印)",
        "hour支藏戊(偏印)",
    ),
    "B_required_competition_kinds": ("HIDDEN_RESOURCE",),
    "B_allowed_regime_classifications": (
        "ORDINARY_WEAK",
        "UNRESOLVED",
        "NON_WEAK_OUTSIDE_SCOPE",
    ),
    "B_expected_pattern_refs": (
        "bazi.mechanism.output-to-wealth@1",
        "bazi.mechanism.output-to-pressure@1",
        "bazi.mechanism.wealth-to-pressure@1",
    ),
    "candidate_partition": {
        "candidate_count": 3,
        "selected_count": 2,
        "excluded_count": 1,
        "winner_not_preselected": True,
    },
    "must_hold": (
        "FIRST_THREE_PILLARS",
        "DAY_MASTER",
        "MONTH_COMMAND",
        "VISIBLE_PEERS",
        "MECHANISM_PATTERN_SET",
    ),
    "qualification_effect": "DEV_EVIDENCE_ONLY_NOT_METHOD_QUALIFICATION",
}
CANDIDATE_PARTITION_FALSIFIER_GENERALIZATION_DEV_GOLD_HASH: Final = content_hash(
    CANDIDATE_PARTITION_FALSIFIER_GENERALIZATION_DEV_GOLD
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
    HIDDEN_RANK_PRIMARY_SECONDARY_EXPERIMENT_REF: (
        HIDDEN_RANK_PRIMARY_SECONDARY_DEV_GOLD,
        HIDDEN_RANK_PRIMARY_SECONDARY_DEV_GOLD_HASH,
    ),
    HIDDEN_RANK_SECONDARY_TERTIARY_EXPERIMENT_REF: (
        HIDDEN_RANK_SECONDARY_TERTIARY_DEV_GOLD,
        HIDDEN_RANK_SECONDARY_TERTIARY_DEV_GOLD_HASH,
    ),
    HIDDEN_RANK_CROSS_DAY_MASTER_GENERALIZATION_EXPERIMENT_REF: (
        HIDDEN_RANK_CROSS_DAY_MASTER_GENERALIZATION_DEV_GOLD,
        HIDDEN_RANK_CROSS_DAY_MASTER_GENERALIZATION_DEV_GOLD_HASH,
    ),
    REGIME_WORK_PATH_GENERALIZATION_EXPERIMENT_REF: (
        REGIME_WORK_PATH_GENERALIZATION_DEV_GOLD,
        REGIME_WORK_PATH_GENERALIZATION_DEV_GOLD_HASH,
    ),
    CANDIDATE_PARTITION_FALSIFIER_GENERALIZATION_EXPERIMENT_REF: (
        CANDIDATE_PARTITION_FALSIFIER_GENERALIZATION_DEV_GOLD,
        CANDIDATE_PARTITION_FALSIFIER_GENERALIZATION_DEV_GOLD_HASH,
    ),
}


def synthetic_experiment_dev_gold(
    experiment_ref: str,
) -> tuple[dict[str, object], str]:
    try:
        return SYNTHETIC_EXPERIMENT_DEV_GOLD_BY_REF[experiment_ref]
    except KeyError as exc:
        raise ValueError("mingli_synthetic_experiment_gold_not_found") from exc
