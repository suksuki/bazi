from __future__ import annotations

import pytest
from abu_v60.knowledge import (
    RELATION_EFFECT_RULE_DIMENSIONS,
    KnowledgeAuthority,
    KnowledgeAuthorityError,
    bazi_relation_effect_admission_policy,
    bazi_zi_wu_automatic_damage_proposal,
)
from abu_v60.mingli import (
    RELATION_EFFECT_EVIDENCE_DECISION_PATH,
    RELATION_EFFECT_EVIDENCE_PACKET_VERSION,
    RELATION_EFFECT_REQUIRED_PROFESSIONAL_PATH,
    MingliRelationEffectAdmissionProjector,
    MingliRelationEffectAdmissionReviewEnvelope,
    MingliRelationEffectEvidencePacketEnvelope,
    MingliRelationEffectEvidencePacketProjector,
    RelationEffectRuleAdmissionAssessment,
)
from abu_v60.mingli.calendar import ChartPillars
from abu_v60.provenance import content_hash, stable_ref
from mingli_relation_effect_test_support import (
    project_relation_effect_frontier,
    relation_effect_bundle,
)


def _evidence_packet(
    pillars: ChartPillars,
    *,
    reverse_facts: bool = False,
):
    bundle = relation_effect_bundle(
        pillars,
        reverse_facts=reverse_facts,
    )
    frontier = project_relation_effect_frontier(bundle)
    review = MingliRelationEffectAdmissionProjector().project(
        frontier=frontier
    )
    packet = MingliRelationEffectEvidencePacketProjector().project(
        reading=bundle["reading"],
        frontier=frontier,
        admission_review=review,
    )
    return bundle, frontier, review, packet


def test_relation_effect_evidence_packet_projects_real_10_7_3_readiness() -> None:
    pillars = ChartPillars(
        year="己巳",
        month="丙子",
        day="丙寅",
        hour="甲午",
    )
    bundle, frontier, review, first = _evidence_packet(pillars)
    _, _, _, second = _evidence_packet(
        pillars,
        reverse_facts=True,
    )
    source_review = bundle["source_review"]
    reading = bundle["reading"]

    assert first == second
    assert (
        first.packet_version
        == RELATION_EFFECT_EVIDENCE_PACKET_VERSION
    )
    assert source_review.source_evidence_count == 10
    assert source_review.clear_coordinate_count == 7
    assert source_review.review_required_count == 3
    assert frontier.demand_count == 3
    assert review.reviewed_demand_count == 1
    assert first.demand_packet_count == 1
    assert first.required_dimension_slot_count == 6
    assert first.ready_dimension_slot_count == 0
    assert first.professional_evidence_count == 0
    assert first.status == "EVIDENCE_INTAKE_REQUIRED"
    assert first.projection_semantics == (
        "PROFESSIONAL_EVIDENCE_READINESS_NOT_DECISION"
    )
    assert first.decision_path_semantics == (
        "READINESS_PATH_NOT_DECISION"
    )
    assert first.decision_path == (
        RELATION_EFFECT_EVIDENCE_DECISION_PATH
    )
    assert first.required_professional_path_semantics == (
        "FUTURE_AUTHORITY_PATH_NOT_EXECUTED"
    )
    assert first.required_professional_path == (
        RELATION_EFFECT_REQUIRED_PROFESSIONAL_PATH
    )
    assert first.effect_decision_status == "WITHHELD"
    assert (first.case_ref, first.chart_version_ref) == (
        reading.case_ref,
        reading.chart_version_ref,
    )
    assert (first.reading_ref, first.reading_hash) == (
        reading.reading_ref,
        reading.reading_hash,
    )
    assert (first.frontier_ref, first.frontier_hash) == (
        frontier.frontier_ref,
        frontier.frontier_hash,
    )
    assert (
        first.admission_review_ref,
        first.admission_review_hash,
    ) == (review.review_ref, review.review_hash)

    demand_packet = first.demand_packets[0]
    assessment = review.assessments[0]
    demand = next(
        item
        for item in frontier.demands
        if item.demand_ref == assessment.demand_ref
    )
    assert (
        demand_packet.assessment_ref,
        demand_packet.assessment_hash,
    ) == (assessment.assessment_ref, assessment.assessment_hash)
    assert demand_packet.demand_ref == demand.demand_ref
    assert (
        demand_packet.visible_slot,
        demand_packet.visible_stem,
        demand_packet.source_slot,
        demand_packet.source_branch,
        demand_packet.peer_slot,
        demand_packet.peer_branch,
    ) == ("year", "己", "hour", "午", "month", "子")
    assert demand_packet.required_dimension_slot_count == 6
    assert demand_packet.ready_dimension_slot_count == 0
    assert demand_packet.professional_evidence_count == 0
    assert demand_packet.status == "EVIDENCE_INTAKE_REQUIRED"
    assert [
        item.dimension_id
        for item in demand_packet.dimension_slots
    ] == list(RELATION_EFFECT_RULE_DIMENSIONS)
    assert [
        item.current_basis_refs
        for item in demand_packet.dimension_slots
    ] == [
        item.current_basis_refs
        for item in assessment.dimension_assessments
    ]
    assert all(
        item.current_basis_status
        == "RUNTIME_CONTEXT_ONLY_NOT_PROFESSIONAL_EVIDENCE"
        and item.guidance_semantics
        == "REQUEST_GUIDANCE_NOT_KNOWLEDGE_ADMISSION"
        and item.professional_evidence_refs == ()
        and item.professional_evidence_count == 0
        and item.slot_status
        == "BLOCKED_MISSING_PROFESSIONAL_EVIDENCE"
        and item.requested_artifact_kinds
        and item.requirement
        and item.next_action
        and item.ready is False
        and not (
            set(item.current_basis_refs)
            & set(item.professional_evidence_refs)
        )
        for item in demand_packet.dimension_slots
    )
    assert all(
        getattr(first, name) is False
        for name in (
            "knowledge_admission_eligible",
            "llm_allowed",
            "provider_invoked",
            "reasoner_invoked",
            "decision_request_created",
            "owner_professional_review_invoked",
            "knowledge_promotion_request_created",
            "gate_invoked",
            "ledger_invoked",
            "decision_created",
            "selection_authority",
            "professional_verdict_allowed",
            "probability_claim_allowed",
            "canonical_write_allowed",
        )
    )
    assert first.read_only is True


