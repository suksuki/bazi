from __future__ import annotations

from functools import lru_cache
from typing import Final

from abu_v60.knowledge.timing_contracts import (
    BaziTimingEvidenceProfile,
    YunGenderCode,
)

TIMING_EVIDENCE_PROFILE_ID: Final = "v60.timing-evidence.owner-bounded.v1"
TIMING_EVIDENCE_PROFILE_VERSION: Final = "1.0.0"
TIMING_CALENDAR_ENGINE_VERSION: Final = (
    "v60.birth-calendar.lunar-python-1.4.8.five-rats.v1"
)


@lru_cache(maxsize=1)
def bazi_timing_evidence_profile() -> BaziTimingEvidenceProfile:
    return BaziTimingEvidenceProfile(
        profile_id=TIMING_EVIDENCE_PROFILE_ID,
        profile_version=TIMING_EVIDENCE_PROFILE_VERSION,
        governance_status="OWNER_AUTHORIZED_COORDINATES_ONLY",
        runtime_scope="DETERMINISTIC_TIMING_COORDINATES",
        professionally_reviewed=False,
        source_refs=(
            f"v60-calendar:{TIMING_CALENDAR_ENGINE_VERSION}",
            "dependency:lunar_python==1.4.8:EightChar.getYun",
            (
                "v50-reference:packages/core/engines/bazi/dayun.py"
                "#sha256:7bd44db37f94894d91ab3964e44ddebc0a2d2bad7e3691d6a41c79b9fb6181d3"
            ),
            (
                "v50-reference:packages/core/engines/bazi/temporal_service.py"
                "#sha256:2dcd5c45e4348bcf7b065e5912d059ed1ff29cbfe8462a3601158775c85fddb1"
            ),
            "owner-direction:V60_REAL_MINGLI_TIMING_V1",
        ),
        calendar_engine_version=TIMING_CALENDAR_ENGINE_VERSION,
        yun_gender_codes=(
            YunGenderCode(gender="female", lunar_python_code=0),
            YunGenderCode(gender="male", lunar_python_code=1),
        ),
        timing_layers=("DAYUN", "ANNUAL", "MONTHLY"),
        admitted_relation_types=(
            "same_branch_membership",
            "six_clash_membership",
            "six_harmony_membership",
        ),
        forbidden_conclusions=(
            "automatic_activation",
            "effective_relation",
            "mechanism_capacity",
            "mechanism_usability",
            "professional_path_selection",
            "auspiciousness",
            "reality_event",
            "empirical_probability",
            "canonical_life_case_write",
        ),
    )
