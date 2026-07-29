from __future__ import annotations

from typing import Any

import pytest
from abu_v60.db import engine
from abu_v60.decision import ReasonerRuntimeUnavailable
from abu_v60.experience.home import (
    HomeExperienceService,
    HomeExperienceUnavailableError,
)
from abu_v60.provenance import canonical_json
from sqlalchemy import text


def _human_owner_account_ref() -> str:
    with engine.connect() as connection:
        return str(
            connection.execute(
                text(
                    """
                    SELECT DISTINCT owner_account_ref
                    FROM mingli.cases
                    WHERE subject_kind = 'HUMAN_OWNER'
                      AND status = 'ACTIVE'
                    ORDER BY owner_account_ref
                    LIMIT 1
                    """
                )
            ).scalar_one()
        )


def test_home_experience_uses_only_the_signed_in_human_owner_case() -> None:
    snapshot = HomeExperienceService(engine).snapshot(account_ref=_human_owner_account_ref())

    assert snapshot["scope"] == "HOME_CASE"
    assert snapshot["case"]["subject_kind"] == "HUMAN_OWNER"
    assert snapshot["case"]["status"] == "ACTIVE"
    assert snapshot["tree"]["read_only"] is True
    assert snapshot["tree"]["phenotype"]["semantic_status"] == "VISUAL_METAPHOR_ONLY"
    reading = snapshot["mingli"]["reading"]
    explanation = snapshot["mingli"]["explanation"]
    expression = snapshot["mingli"]["abu_expression"]
    assert reading["case_ref"] == snapshot["case"]["case_ref"]
    assert reading["chart_version_ref"] == snapshot["chart"]["chart_version_ref"]
    assert reading["life_case_revision_ref"] == snapshot["life_case"]["life_case_revision_ref"]
    assert expression["reading_ref"] == reading["reading_ref"]
    assert explanation["reading_ref"] == reading["reading_ref"]
    assert explanation["reading_hash"] == reading["reading_hash"]
    assert expression["explanation_ref"] == explanation["explanation_ref"]
    assert expression["explanation_hash"] == explanation["explanation_hash"]
    assert snapshot["lab"]["reading_ref"] == reading["reading_ref"]
    assert snapshot["lab"]["explanation_ref"] == explanation["explanation_ref"]
    assert snapshot["lab"]["explanation_hash"] == explanation["explanation_hash"]
    assert snapshot["units"]["abu"]["reading_ref"] == reading["reading_ref"]
    assert expression["authority"] == "EXPRESSION_ONLY"
    assert expression["fact_creation"] is False
    assert expression["decision_creation"] is False
    assert expression["confirmed_claim_count"] == explanation["confirmed_count"]
    assert expression["candidate_claim_count"] == explanation["candidate_count"]
    assert expression["observation_claim_count"] == explanation["observation_count"]
    brief = snapshot["mingli"]["reading_brief"]
    assert brief["lineage"]["reading_ref"] == reading["reading_ref"]
    assert brief["lineage"]["reading_hash"] == reading["reading_hash"]
    assert brief["professional_verdict"] is False
    assert brief["probability_claim"] is False
    assert brief["canonical_write_allowed"] is False
    assert brief["qualification"]["status"] == "FORMAL_BOUNDED_READING"
    assert brief["qualification"]["fact_count"] == len(snapshot["mingli"]["facts"])
    assert len(snapshot["case_options"]) >= 1
    assert sum(1 for item in snapshot["case_options"] if item["active"]) == 1
    assert len(brief["confirmed"]) == 3
    assert [item["domain"] for item in brief["life_domains"]] == [
        "career",
        "wealth",
        "relationship",
    ]
    assert explanation["professional_verdict"] is False
    assert explanation["probability_claim"] is False
    assert explanation["canonical_write_allowed"] is False
    assert explanation["read_only"] is True
    assert explanation["confirmed_count"] == 1
    assert explanation["candidate_count"] == len(
        snapshot["mingli"]["mechanism_evidence"]["candidates"]
    )
    assert explanation["observation_count"] == 3
    assert [item["epistemic_status"] for item in explanation["claims"]].count(
        "CONFIRMED"
    ) == 1
    assert all(item["support_evidence"] for item in explanation["claims"])
    assert snapshot["lab"]["research_admission_status"] == ("PROFILE_ADMISSION_REQUIRED")
    with engine.connect() as connection:
        persisted = connection.execute(
            text(
                """
                SELECT reading_json
                FROM mingli.readings
                WHERE reading_ref = :reading_ref
                """
            ),
            {"reading_ref": reading["reading_ref"]},
        ).scalar_one()
    assert persisted == reading
    assert snapshot["boundaries"] == {
        "private_to_account": True,
        "dream_encounter_subject": False,
        "canonical_write_allowed": False,
        "visual_semantics": "VISUAL_METAPHOR_ONLY",
    }


