from __future__ import annotations

from datetime import date, time

import pytest
from abu_v60.knowledge import (
    CANDIDATE_QUALIFICATION_PROFILE_ID,
    CANDIDATE_QUALIFICATION_PROFILE_VERSION,
    FOUNDATION_PROFILE_ID,
    FOUNDATION_PROFILE_VERSION,
    QUANT_FOUNDATION_PROFILE_ID,
    QUANT_FOUNDATION_PROFILE_VERSION,
    SOURCE_REF,
    STEM_ELEMENTS,
    BaziCandidateQualificationProfile,
    BaziFoundationProfile,
    KnowledgeAuthority,
    KnowledgeAuthorityError,
    KnowledgeProfileSelection,
    bazi_candidate_qualification_profile,
    bazi_foundation_profile,
    bazi_quant_foundation_profile,
)
from abu_v60.mingli.calendar import BirthInput
from abu_v60.mingli.compiler import compile_birth_case
from abu_v60.system_manifest import runtime_manifest
from pydantic import ValidationError

EXPECTED_FOUNDATION_PROFILE_HASH = (
    "d02eb38e8a65882951dc2668b2d5aeb404902489d2d5441c915437b3a81452bb"
)
EXPECTED_CANDIDATE_RULE_PROFILE_HASH = (
    "cedcf77d6684448b9dcacda446cc7623bdd905781a3b3a9773bfc6d7dcf7c4d7"
)
EXPECTED_QUANT_FOUNDATION_PROFILE_HASH = (
    "9a5d4146a88458d8da32512f702c1e2b88ef7502b9df8020bd79d883855bb07c"
)


def test_foundation_profile_is_complete_and_hash_locked() -> None:
    profile = bazi_foundation_profile()

    assert len(profile.stems) == 10
    assert len(profile.branches) == 12
    assert len(profile.relations) == 12
    assert profile.profile_hash == EXPECTED_FOUNDATION_PROFILE_HASH
    assert profile.source_ref == SOURCE_REF
    assert profile.professionally_reviewed is False


def test_foundation_runtime_maps_are_immutable() -> None:
    with pytest.raises(TypeError):
        STEM_ELEMENTS["甲"] = "fire"  # type: ignore[index]


def test_candidate_rule_profile_is_hash_locked_and_cannot_select() -> None:
    profile = bazi_candidate_qualification_profile()

    assert profile.profile_hash == EXPECTED_CANDIDATE_RULE_PROFILE_HASH
    assert profile.runtime_scope == "STRUCTURE_VISIBILITY_ONLY"
    assert profile.professionally_reviewed is False
    assert len(profile.rules) == 1
    rule = profile.rules[0]
    assert rule.dimension == "STRUCTURE_EVIDENCE"
    assert rule.selection_authority is False
    assert "effective_work" in rule.forbidden_conclusions


def test_quant_foundation_profile_is_complete_bounded_and_hash_locked() -> None:
    profile = bazi_quant_foundation_profile()

    assert profile.profile_hash == EXPECTED_QUANT_FOUNDATION_PROFILE_HASH
    assert profile.runtime_scope == "DETERMINISTIC_STRUCTURE_MEASUREMENTS"
    assert profile.calibration_status == "NOT_CALIBRATED"
    assert profile.professionally_reviewed is False
    assert len(profile.element_cycles) == 5
    assert len(profile.ten_god_definitions) == 10
    assert "day_master_strength" in profile.forbidden_conclusions
    assert "empirical_probability" in profile.forbidden_conclusions