def test_relation_effect_evidence_clear_case_creates_zero_demand_packets() -> None:
    _, frontier, review, packet = _evidence_packet(
        ChartPillars(
            year="丁巳",
            month="乙巳",
            day="乙丑",
            hour="乙酉",
        )
    )

    assert frontier.demands == ()
    assert review.disposition == "NOT_TRIGGERED"
    assert packet.demand_packets == ()
    assert packet.demand_packet_count == 0
    assert packet.required_dimension_slot_count == 0
    assert packet.ready_dimension_slot_count == 0
    assert packet.professional_evidence_count == 0
    assert packet.status == "NOT_TRIGGERED"
    assert packet.decision_path == ()
    assert packet.effect_decision_status == "NOT_TRIGGERED"


def test_relation_effect_evidence_fails_closed_on_rehashed_lineage() -> None:
    bundle, frontier, review, _ = _evidence_packet(
        ChartPillars(
            year="己巳",
            month="丙子",
            day="丙寅",
            hour="甲午",
        )
    )
    frontier_identity = frontier.model_dump(
        mode="json",
        exclude={"frontier_ref", "frontier_hash"},
    )
    frontier_identity["case_ref"] = "case-cross-lineage"
    rehashed_frontier = type(frontier)(
        frontier_ref=stable_ref(
            "v60-relation-effect-research-frontier",
            frontier_identity,
        ),
        frontier_hash=content_hash(frontier_identity),
        **frontier_identity,
    )

    with pytest.raises(
        ValueError,
        match="relation_effect_evidence_frontier_reading_mismatch",
    ):
        MingliRelationEffectEvidencePacketProjector().project(
            reading=bundle["reading"],
            frontier=rehashed_frontier,
            admission_review=review,
        )