def test_home_projection_contains_no_dream_subject_or_mutable_dream_state() -> None:
    snapshot = HomeExperienceService(engine).snapshot(account_ref=_human_owner_account_ref())
    serialized = canonical_json(snapshot)
    with engine.connect() as connection:
        synthetic_case_refs = connection.execute(
            text(
                """
                SELECT case_ref
                FROM mingli.cases
                WHERE subject_kind = 'CANONICAL_SYNTHETIC'
                """
            )
        ).scalars()

    assert all(str(case_ref) not in serialized for case_ref in synthetic_case_refs)
    assert all(
        forbidden not in snapshot
        for forbidden in (
            "encounter",
            "actor",
            "question",
            "human_seal",
            "fruit",
            "reveal",
        )
    )
    fact_refs = set(snapshot["lineage"]["fact_refs"])
    assert all(
        set(candidate["evidence_refs"]) <= fact_refs
        for candidate in snapshot["lab"]["candidate_paths"]
    )
    comparison_decision_ref = snapshot["lab"]["mechanism_comparison"]["decision_ref"]
    reading_focus = snapshot["mingli"]["reading_brief"]["focus"]
    assert snapshot["mingli"]["reading"]["decision_refs"] == (
        [comparison_decision_ref] if comparison_decision_ref is not None else []
    )
    if reading_focus["candidate_ref"] is None:
        assert reading_focus["support"] is None
    else:
        assert reading_focus["support"]["direct_fact_count"] > 0
        assert reading_focus["support"]["visible_occurrence_count"] > 0
        assert "专业准入" in reading_focus["support"]["unresolved"]
    assert snapshot["lab"]["canonical_write_allowed"] is False
    mechanism = snapshot["mingli"]["mechanism_evidence"]
    domains = snapshot["mingli"]["life_domains"]
    assert len(mechanism["candidates"]) >= 1
    explanation = snapshot["mingli"]["explanation"]
    candidate_claims = [
        item
        for item in explanation["claims"]
        if item["claim_kind"] == "MECHANISM_CANDIDATE"
    ]
    assert len(candidate_claims) == len(mechanism["candidates"])
    assert all(
        item["epistemic_status"] == "CANDIDATE"
        and item["counter_evidence_status"] == "NOT_ADMITTED"
        and item["counter_evidence"] == []
        and "不能直接写成有效做功" in item["boundary"]
        and item["unresolved_questions"]
        for item in candidate_claims
    )
    observation_claims = [
        item
        for item in explanation["claims"]
        if item["claim_kind"] == "LIFE_DOMAIN_WINDOW"
    ]
    assert len(observation_claims) == 3
    assert all(
        item["epistemic_status"] == "OBSERVE"
        and "不是事件预言" in item["boundary"]
        for item in observation_claims
    )
    assert snapshot["lab"]["mechanism_vector_ref"] == mechanism["vector_ref"]
    assert snapshot["lab"]["mechanism_vector_hash"] == mechanism["vector_hash"]
    assert snapshot["lab"]["mechanism_comparison"]["meaning"] == ("ATTENTION_PRIORITY_ONLY")
    assert snapshot["lab"]["mechanism_comparison"]["professional_verdict"] is False
    assert snapshot["lab"]["mechanism_comparison"]["canonical_mingli_write_allowed"] is False
    assert snapshot["lab"]["mechanism_comparison"]["reasoner_runtime"]["status"] == (
        "NOT_CONFIGURED"
    )
    with engine.connect() as connection:
        persisted_mechanism = connection.execute(
            text(
                """
                SELECT vector_json
                FROM mingli.mechanism_evidence_vectors
                WHERE vector_ref = :vector_ref
                """
            ),
            {"vector_ref": mechanism["vector_ref"]},
        ).scalar_one()
    assert persisted_mechanism == mechanism
    assert domains["case_ref"] == snapshot["case"]["case_ref"]
    assert domains["timing_vector_ref"] == snapshot["lab"]["timing_vector_ref"]
    assert domains["mechanism_vector_ref"] == snapshot["lab"]["mechanism_vector_ref"]
    assert [item["domain"] for item in domains["observations"]] == [
        "career",
        "wealth",
        "relationship",
    ]
    assert all(
        item["outcome_status"] == "UNRESOLVED"
        and item["probability_status"] == "NOT_COMPUTED"
        for item in domains["observations"]
    )
    with engine.connect() as connection:
        persisted_domains = connection.execute(
            text(
                """
                SELECT vector_json
                FROM mingli.life_domain_evidence_vectors
                WHERE vector_ref = :vector_ref
                """
            ),
            {"vector_ref": domains["vector_ref"]},
        ).scalar_one()
    assert persisted_domains == domains