def test_knowledge_authority_requires_exact_identity_and_hash() -> None:
    authority = KnowledgeAuthority()
    resolved = authority.resolve(
        profile_id=FOUNDATION_PROFILE_ID,
        profile_version=FOUNDATION_PROFILE_VERSION,
        expected_hash=EXPECTED_FOUNDATION_PROFILE_HASH,
    )
    assert resolved is bazi_foundation_profile()

    with pytest.raises(KnowledgeAuthorityError, match="not_admitted"):
        authority.resolve(
            profile_id="profile:unknown",
            profile_version="1",
        )
    with pytest.raises(KnowledgeAuthorityError, match="hash_mismatch"):
        authority.resolve(
            profile_id=FOUNDATION_PROFILE_ID,
            profile_version=FOUNDATION_PROFILE_VERSION,
            expected_hash="0" * 64,
        )

    rule_profile = authority.resolve_candidate_rule_profile(
        profile_id=CANDIDATE_QUALIFICATION_PROFILE_ID,
        profile_version=CANDIDATE_QUALIFICATION_PROFILE_VERSION,
        expected_hash=EXPECTED_CANDIDATE_RULE_PROFILE_HASH,
    )
    assert rule_profile is bazi_candidate_qualification_profile()

    with pytest.raises(KnowledgeAuthorityError, match="candidate_rule_profile_not_admitted"):
        authority.resolve_candidate_rule_profile(
            profile_id="rule-profile:unknown",
            profile_version="1",
        )
    with pytest.raises(KnowledgeAuthorityError, match="candidate_rule_profile_hash_mismatch"):
        authority.resolve_candidate_rule_profile(
            profile_id=CANDIDATE_QUALIFICATION_PROFILE_ID,
            profile_version=CANDIDATE_QUALIFICATION_PROFILE_VERSION,
            expected_hash="0" * 64,
        )

    quant_profile = authority.resolve_quant_foundation_profile(
        profile_id=QUANT_FOUNDATION_PROFILE_ID,
        profile_version=QUANT_FOUNDATION_PROFILE_VERSION,
        expected_hash=EXPECTED_QUANT_FOUNDATION_PROFILE_HASH,
    )
    assert quant_profile is bazi_quant_foundation_profile()

    with pytest.raises(KnowledgeAuthorityError, match="quant_foundation_profile_not_admitted"):
        authority.resolve_quant_foundation_profile(
            profile_id="quant-profile:unknown",
            profile_version="1",
        )
    with pytest.raises(KnowledgeAuthorityError, match="quant_foundation_profile_hash_mismatch"):
        authority.resolve_quant_foundation_profile(
            profile_id=QUANT_FOUNDATION_PROFILE_ID,
            profile_version=QUANT_FOUNDATION_PROFILE_VERSION,
            expected_hash="0" * 64,
        )


def test_profile_activation_is_explicit_hash_locked_and_visible() -> None:
    foundation_v1 = bazi_foundation_profile()
    candidate_v1 = bazi_candidate_qualification_profile()
    quant_v1 = bazi_quant_foundation_profile()
    foundation_v2 = foundation_v1.model_copy(
        update={
            "profile_version": "1.0.1-test",
            "source_refs": foundation_v1.source_refs + ("test-only:admitted-foundation-profile",),
        }
    )
    candidate_v2 = candidate_v1.model_copy(
        update={
            "profile_version": "1.0.1-test",
            "source_refs": candidate_v1.source_refs + ("test-only:admitted-candidate-profile",),
        }
    )
    selection = KnowledgeProfileSelection.from_profiles(
        foundation=foundation_v2,
        candidate_rules=candidate_v2,
        quant_foundation=quant_v1,
    )
    authority = KnowledgeAuthority(
        profiles=(foundation_v1, foundation_v2),
        candidate_rule_profiles=(candidate_v1, candidate_v2),
        active_selection=selection,
    )

    assert authority.active_foundation_profile() is foundation_v2
    assert authority.active_candidate_rule_profile() is candidate_v2
    assert authority.selection_manifest()["selection_hash"] == (selection.selection_hash)
    assert [item["active"] for item in authority.public_manifest()] == [
        False,
        True,
    ]
    assert [item["active"] for item in authority.candidate_rule_manifest()] == [False, True]
    assert authority.quant_foundation_manifest()[0]["active"] is True


