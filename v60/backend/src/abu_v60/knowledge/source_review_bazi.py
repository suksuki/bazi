from __future__ import annotations

from functools import lru_cache
from typing import Final

from abu_v60.knowledge.source_review_contracts import (
    BaziSourceCoordinateReviewProfile,
    SourceCoordinateReviewRule,
)

SOURCE_REVIEW_PROFILE_ID: Final = "v60.source-coordinate-review.owner-bounded.v1"
SOURCE_REVIEW_PROFILE_VERSION: Final = "1.0.0"


@lru_cache(maxsize=1)
def bazi_source_coordinate_review_profile() -> BaziSourceCoordinateReviewProfile:
    return BaziSourceCoordinateReviewProfile(
        profile_id=SOURCE_REVIEW_PROFILE_ID,
        profile_version=SOURCE_REVIEW_PROFILE_VERSION,
        governance_status="OWNER_AUTHORIZED_EVIDENCE_TRIAGE_ONLY",
        runtime_scope="SOURCE_COORDINATE_RELATION_REVIEW",
        professionally_reviewed=False,
        source_refs=(
            "v60.foundation.owner-bounded.v1@1.0.0",
            "v60.quant-foundation.owner-bounded.v1@1.0.0",
            (
                "v50-research-reference:data/knowledge/canon/"
                "bazi_source_manifestation_profile_b_v1.json"
                "#sha256:d89778a5cce8ee368ddcbbe9799eebace9e53e9b71741c3c1e3f94a04938c501"
            ),
            "owner-decision:V60_SOURCE_COORDINATE_RELATION_REVIEW_V1",
        ),
        rules=(
            SourceCoordinateReviewRule(
                rule_id="v60.source-review.six-clash-coordinate.v1",
                rule_version="1.0.0",
                admitted_fact_type="six_clash_membership",
                required_authority="SYSTEM_DETERMINISTIC_BOUNDED",
                required_boolean_claims=(
                    "membership_only",
                    "effect_not_inferred",
                ),
                review_state="SIX_CLASH_COORDINATE_REVIEW_REQUIRED",
                effect_conclusion_allowed=False,
                weight_allowed=False,
            ),
            SourceCoordinateReviewRule(
                rule_id="v60.source-review.six-harmony-coordinate.v1",
                rule_version="1.0.0",
                admitted_fact_type="six_harmony_membership",
                required_authority="SYSTEM_DETERMINISTIC_BOUNDED",
                required_boolean_claims=(
                    "membership_only",
                    "effect_not_inferred",
                ),
                review_state="SIX_HARMONY_COORDINATE_REVIEW_REQUIRED",
                effect_conclusion_allowed=False,
                weight_allowed=False,
            ),
        ),
        clear_state="NO_ADMITTED_RELATION_INTERSECTION",
        unresolved_dimensions=(
            "ROOT_USABILITY",
            "ROOT_STRENGTH",
            "RELATION_EFFECT",
            "SEASONAL_CAPACITY",
            "MECHANISM_EFFECT",
        ),
        forbidden_conclusions=(
            "root_verdict",
            "usable_root",
            "root_strength",
            "relation_damage",
            "relation_benefit",
            "relation_effect",
            "seasonal_authority",
            "capacity",
            "mechanism_effectiveness",
            "auspiciousness",
            "reality_event",
            "empirical_probability",
        ),
    )
