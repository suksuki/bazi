from __future__ import annotations

from functools import lru_cache
from typing import Final

from abu_v60.knowledge.quant_contracts import (
    BaziQuantFoundationProfile,
    ElementCycleDefinition,
    TenGodDefinition,
)

QUANT_FOUNDATION_PROFILE_ID: Final = "v60.quant-foundation.owner-bounded.v1"
QUANT_FOUNDATION_PROFILE_VERSION: Final = "1.0.0"

_ELEMENT_CYCLES = (
    ("wood", "fire", "earth"),
    ("fire", "earth", "metal"),
    ("earth", "metal", "water"),
    ("metal", "water", "wood"),
    ("water", "wood", "fire"),
)

_TEN_GOD_DEFINITIONS = (
    ("same_element", True, "比肩"),
    ("same_element", False, "劫财"),
    ("day_master_generates", True, "食神"),
    ("day_master_generates", False, "伤官"),
    ("day_master_controls", True, "偏财"),
    ("day_master_controls", False, "正财"),
    ("other_controls_day_master", True, "七杀"),
    ("other_controls_day_master", False, "正官"),
    ("other_generates_day_master", True, "偏印"),
    ("other_generates_day_master", False, "正印"),
)


@lru_cache(maxsize=1)
def bazi_quant_foundation_profile() -> BaziQuantFoundationProfile:
    return BaziQuantFoundationProfile(
        profile_id=QUANT_FOUNDATION_PROFILE_ID,
        profile_version=QUANT_FOUNDATION_PROFILE_VERSION,
        governance_status="OWNER_AUTHORIZED_MEASUREMENT_ONLY",
        runtime_scope="DETERMINISTIC_STRUCTURE_MEASUREMENTS",
        professionally_reviewed=False,
        source_refs=(
            "v60.foundation.owner-bounded.v1@1.0.0",
            (
                "v50-reference:packages/core/mingli_agent/fact_review.py"
                "#sha256:05eaaa5ca4fcbbf51a0f4f90777a232a8e3e53129f211572f473b4b745e9b097"
            ),
            (
                "v50-research-reference:data/knowledge/canon/"
                "bazi_source_manifestation_profile_b_v1.json"
                "#sha256:d89778a5cce8ee368ddcbbe9799eebace9e53e9b71741c3c1e3f94a04938c501"
            ),
            "owner-decision:V60_MINGLI_QUANT_FOUNDATION_V1",
        ),
        element_cycles=tuple(
            ElementCycleDefinition(
                element=element,
                generates=generates,
                controls=controls,
            )
            for element, generates, controls in _ELEMENT_CYCLES
        ),
        ten_god_definitions=tuple(
            TenGodDefinition(
                relationship=relationship,
                same_polarity=same_polarity,
                label=label,
            )
            for relationship, same_polarity, label in _TEN_GOD_DEFINITIONS
        ),
        source_evidence_states=(
            "HIDDEN_STEM_MEMBER",
            "SOURCE_COORDINATE_PRESENT",
            "STEM_LAYER_PRESENT",
            "EXACT_IDENTITY_CROSS_LAYER_PRESENT",
            "ELEMENTAL_AFFINITY_CROSS_LAYER_PRESENT",
            "SAME_PILLAR_SOURCE_COORDINATE",
            "MONTH_BRANCH_SOURCE_COORDINATE",
            "EFFECT_UNRESOLVED",
        ),
        source_match_kinds=(
            "EXACT_IDENTITY",
            "SAME_ELEMENT_DIFFERENT_IDENTITY",
        ),
        forbidden_conclusions=(
            "root_verdict",
            "root_strength",
            "usable_root",
            "causal_manifestation",
            "manifestation_quality",
            "seasonal_authority",
            "day_master_strength",
            "capacity",
            "usability",
            "mechanism_effectiveness",
            "relation_effect",
            "auspiciousness",
            "reality_event",
            "empirical_probability",
        ),
        calibration_status="NOT_CALIBRATED",
    )
