from __future__ import annotations

from typing import Any

import pytest
from abu_v60.db import engine
from abu_v60.decision import ReasonerRuntimeUnavailable
from abu_v60.experience.home import (
    HomeExperienceService,
    HomeExperienceUnavailableError,
)
from abu_v60.mingli import (
    MechanismComparisonUnavailableError,
    MingliMechanismComparisonService,
    MingliMechanismVectorStore,
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
    assert all(
        item["subject_kind"] in {"HUMAN_OWNER", "HUMAN_REFERENCE"}
        and item["identity_badge"] in {"私密真实档案", "真实参考档案"}
        and item["stage_subject_id"]
        and item["birth_location_status"] in {"RECORDED", "HISTORICAL_MISSING"}
        for item in snapshot["case_options"]
    )
    assert all(
        {
            "gender",
            "calendar_type",
            "birth_date",
            "birth_time",
            "birth_location",
            "timezone",
            "lunar_leap_month",
        }
        <= item.keys()
        for item in snapshot["case_options"]
    )
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
    comparison = snapshot["lab"]["mechanism_comparison"]
    comparison_decision_ref = comparison["decision_ref"]
    decision_trace = comparison["decision_trace"]
    reading_focus = snapshot["mingli"]["reading_brief"]["focus"]
    assert snapshot["mingli"]["reading"]["decision_refs"] == (
        [comparison_decision_ref] if comparison_decision_ref is not None else []
    )
    if comparison_decision_ref is None:
        assert decision_trace is None
    else:
        assert decision_trace["decision_ref"] == comparison_decision_ref
        assert decision_trace["decision_hash"] == comparison["decision_hash"]
        assert decision_trace["selected_candidate_ref"] == (
            comparison["selected_candidate_ref"]
        )
        assert decision_trace["trace_integrity_status"] == "VERIFIED"
        assert decision_trace["candidate_coverage_complete"] is True
        assert decision_trace["selected_evidence_bound"] is True
        assert decision_trace["selected_evidence_use_semantics"] in {
            "PROVIDER_CITED_BOUND_EVIDENCE",
            "REQUEST_BOUND_RULE_NOT_PROVIDER_CITED",
        }
        assert decision_trace["professional_selection_qualified"] is False
        assert decision_trace["professional_verdict_allowed"] is False
        assert decision_trace["probability_claim_allowed"] is False
        assert decision_trace["canonical_domain_write_allowed"] is False
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


def test_home_source_discussion_receipt_is_shared_and_creates_no_decision() -> None:
    account_ref = _human_owner_account_ref()
    service = HomeExperienceService(engine)
    with engine.connect() as connection:
        decisions_before = connection.execute(
            text("SELECT count(*) FROM cognition.decision_records")
        ).scalar_one()

    first = service.snapshot(account_ref=account_ref)
    second = service.snapshot(account_ref=account_ref)
    receipt = first["mingli"]["source_discussion_receipt"]
    prerequisite = first["mingli"]["source_usability_prerequisite"]
    reading = first["mingli"]["reading"]
    source_review = first["mingli"]["source_coordinate_review"]

    with engine.connect() as connection:
        decisions_after = connection.execute(
            text("SELECT count(*) FROM cognition.decision_records")
        ).scalar_one()

    assert receipt == second["mingli"]["source_discussion_receipt"]
    assert receipt["case_ref"] == reading["case_ref"]
    assert receipt["chart_version_ref"] == reading["chart_version_ref"]
    assert (receipt["reading_ref"], receipt["reading_hash"]) == (
        reading["reading_ref"],
        reading["reading_hash"],
    )
    assert (
        receipt["source_review_vector_ref"],
        receipt["source_review_vector_hash"],
    ) == (source_review["vector_ref"], source_review["vector_hash"])
    assert (receipt["prerequisite_ref"], receipt["prerequisite_hash"]) == (
        prerequisite["prerequisite_ref"],
        prerequisite["prerequisite_hash"],
    )
    assert receipt["carrier_refs"] == [
        item["carrier_ref"] for item in prerequisite["carriers"]
    ]
    assert receipt["carrier_count"] == prerequisite["carrier_count"]
    assert receipt["ready_carrier_count"] == 0
    assert receipt["abstained_claims"] == [
        "RELATION_EFFECT",
        "SOURCE_USABILITY",
    ]
    assert receipt["disposition"] == "ABSTAIN"
    assert receipt["reason"] == "NO_ADMITTED_PROFESSIONAL_RULE_CHAIN"
    assert receipt["output_mode"] == "FACTS_AND_GAPS_ONLY"
    assert "PROFESSIONAL_ADMISSION" in receipt["blocking_requirement_ids"]
    assert receipt["provider_invoked"] is False
    assert receipt["decision_created"] is False
    assert receipt["discussion_allowed"] is False
    assert receipt["professional_verdict_allowed"] is False
    assert receipt["probability_claim_allowed"] is False
    assert receipt["canonical_write_allowed"] is False
    assert receipt["read_only"] is True
    assert first["lab"]["source_discussion_receipt_ref"] == receipt["receipt_ref"]
    assert first["lab"]["source_discussion_receipt_hash"] == receipt["receipt_hash"]
    assert decisions_after == decisions_before


def test_home_relation_effect_frontier_is_shared_and_creates_no_decision() -> None:
    account_ref = _human_owner_account_ref()
    service = HomeExperienceService(engine)
    with engine.connect() as connection:
        decisions_before = connection.execute(
            text("SELECT count(*) FROM cognition.decision_records")
        ).scalar_one()

    first = service.snapshot(account_ref=account_ref)
    second = service.snapshot(account_ref=account_ref)
    frontier = first["mingli"]["relation_effect_frontier"]
    reading = first["mingli"]["reading"]
    source_review = first["mingli"]["source_coordinate_review"]
    prerequisite = first["mingli"]["source_usability_prerequisite"]
    refusal = first["mingli"]["source_discussion_receipt"]

    with engine.connect() as connection:
        decisions_after = connection.execute(
            text("SELECT count(*) FROM cognition.decision_records")
        ).scalar_one()

    assert frontier == second["mingli"]["relation_effect_frontier"]
    assert (frontier["reading_ref"], frontier["reading_hash"]) == (
        reading["reading_ref"],
        reading["reading_hash"],
    )
    assert (
        frontier["source_review_vector_ref"],
        frontier["source_review_vector_hash"],
    ) == (source_review["vector_ref"], source_review["vector_hash"])
    assert (frontier["prerequisite_ref"], frontier["prerequisite_hash"]) == (
        prerequisite["prerequisite_ref"],
        prerequisite["prerequisite_hash"],
    )
    assert (
        frontier["refusal_receipt_ref"],
        frontier["refusal_receipt_hash"],
    ) == (refusal["receipt_ref"], refusal["receipt_hash"])
    assert source_review["source_evidence_count"] == 10
    assert source_review["clear_coordinate_count"] == 7
    assert source_review["review_required_count"] == 3
    assert frontier["demand_count"] == 3
    assert frontier["scope_invariant_rule_demand_count"] == 1
    assert frontier["match_scope_rule_first_count"] == 2
    assert frontier["admitted_effect_rule_count"] == 0
    assert frontier["source_discussion_disposition"] == "ABSTAIN"
    assert frontier["provider_invoked"] is False
    assert frontier["decision_created"] is False
    assert frontier["gate_invoked"] is False
    assert frontier["professional_verdict_allowed"] is False
    assert frontier["probability_claim_allowed"] is False
    assert frontier["canonical_write_allowed"] is False
    assert first["lab"]["relation_effect_frontier_ref"] == frontier["frontier_ref"]
    assert first["lab"]["relation_effect_frontier_hash"] == frontier["frontier_hash"]
    assert decisions_after == decisions_before


def test_home_relation_effect_admission_review_is_shared_and_creates_no_decision() -> None:
    account_ref = _human_owner_account_ref()
    service = HomeExperienceService(engine)
    with engine.connect() as connection:
        decisions_before = connection.execute(
            text("SELECT count(*) FROM cognition.decision_records")
        ).scalar_one()

    first = service.snapshot(account_ref=account_ref)
    second = service.snapshot(account_ref=account_ref)
    review = first["mingli"]["relation_effect_admission_review"]
    frontier = first["mingli"]["relation_effect_frontier"]
    source_review = first["mingli"]["source_coordinate_review"]

    with engine.connect() as connection:
        decisions_after = connection.execute(
            text("SELECT count(*) FROM cognition.decision_records")
        ).scalar_one()

    assert review == second["mingli"]["relation_effect_admission_review"]
    assert source_review["source_evidence_count"] == 10
    assert source_review["clear_coordinate_count"] == 7
    assert source_review["review_required_count"] == 3
    assert (review["frontier_ref"], review["frontier_hash"]) == (
        frontier["frontier_ref"],
        frontier["frontier_hash"],
    )
    assert review["reviewed_demand_count"] == 1
    assert review["rejected_pre_admission_count"] == 1
    assert review["admitted_effect_rule_count"] == 0
    assert len(review["deferred_match_scope_demand_refs"]) == 2
    assert review["unreviewed_scope_invariant_demand_refs"] == []
    assert review["disposition"] == "REJECTED_PRE_ADMISSION"
    assert review["effect_status"] == "UNRESOLVED"
    assert review["usability_status"] == "UNRESOLVED"
    assert review["provider_invoked"] is False
    assert review["owner_professional_review_invoked"] is False
    assert review["knowledge_promotion_request_created"] is False
    assert review["gate_invoked"] is False
    assert review["decision_created"] is False
    assert review["selection_authority"] is False
    assert review["professional_verdict_allowed"] is False
    assert review["probability_claim_allowed"] is False
    assert review["canonical_write_allowed"] is False
    assert review["read_only"] is True
    assert first["lab"]["relation_effect_admission_review_ref"] == (
        review["review_ref"]
    )
    assert first["lab"]["relation_effect_admission_review_hash"] == (
        review["review_hash"]
    )
    assert decisions_after == decisions_before


def test_home_relation_effect_evidence_packet_is_shared_and_creates_no_decision() -> None:
    account_ref = _human_owner_account_ref()
    service = HomeExperienceService(engine)
    with engine.connect() as connection:
        decisions_before = connection.execute(
            text("SELECT count(*) FROM cognition.decision_records")
        ).scalar_one()

    first = service.snapshot(account_ref=account_ref)
    second = service.snapshot(account_ref=account_ref)
    packet = first["mingli"]["relation_effect_evidence_packet"]
    reading = first["mingli"]["reading"]
    frontier = first["mingli"]["relation_effect_frontier"]
    review = first["mingli"]["relation_effect_admission_review"]
    source_review = first["mingli"]["source_coordinate_review"]

    with engine.connect() as connection:
        decisions_after = connection.execute(
            text("SELECT count(*) FROM cognition.decision_records")
        ).scalar_one()

    assert packet == second["mingli"]["relation_effect_evidence_packet"]
    assert source_review["source_evidence_count"] == 10
    assert source_review["clear_coordinate_count"] == 7
    assert source_review["review_required_count"] == 3
    assert (packet["case_ref"], packet["chart_version_ref"]) == (
        reading["case_ref"],
        reading["chart_version_ref"],
    )
    assert (packet["reading_ref"], packet["reading_hash"]) == (
        reading["reading_ref"],
        reading["reading_hash"],
    )
    assert (packet["frontier_ref"], packet["frontier_hash"]) == (
        frontier["frontier_ref"],
        frontier["frontier_hash"],
    )
    assert (
        packet["admission_review_ref"],
        packet["admission_review_hash"],
    ) == (review["review_ref"], review["review_hash"])
    assert packet["demand_packet_count"] == (
        review["reviewed_demand_count"]
    )
    assert packet["demand_packet_count"] == 1
    assert packet["required_dimension_slot_count"] == 6
    assert packet["ready_dimension_slot_count"] == 0
    assert packet["professional_evidence_count"] == 0
    assert packet["status"] == "EVIDENCE_INTAKE_REQUIRED"
    assert packet["projection_semantics"] == (
        "PROFESSIONAL_EVIDENCE_READINESS_NOT_DECISION"
    )
    assert packet["decision_path_semantics"] == (
        "READINESS_PATH_NOT_DECISION"
    )
    assert packet["decision_path"] == [
        "DETERMINISTIC_RELATION_FACT_AVAILABLE",
        "PROFESSIONAL_RULE_EVIDENCE_BLOCKED",
        "OWNER_PROFESSIONAL_REVIEW_NOT_INVOKED",
        "KNOWLEDGE_ADMISSION_NOT_ELIGIBLE",
        "READING_RULE_PROFILE_QUALIFICATION_NOT_AUTHORIZED",
        "EFFECT_DECISION_WITHHELD",
    ]
    assert packet["required_professional_path_semantics"] == (
        "FUTURE_AUTHORITY_PATH_NOT_EXECUTED"
    )
    assert packet["required_professional_path"] == [
        "COMPLETE_PROFESSIONAL_EVIDENCE_PACKET",
        "OWNER_PROFESSIONAL_REVIEW_APPROVED",
        "KNOWLEDGE_IMMUTABLE_RULE_PROFILE_ADMITTED",
        "NEW_READING_BINDS_ADMITTED_RULE_PROFILE",
        "DETERMINISTIC_RULE_APPLICATION_OR_UNRESOLVED",
    ]
    assert packet["effect_decision_status"] == "WITHHELD"
    assert all(
        item["professional_evidence_refs"] == []
        and item["professional_evidence_count"] == 0
        and item["ready"] is False
        for demand_packet in packet["demand_packets"]
        for item in demand_packet["dimension_slots"]
    )
    current_basis_refs = {
        basis_ref
        for demand_packet in packet["demand_packets"]
        for item in demand_packet["dimension_slots"]
        for basis_ref in item["current_basis_refs"]
    }
    assert current_basis_refs.isdisjoint(reading["decision_refs"])
    assert '"decision_ref"' not in canonical_json(packet)
    assert first["lab"]["relation_effect_evidence_packet_ref"] == (
        packet["packet_ref"]
    )
    assert first["lab"]["relation_effect_evidence_packet_hash"] == (
        packet["packet_hash"]
    )
    assert reading["decision_refs"] == second["mingli"]["reading"][
        "decision_refs"
    ]
    assert decisions_after == decisions_before


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


def test_mechanism_comparison_rejects_wrong_account_before_decision() -> None:
    account_ref = _human_owner_account_ref()
    snapshot = HomeExperienceService(engine).snapshot(
        account_ref=account_ref
    )
    vector = MingliMechanismVectorStore(engine).get(
        vector_ref=str(snapshot["lab"]["mechanism_vector_ref"])
    )

    class ForbiddenCoordinator:
        @staticmethod
        def decide_and_record(**_kwargs):
            raise AssertionError("ownership fence must precede decision")

    service = MingliMechanismComparisonService(
        engine,
        coordinator=ForbiddenCoordinator(),
    )

    with pytest.raises(
        MechanismComparisonUnavailableError,
        match="mechanism_comparison_active_owner_case_conflict",
    ):
        service.compare(
            account_ref="v60-account-wrong-mechanism-owner",
            vector=vector,
        )


def test_mechanism_comparison_rejects_owned_non_owner_case() -> None:
    with engine.connect() as connection:
        reference_row = (
            connection.execute(
                text(
                    """
                    SELECT vector.vector_ref,
                           owner_case.owner_account_ref
                    FROM mingli.mechanism_evidence_vectors AS vector
                    JOIN mingli.cases AS owner_case
                      ON owner_case.case_ref = vector.case_ref
                    WHERE owner_case.subject_kind = 'HUMAN_REFERENCE'
                      AND owner_case.status = 'ACTIVE'
                    ORDER BY vector.vector_ref
                    LIMIT 1
                    """
                )
            )
            .mappings()
            .one()
        )
    account_ref = str(reference_row["owner_account_ref"])
    vector = MingliMechanismVectorStore(engine).get(
        vector_ref=str(reference_row["vector_ref"])
    )

    class ForbiddenCoordinator:
        @staticmethod
        def decide_and_record(**_kwargs):
            raise AssertionError("case fence must precede decision")

    service = MingliMechanismComparisonService(
        engine,
        coordinator=ForbiddenCoordinator(),
    )

    with engine.begin() as connection, pytest.raises(
        MechanismComparisonUnavailableError,
        match="mechanism_comparison_active_owner_case_conflict",
    ):
        service.compare_in_connection(
            connection,
            account_ref=account_ref,
            vector=vector,
        )


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
