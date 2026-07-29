from __future__ import annotations

from functools import lru_cache
from typing import Final

from abu_v60.knowledge.mechanism_contracts import (
    BaziMechanismEvidenceProfile,
    MechanismPatternDefinition,
    MechanismRoleDefinition,
)

MECHANISM_EVIDENCE_PROFILE_ID: Final = "v60.mechanism-evidence.owner-bounded.v1"
MECHANISM_EVIDENCE_PROFILE_VERSION: Final = "1.0.0"


def _role(role_id: str, *labels: str) -> MechanismRoleDefinition:
    return MechanismRoleDefinition(
        role_id=role_id,
        accepted_ten_god_labels=labels,
    )


@lru_cache(maxsize=1)
def bazi_mechanism_evidence_profile() -> BaziMechanismEvidenceProfile:
    """Return the selected candidate grammar without effective-work authority."""

    patterns = (
        MechanismPatternDefinition(
            pattern_id="bazi.mechanism.output-to-wealth",
            label="食伤生财结构候选",
            roles=(
                _role("SOURCE", "食神", "伤官"),
                _role("TARGET", "偏财", "正财"),
            ),
            structural_statement="食伤与财星成员同时出现在当前命盘结构中。",
            forbidden_shortcut="共同出现不等于食伤已经有效生财。",
        ),
        MechanismPatternDefinition(
            pattern_id="bazi.mechanism.output-to-pressure",
            label="食伤制官杀结构候选",
            roles=(
                _role("SOURCE", "食神", "伤官"),
                _role("TARGET", "七杀", "正官"),
            ),
            structural_statement="食伤与官杀成员同时出现在当前命盘结构中。",
            forbidden_shortcut="共同出现不等于制化关系已经有效。",
        ),
        MechanismPatternDefinition(
            pattern_id="bazi.mechanism.pressure-resource-self",
            label="官杀印身传递结构候选",
            roles=(
                _role("SOURCE", "七杀", "正官"),
                _role("BRIDGE", "偏印", "正印"),
                _role("TARGET", "日主", "比肩", "劫财"),
            ),
            structural_statement="官杀、印星与身的成员在当前结构中同时可见。",
            forbidden_shortcut="三类成员齐备不等于杀印相生或官印相生成立。",
        ),
        MechanismPatternDefinition(
            pattern_id="bazi.mechanism.wealth-to-pressure",
            label="财生官杀结构候选",
            roles=(
                _role("SOURCE", "偏财", "正财"),
                _role("TARGET", "七杀", "正官"),
            ),
            structural_statement="财星与官杀成员同时出现在当前命盘结构中。",
            forbidden_shortcut="共同出现不等于财已经有效生官杀。",
        ),
        MechanismPatternDefinition(
            pattern_id="bazi.mechanism.resource-to-self",
            label="印生身结构候选",
            roles=(
                _role("SOURCE", "偏印", "正印"),
                _role("TARGET", "日主", "比肩", "劫财"),
            ),
            structural_statement="印星与身的成员同时出现在当前命盘结构中。",
            forbidden_shortcut="共同出现不等于印星已经有效生身。",
        ),
    )
    return BaziMechanismEvidenceProfile(
        profile_id=MECHANISM_EVIDENCE_PROFILE_ID,
        profile_version=MECHANISM_EVIDENCE_PROFILE_VERSION,
        governance_status="OWNER_AUTHORIZED_RESEARCH_CANDIDATES",
        runtime_scope="MECHANISM_CANDIDATE_EVIDENCE_ONLY",
        professionally_reviewed=False,
        source_refs=(
            "v60.quant-foundation.owner-bounded.v1@1.0.0",
            (
                "v50-research-reference:docs/V50_MECHANISM_REPRESENTATION.md"
                "#sha256:440daf88c2eef7f4d34bcfb9aa651ef52f585be93fa40ea0518867f37693c718"
            ),
            (
                "v50-research-reference:packages/core/mechanism/contracts.py"
                "#sha256:6381d3197b6d98aebb26724f688f7094cb870afe61597df29ec834cac4cbdb94"
            ),
            "owner-direction:V60_MINGLI_MECHANISM_EVIDENCE_V1",
        ),
        patterns=patterns,
        candidate_presence_rule=("ALL_ROLES_PRESENT_AND_SOURCE_OR_BRIDGE_VISIBLE"),
        required_blockers=(
            "EFFECT_EVIDENCE_NOT_ADMITTED",
            "CAPACITY_MODEL_NOT_ADMITTED",
            "USABILITY_MODEL_NOT_ADMITTED",
            "TIMING_ACTIVATION_NOT_ADMITTED",
            "COUNTER_EVIDENCE_MODEL_NOT_ADMITTED",
            "PROFESSIONAL_REVIEW_REQUIRED",
        ),
        forbidden_conclusions=(
            "effective_work",
            "mechanism_effectiveness",
            "dominant_path",
            "capacity",
            "usability",
            "auspiciousness",
            "reality_event",
            "empirical_probability",
            "professional_verdict",
        ),
    )
