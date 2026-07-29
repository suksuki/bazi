from __future__ import annotations

from functools import lru_cache
from types import MappingProxyType
from typing import Final

from abu_v60.knowledge.contracts import (
    BaziCandidateQualificationProfile,
    BaziFoundationProfile,
    BranchDefinition,
    BranchRelationDefinition,
    CandidateQualificationRule,
    StemDefinition,
)

FOUNDATION_PROFILE_ID: Final = "v60.foundation.owner-bounded.v1"
FOUNDATION_PROFILE_VERSION: Final = "1.0.0"
FOUNDATION_OWNER_DECISION_HASH: Final = (
    "ca04b027fd56dbb93034a5dfc4e0e02ce4dd070076f907f2a1e09e6ce2a3485f"
)

_STEM_ROWS = (
    ("甲", "wood", "yang"),
    ("乙", "wood", "yin"),
    ("丙", "fire", "yang"),
    ("丁", "fire", "yin"),
    ("戊", "earth", "yang"),
    ("己", "earth", "yin"),
    ("庚", "metal", "yang"),
    ("辛", "metal", "yin"),
    ("壬", "water", "yang"),
    ("癸", "water", "yin"),
)
_BRANCH_ROWS = (
    ("子", ("癸",)),
    ("丑", ("己", "癸", "辛")),
    ("寅", ("甲", "丙", "戊")),
    ("卯", ("乙",)),
    ("辰", ("戊", "乙", "癸")),
    ("巳", ("丙", "戊", "庚")),
    ("午", ("丁", "己")),
    ("未", ("己", "丁", "乙")),
    ("申", ("庚", "壬", "戊")),
    ("酉", ("辛",)),
    ("戌", ("戊", "辛", "丁")),
    ("亥", ("壬", "甲")),
)
_RELATION_ROWS = (
    ("six_clash_membership", "子", "午"),
    ("six_clash_membership", "丑", "未"),
    ("six_clash_membership", "寅", "申"),
    ("six_clash_membership", "卯", "酉"),
    ("six_clash_membership", "辰", "戌"),
    ("six_clash_membership", "巳", "亥"),
    ("six_harmony_membership", "子", "丑"),
    ("six_harmony_membership", "寅", "亥"),
    ("six_harmony_membership", "卯", "戌"),
    ("six_harmony_membership", "辰", "酉"),
    ("six_harmony_membership", "巳", "申"),
    ("six_harmony_membership", "午", "未"),
)
FORBIDDEN_INFERENCES: Final = (
    "strength",
    "personality",
    "auspiciousness",
    "event",
    "usable_root",
    "root_strength",
    "mechanism_success",
    "relation_effect",
    "transformation",
)


@lru_cache(maxsize=1)
def bazi_foundation_profile() -> BaziFoundationProfile:
    return BaziFoundationProfile(
        profile_id=FOUNDATION_PROFILE_ID,
        profile_version=FOUNDATION_PROFILE_VERSION,
        governance_status="OWNER_CONDITIONALLY_ACCEPTED",
        runtime_scope="BOUNDED_DETERMINISTIC_FACTS",
        professionally_reviewed=False,
        source_refs=("owner-decision:TASK_18B_KB_P0_FOUNDATION_BOUNDARY_REPAIR",),
        owner_decision_hash=FOUNDATION_OWNER_DECISION_HASH,
        stems=tuple(
            StemDefinition(stem=stem, element=element, polarity=polarity)
            for stem, element, polarity in _STEM_ROWS
        ),
        branches=tuple(
            BranchDefinition(branch=branch, hidden_stems=hidden_stems)
            for branch, hidden_stems in _BRANCH_ROWS
        ),
        relations=tuple(
            BranchRelationDefinition(
                relation_type=relation_type,
                left_branch=left,
                right_branch=right,
            )
            for relation_type, left, right in _RELATION_ROWS
        ),
        forbidden_inferences=FORBIDDEN_INFERENCES,
    )


_PROFILE = bazi_foundation_profile()
STEM_ELEMENTS: Final = MappingProxyType({item.stem: item.element for item in _PROFILE.stems})
STEM_POLARITY: Final = MappingProxyType({item.stem: item.polarity for item in _PROFILE.stems})
HIDDEN_STEMS: Final = MappingProxyType(
    {item.branch: item.hidden_stems for item in _PROFILE.branches}
)
SIX_CLASH: Final = frozenset(
    frozenset((item.left_branch, item.right_branch))
    for item in _PROFILE.relations
    if item.relation_type == "six_clash_membership"
)
SIX_HARMONY: Final = frozenset(
    frozenset((item.left_branch, item.right_branch))
    for item in _PROFILE.relations
    if item.relation_type == "six_harmony_membership"
)
SOURCE_REF: Final = _PROFILE.source_ref

CANDIDATE_QUALIFICATION_PROFILE_ID: Final = "v60.candidate-qualification.owner-bounded.v1"
CANDIDATE_QUALIFICATION_PROFILE_VERSION: Final = "1.0.0"


@lru_cache(maxsize=1)
def bazi_candidate_qualification_profile() -> BaziCandidateQualificationProfile:
    return BaziCandidateQualificationProfile(
        profile_id=CANDIDATE_QUALIFICATION_PROFILE_ID,
        profile_version=CANDIDATE_QUALIFICATION_PROFILE_VERSION,
        governance_status="OWNER_CONDITIONALLY_ACCEPTED",
        runtime_scope="STRUCTURE_VISIBILITY_ONLY",
        professionally_reviewed=False,
        source_refs=(
            SOURCE_REF,
            "owner-boundary:structure-membership-is-not-relation-effect",
        ),
        rules=(
            CandidateQualificationRule(
                rule_id="v60.rule.structure-membership.visibility",
                rule_version="1.0.0",
                dimension="STRUCTURE_EVIDENCE",
                admitted_fact_types=(
                    "six_clash_membership",
                    "six_harmony_membership",
                ),
                required_authority="SYSTEM_DETERMINISTIC_BOUNDED",
                required_boolean_claims=(
                    "membership_only",
                    "effect_not_inferred",
                ),
                required_source_refs=(SOURCE_REF,),
                conclusion="STRUCTURE_EVIDENCE_SATISFIED",
                selection_authority=False,
                forbidden_conclusions=(
                    "relation_effect",
                    "usable_root",
                    "mechanism_capacity",
                    "time_activation",
                    "professional_admission",
                    "effective_work",
                ),
            ),
        ),
    )