def test_profile_rejects_duplicate_relation_membership() -> None:
    payload = bazi_foundation_profile().model_dump(mode="json")
    payload["relations"][1] = payload["relations"][0]

    with pytest.raises(
        ValidationError,
        match="knowledge_profile_relations_must_be_unique",
    ):
        BaziFoundationProfile.model_validate(payload)


def test_candidate_rule_profile_rejects_duplicate_rule_identity() -> None:
    payload = bazi_candidate_qualification_profile().model_dump(mode="json")
    payload["rules"].append(payload["rules"][0])

    with pytest.raises(
        ValidationError,
        match="candidate_qualification_rule_identity_must_be_unique",
    ):
        BaziCandidateQualificationProfile.model_validate(payload)


def test_mingli_compiler_consumes_the_admitted_profile_source() -> None:
    birth_input = BirthInput(
        calendar_type="solar",
        birth_date=date(1977, 5, 8),
        birth_time=time(17, 30),
        timezone="Asia/Shanghai",
        true_solar_time_policy="not_applied",
    )
    compiled = compile_birth_case(
        case_ref="v60-test-knowledge-authority",
        birth_input=birth_input,
    )

    assert compiled.evidence_manifest["profile_source_ref"] == SOURCE_REF
    assert {fact["source_ref"] for fact in compiled.facts} == {SOURCE_REF}


def test_mingli_compiler_uses_the_explicit_active_profile_maps() -> None:
    foundation_v1 = bazi_foundation_profile()
    candidate_v1 = bazi_candidate_qualification_profile()
    quant_v1 = bazi_quant_foundation_profile()
    foundation_v2 = foundation_v1.model_copy(
        update={
            "profile_version": "1.0.1-test",
            "source_refs": foundation_v1.source_refs + ("test-only:admitted-foundation-profile",),
        }
    )
    authority = KnowledgeAuthority(
        profiles=(foundation_v1, foundation_v2),
        candidate_rule_profiles=(candidate_v1,),
        active_selection=KnowledgeProfileSelection.from_profiles(
            foundation=foundation_v2,
            candidate_rules=candidate_v1,
            quant_foundation=quant_v1,
        ),
    )
    birth_input = BirthInput(
        calendar_type="solar",
        birth_date=date(1977, 5, 8),
        birth_time=time(17, 30),
        timezone="Asia/Shanghai",
        true_solar_time_policy="not_applied",
    )

    compiled = compile_birth_case(
        case_ref="v60-test-selected-knowledge-profile",
        birth_input=birth_input,
        knowledge=authority,
    )

    assert compiled.evidence_manifest["profile_source_ref"] == (foundation_v2.source_ref)
    assert {fact["source_ref"] for fact in compiled.facts} == {foundation_v2.source_ref}


def test_runtime_manifest_exposes_only_admitted_knowledge_profiles() -> None:
    profiles = runtime_manifest()["knowledge_profiles"]

    assert profiles == KnowledgeAuthority().public_manifest()
    assert profiles[0]["profile_hash"] == EXPECTED_FOUNDATION_PROFILE_HASH
    rule_profiles = runtime_manifest()["candidate_rule_profiles"]
    assert rule_profiles == KnowledgeAuthority().candidate_rule_manifest()
    assert rule_profiles[0]["profile_hash"] == EXPECTED_CANDIDATE_RULE_PROFILE_HASH
    selection = runtime_manifest()["knowledge_profile_selection"]
    assert selection == KnowledgeAuthority().selection_manifest()
    assert selection["foundation_profile_hash"] == (EXPECTED_FOUNDATION_PROFILE_HASH)
    quant_profiles = runtime_manifest()["quant_foundation_profiles"]
    assert quant_profiles == KnowledgeAuthority().quant_foundation_manifest()
    assert quant_profiles[0]["profile_hash"] == (EXPECTED_QUANT_FOUNDATION_PROFILE_HASH)
    assert selection["quant_foundation_profile_hash"] == (EXPECTED_QUANT_FOUNDATION_PROFILE_HASH)