def test_home_explanation_is_stable_and_contains_no_outcome_verdict() -> None:
    service = HomeExperienceService(engine)
    first = service.snapshot(account_ref=_human_owner_account_ref())
    second = service.snapshot(account_ref=_human_owner_account_ref())
    explanation = first["mingli"]["explanation"]

    assert explanation == second["mingli"]["explanation"]
    assert explanation["explanation_ref"] == second["lab"]["explanation_ref"]
    serialized = canonical_json(explanation)
    assert '"professional_verdict":false' in serialized
    assert '"probability_claim":false' in serialized
    assert "SUPPORTED" not in serialized
    assert "NOT_SUPPORTED" not in serialized
    assert "sealed_outcome" not in serialized


def test_home_mechanism_comparison_fails_closed_or_replays_existing_record() -> None:
    service = HomeExperienceService(engine)
    snapshot = service.snapshot(account_ref=_human_owner_account_ref())
    decision_ref = snapshot["lab"]["mechanism_comparison"]["decision_ref"]

    if decision_ref is None:
        with pytest.raises(
            ReasonerRuntimeUnavailable,
            match="bounded_reasoner_not_ready",
        ):
            service.compare_mechanisms(account_ref=_human_owner_account_ref())
        return

    replay = service.compare_mechanisms(account_ref=_human_owner_account_ref())

    assert replay["decision_ref"] == decision_ref
    assert replay["already_recorded"] is True
    assert replay["reasoner_execution"] is None
    assert replay["canonical_mingli_write_allowed"] is False


class _AmbiguousCaseService:
    def list_cases(self, *, account_ref: str) -> list[dict[str, Any]]:
        return [
            {
                "case_ref": "case-a",
                "subject_kind": "HUMAN_OWNER",
                "status": "ACTIVE",
            },
            {
                "case_ref": "case-b",
                "subject_kind": "HUMAN_OWNER",
                "status": "ACTIVE",
            },
        ]

    def workspace(self, *, account_ref: str, case_ref: str) -> dict[str, Any]:
        raise AssertionError("ambiguous home case must fail before workspace load")


def test_home_experience_fails_closed_when_case_selection_is_ambiguous() -> None:
    service = HomeExperienceService(engine, cases=_AmbiguousCaseService())  # type: ignore[arg-type]

    with pytest.raises(
        HomeExperienceUnavailableError,
        match="home_case_selection_required",
    ):
        service.snapshot(account_ref="account-owner")