def test_relation_effect_evidence_revalidates_reading_frontier_and_review_hashes() -> None:
    bundle, frontier, review, _ = _evidence_packet(
        ChartPillars(
            year="己巳",
            month="丙子",
            day="丙寅",
            hour="甲午",
        )
    )
    projector = MingliRelationEffectEvidencePacketProjector()

    with pytest.raises(
        ValueError,
        match="mingli_reading_hash_mismatch",
    ):
        projector.project(
            reading=bundle["reading"].model_copy(
                update={"reading_hash": "f" * 64}
            ),
            frontier=frontier,
            admission_review=review,
        )
    with pytest.raises(
        ValueError,
        match="relation_effect_frontier_hash_mismatch",
    ):
        projector.project(
            reading=bundle["reading"],
            frontier=frontier.model_copy(
                update={"reading_hash": "f" * 64}
            ),
            admission_review=review,
        )
    with pytest.raises(
        ValueError,
        match="relation_effect_review_hash_mismatch",
    ):
        projector.project(
            reading=bundle["reading"],
            frontier=frontier,
            admission_review=review.model_copy(
                update={"frontier_hash": "f" * 64}
            ),
        )


def test_relation_effect_evidence_fails_closed_on_rehashed_coordinate_drift() -> None:
    bundle, frontier, review, _ = _evidence_packet(
        ChartPillars(
            year="己巳",
            month="丙子",
            day="丙寅",
            hour="甲午",
        )
    )
    assessment = review.assessments[0]
    assessment_identity = assessment.model_dump(
        mode="json",
        exclude={"assessment_ref", "assessment_hash"},
    )
    assessment_identity["source_slot"] = "day"
    forged_assessment = RelationEffectRuleAdmissionAssessment(
        assessment_ref=stable_ref(
            "v60-relation-effect-admission-assessment",
            assessment_identity,
        ),
        assessment_hash=content_hash(assessment_identity),
        **assessment_identity,
    )
    review_identity = review.model_dump(
        mode="json",
        exclude={"review_ref", "review_hash"},
    )
    review_identity["assessments"] = (
        forged_assessment.model_dump(mode="json"),
    )
    forged_review = MingliRelationEffectAdmissionReviewEnvelope(
        review_ref=stable_ref(
            "v60-relation-effect-admission-review",
            review_identity,
        ),
        review_hash=content_hash(review_identity),
        **review_identity,
    )

    with pytest.raises(
        ValueError,
        match="relation_effect_evidence_admission_review_not_canonical",
    ):
        MingliRelationEffectEvidencePacketProjector().project(
            reading=bundle["reading"],
            frontier=frontier,
            admission_review=forged_review,
        )


def test_relation_effect_evidence_rejects_version_and_packet_forgery() -> None:
    _, _, _, packet = _evidence_packet(
        ChartPillars(
            year="己巳",
            month="丙子",
            day="丙寅",
            hour="甲午",
        )
    )
    version_drift = packet.model_dump(mode="python")
    version_drift["packet_version"] = (
        "v60.mingli-relation-effect-evidence-packet.999"
    )
    with pytest.raises(ValueError, match="packet_version"):
        MingliRelationEffectEvidencePacketEnvelope.model_validate(
            version_drift
        )

    slot_drift = packet.model_dump(mode="python")
    slot_drift["demand_packets"][0]["dimension_slots"][0][
        "professional_evidence_refs"
    ] = ("artifact:forged",)
    with pytest.raises(
        ValueError,
        match=(
            "relation_effect_evidence_slot_"
            "professional_evidence_not_admitted"
        ),
    ):
        MingliRelationEffectEvidencePacketEnvelope.model_validate(
            slot_drift
        )


def test_relation_effect_evidence_requires_canonical_knowledge_registry() -> None:
    bundle = relation_effect_bundle(
        ChartPillars(
            year="己巳",
            month="丙子",
            day="丙寅",
            hour="甲午",
        )
    )
    frontier = project_relation_effect_frontier(bundle)
    review = MingliRelationEffectAdmissionProjector().project(
        frontier=frontier
    )
    authority = KnowledgeAuthority(
        relation_effect_admission_policies=(),
    )

    with pytest.raises(
        KnowledgeAuthorityError,
        match="relation_effect_admission_policy_not_registered",
    ):
        MingliRelationEffectEvidencePacketProjector(
            authority=authority
        ).project(
            reading=bundle["reading"],
            frontier=frontier,
            admission_review=review,
        )

    assert bazi_relation_effect_admission_policy().professionally_reviewed is False
    proposal = bazi_zi_wu_automatic_damage_proposal()
    assert proposal.professional_source_manifest == ()
    assert all(
        item.evidence_refs == ()
        for item in proposal.dimension_submissions
    )
