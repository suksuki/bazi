from __future__ import annotations

import pytest
from abu_v60.knowledge import (
    RELATION_EFFECT_RULE_DIMENSIONS,
    BaziRelationEffectRuleProposal,
    KnowledgeAuthority,
    KnowledgeAuthorityError,
    RelationEffectProposalDimension,
    bazi_relation_effect_admission_policy,
    bazi_zi_wu_automatic_damage_proposal,
)
from abu_v60.mingli import (
    RELATION_EFFECT_ADMISSION_REVIEW_VERSION,
    MingliRelationEffectAdmissionProjector,
    MingliRelationEffectAdmissionReviewEnvelope,
    RelationEffectRuleAdmissionAssessment,
)
from abu_v60.mingli.calendar import ChartPillars
from mingli_relation_effect_test_support import (
    project_relation_effect_frontier,
    relation_effect_bundle,
)


def _admission_review(
    pillars: ChartPillars,
    *,
    reverse_facts: bool = False,
):
    bundle = relation_effect_bundle(
        pillars,
        reverse_facts=reverse_facts,
    )
    frontier = project_relation_effect_frontier(bundle)
    return (
        bundle,
        frontier,
        MingliRelationEffectAdmissionProjector().project(
            frontier=frontier,
        ),
    )


def test_relation_effect_admission_policy_registers_only_research_material() -> None:
    manifest = KnowledgeAuthority().relation_effect_rule_admission_manifest()
    policy = manifest["policy"]
    proposal = manifest["proposal"]

    assert policy["required_dimensions"] == list(RELATION_EFFECT_RULE_DIMENSIONS)
    assert policy["professionally_reviewed"] is False
    assert policy["effect_conclusion_allowed"] is False
    assert policy["source_usability_conclusion_allowed"] is False
    assert policy["admitted_effect_rule_profile_refs"] == []
    assert [item["dimension_id"] for item in proposal["dimension_submissions"]] == list(
        RELATION_EFFECT_RULE_DIMENSIONS
    )
    assert [item["status"] for item in proposal["dimension_submissions"]] == [
        "PARTIAL",
        "COMPETING",
        "MISSING",
        "MISSING",
        "MISSING",
        "MISSING",
    ]
    assert proposal["professional_source_manifest"] == []
    assert proposal["professionally_reviewed"] is False
    assert proposal["research_only"] is True
    assert manifest["admitted_effect_rule_profiles"] == []
    assert manifest["professional_rule_count"] == 0
    assert manifest["runtime_effect_authority"] == "NONE"


def test_relation_effect_admission_reviews_real_10_7_3_shape_stably() -> None:
    pillars = ChartPillars(
        year="己巳",
        month="丙子",
        day="丙寅",
        hour="甲午",
    )
    first_bundle, first_frontier, first = _admission_review(pillars)
    _, second_frontier, second = _admission_review(
        pillars,
        reverse_facts=True,
    )
    source_review = first_bundle["source_review"]

    assert first == second
    assert first_frontier == second_frontier
    assert first.review_version == RELATION_EFFECT_ADMISSION_REVIEW_VERSION
    assert source_review.source_evidence_count == 10
    assert source_review.clear_coordinate_count == 7
    assert source_review.review_required_count == 3
    assert first_frontier.demand_count == 3
    assert first.reviewed_demand_count == 1
    assert first.rejected_pre_admission_count == 1
    assert first.admitted_effect_rule_count == 0
    assert len(first.deferred_match_scope_demand_refs) == 2
    assert first.unreviewed_scope_invariant_demand_refs == ()
    assert first.frontier_scope_invariant_demand_refs == tuple(
        item.demand_ref
        for item in first_frontier.demands
        if item.dependency_status == "SCOPE_INVARIANT_RULE_DEMAND"
    )
    assert first.frontier_match_scope_demand_refs == tuple(
        item.demand_ref
        for item in first_frontier.demands
        if item.dependency_status == "MATCH_SCOPE_RULE_FIRST"
    )
    assert first.disposition == "REJECTED_PRE_ADMISSION"
    assert (first.reading_ref, first.reading_hash) == (
        first_frontier.reading_ref,
        first_frontier.reading_hash,
    )
    assert (first.frontier_ref, first.frontier_hash) == (
        first_frontier.frontier_ref,
        first_frontier.frontier_hash,
    )
    assert first.deferred_match_scope_demand_refs == tuple(
        item.demand_ref
        for item in first_frontier.demands
        if item.dependency_status == "MATCH_SCOPE_RULE_FIRST"
    )

    assessment = first.assessments[0]
    exact_demand = next(
        item
        for item in first_frontier.demands
        if item.dependency_status == "SCOPE_INVARIANT_RULE_DEMAND"
    )
    assert assessment.demand_ref == exact_demand.demand_ref
    assert (
        assessment.visible_slot,
        assessment.visible_stem,
        assessment.source_slot,
        assessment.source_branch,
        assessment.peer_slot,
        assessment.peer_branch,
    ) == ("year", "己", "hour", "午", "month", "子")
    assert [item.dimension_id for item in assessment.dimension_assessments] == list(
        RELATION_EFFECT_RULE_DIMENSIONS
    )
    assert [item.submission_status for item in assessment.dimension_assessments] == [
        "PARTIAL",
        "COMPETING",
        "MISSING",
        "MISSING",
        "MISSING",
        "MISSING",
    ]
    assert all(item.satisfied is False for item in assessment.dimension_assessments)
    assert [item.interpretation_id for item in assessment.interpretations] == [
        "RELATION_MEMBERSHIP_DISTURBANCE_ONLY",
        "SOURCE_OPEN_OR_EXPOSE",
        "SOURCE_DAMAGE_OR_REMOVE",
    ]
    assert all(
        item.status == "HELD" and item.selected is False and item.effect_atom_created is False
        for item in assessment.interpretations
    )
    assert assessment.admitted_effect_atom_refs == ()
    assert assessment.effect_status == "UNRESOLVED"
    assert assessment.usability_status == "UNRESOLVED"
    assert first.provider_invoked is False
    assert first.owner_professional_review_invoked is False
    assert first.knowledge_promotion_request_created is False
    assert first.gate_invoked is False
    assert first.decision_created is False
    assert first.selection_authority is False
    assert first.professional_verdict_allowed is False
    assert first.probability_claim_allowed is False
    assert first.canonical_write_allowed is False
    assert first.read_only is True


def test_relation_effect_admission_fails_closed_on_forged_authority() -> None:
    _, _, review = _admission_review(
        ChartPillars(
            year="己巳",
            month="丙子",
            day="丙寅",
            hour="甲午",
        )
    )
    assessment = review.assessments[0]

    forged_disposition = review.model_dump(mode="python")
    forged_disposition["disposition"] = "ADMITTED"
    with pytest.raises(ValueError, match="disposition"):
        MingliRelationEffectAdmissionReviewEnvelope.model_validate(forged_disposition)

    reordered_dimensions = assessment.model_dump(mode="python")
    reordered_dimensions["dimension_assessments"] = tuple(
        reversed(reordered_dimensions["dimension_assessments"])
    )
    with pytest.raises(
        ValueError,
        match="relation_effect_assessment_dimensions_invalid",
    ):
        RelationEffectRuleAdmissionAssessment.model_validate(reordered_dimensions)

    forged_effect = assessment.model_dump(mode="python")
    forged_effect["admitted_effect_atom_refs"] = ("effect-atom:automatic-source-damage",)
    with pytest.raises(
        ValueError,
        match="relation_effect_assessment_effect_atom_not_allowed",
    ):
        RelationEffectRuleAdmissionAssessment.model_validate(forged_effect)

    drifted_review = review.model_dump(mode="python")
    drifted_review["reading_hash"] = "f" * 64
    with pytest.raises(
        ValueError,
        match="relation_effect_review_hash_mismatch",
    ):
        MingliRelationEffectAdmissionReviewEnvelope.model_validate(drifted_review)


def test_relation_effect_admission_clear_case_is_not_triggered() -> None:
    pillars = ChartPillars(
        year="丁巳",
        month="乙巳",
        day="乙丑",
        hour="乙酉",
    )
    _, frontier, first = _admission_review(pillars)
    _, _, second = _admission_review(pillars)

    assert first == second
    assert frontier.demands == ()
    assert first.assessments == ()
    assert first.reviewed_demand_count == 0
    assert first.rejected_pre_admission_count == 0
    assert first.admitted_effect_rule_count == 0
    assert first.deferred_match_scope_demand_refs == ()
    assert first.unreviewed_scope_invariant_demand_refs == ()
    assert first.disposition == "NOT_TRIGGERED"
    assert first.effect_status == "UNRESOLVED"
    assert first.usability_status == "UNRESOLVED"
    assert first.decision_created is False
    assert first.canonical_write_allowed is False


def test_relation_effect_registry_revalidates_model_copy_identity() -> None:
    policy = bazi_relation_effect_admission_policy()
    stale_policy = policy.model_copy(
        update={
            "source_refs": (
                *policy.source_refs,
                "tamper:stale-policy-identity",
            )
        }
    )
    with pytest.raises(
        ValueError,
        match="relation_effect_admission_policy_hash_mismatch",
    ):
        KnowledgeAuthority(
            relation_effect_admission_policies=(stale_policy,),
        )

    proposal = bazi_zi_wu_automatic_damage_proposal()
    stale_proposal = proposal.model_copy(
        update={"claim": (f"{proposal.claim} tamper:stale-proposal-identity")}
    )
    with pytest.raises(
        ValueError,
        match="relation_effect_proposal_hash_mismatch",
    ):
        KnowledgeAuthority(
            relation_effect_rule_proposals=(stale_proposal,),
        )


def test_relation_effect_explicit_empty_registries_do_not_use_defaults() -> None:
    frontier = project_relation_effect_frontier(
        relation_effect_bundle(
            ChartPillars(
                year="己巳",
                month="丙子",
                day="丙寅",
                hour="甲午",
            )
        )
    )
    no_policy = KnowledgeAuthority(
        relation_effect_admission_policies=(),
    )
    with pytest.raises(
        KnowledgeAuthorityError,
        match="relation_effect_admission_policy_not_registered",
    ):
        no_policy.relation_effect_rule_admission_manifest()
    with pytest.raises(
        KnowledgeAuthorityError,
        match="relation_effect_admission_policy_not_registered",
    ):
        MingliRelationEffectAdmissionProjector(
            authority=no_policy,
        ).project(frontier=frontier)

    no_proposal = KnowledgeAuthority(
        relation_effect_rule_proposals=(),
    )
    with pytest.raises(
        KnowledgeAuthorityError,
        match="relation_effect_rule_proposal_not_registered",
    ):
        no_proposal.relation_effect_rule_admission_manifest()
    with pytest.raises(
        KnowledgeAuthorityError,
        match="relation_effect_rule_proposal_not_registered",
    ):
        MingliRelationEffectAdmissionProjector(
            authority=no_proposal,
        ).project(frontier=frontier)


def test_relation_effect_projector_requires_the_canonical_registered_proposal() -> None:
    canonical = bazi_zi_wu_automatic_damage_proposal()
    reissued = BaziRelationEffectRuleProposal.issue(
        claim=("这是结构合法但未经 canonical registry 选择的另一份研究提案。"),
        dimension_submissions=canonical.dimension_submissions,
    )
    authority = KnowledgeAuthority(
        relation_effect_rule_proposals=(reissued,),
    )
    frontier = project_relation_effect_frontier(
        relation_effect_bundle(
            ChartPillars(
                year="己巳",
                month="丙子",
                day="丙寅",
                hour="甲午",
            )
        )
    )

    assert reissued.proposal_ref != canonical.proposal_ref
    assert (
        authority.resolve_relation_effect_rule_proposal(
            proposal_ref=reissued.proposal_ref,
            proposal_version=reissued.proposal_version,
            expected_hash=reissued.proposal_hash,
        )
        == reissued
    )
    with pytest.raises(
        KnowledgeAuthorityError,
        match="relation_effect_rule_proposal_not_registered",
    ):
        MingliRelationEffectAdmissionProjector(
            authority=authority,
        ).project(frontier=frontier)


def test_relation_effect_review_inventory_fails_closed_on_partition_drift() -> None:
    _, frontier, review = _admission_review(
        ChartPillars(
            year="己巳",
            month="丙子",
            day="丙寅",
            hour="甲午",
        )
    )
    assert review.frontier_scope_invariant_demand_refs == tuple(
        item.demand_ref
        for item in frontier.demands
        if item.dependency_status == "SCOPE_INVARIANT_RULE_DEMAND"
    )
    assert review.frontier_match_scope_demand_refs == tuple(
        item.demand_ref
        for item in frontier.demands
        if item.dependency_status == "MATCH_SCOPE_RULE_FIRST"
    )
    assert len(review.frontier_match_scope_demand_refs) == 2

    overlap = review.model_dump(mode="python")
    overlap["frontier_match_scope_demand_refs"] = (
        review.frontier_scope_invariant_demand_refs[0],
        *review.frontier_match_scope_demand_refs,
    )
    with pytest.raises(
        ValueError,
        match="relation_effect_review_frontier_inventory_overlap",
    ):
        MingliRelationEffectAdmissionReviewEnvelope.model_validate(overlap)

    omitted = review.model_dump(mode="python")
    omitted["frontier_scope_invariant_demand_refs"] = ()
    with pytest.raises(
        ValueError,
        match="relation_effect_review_scope_inventory_not_covered",
    ):
        MingliRelationEffectAdmissionReviewEnvelope.model_validate(omitted)

    reordered = review.model_dump(mode="python")
    reordered["frontier_match_scope_demand_refs"] = tuple(
        reversed(review.frontier_match_scope_demand_refs)
    )
    with pytest.raises(
        ValueError,
        match="relation_effect_review_match_inventory_not_covered",
    ):
        MingliRelationEffectAdmissionReviewEnvelope.model_validate(reordered)

    original = review.assessments[0]
    duplicate_values = original.model_dump(
        mode="python",
        exclude={"assessment_ref", "assessment_hash"},
    )
    duplicate_values["proposal_claim"] = f"{original.proposal_claim} duplicate-demand-fixture"
    duplicate_demand = RelationEffectRuleAdmissionAssessment.issue(**duplicate_values)
    repeated = review.model_dump(mode="python")
    repeated["assessments"] = tuple(
        item.model_dump(mode="python")
        for item in sorted(
            (original, duplicate_demand),
            key=lambda item: item.assessment_ref,
        )
    )
    repeated["reviewed_demand_count"] = 2
    repeated["rejected_pre_admission_count"] = 2
    with pytest.raises(
        ValueError,
        match="relation_effect_review_assessed_demands_not_unique",
    ):
        MingliRelationEffectAdmissionReviewEnvelope.model_validate(repeated)


def test_relation_effect_verified_dimension_requires_evidence() -> None:
    with pytest.raises(
        ValueError,
        match="relation_effect_verified_dimension_evidence_required",
    ):
        RelationEffectProposalDimension(
            dimension_id="APPLICABILITY_CONTEXT",
            status="VERIFIED",
            statement="伪造为已验证，但没有任何证据引用。",
        )


def test_relation_effect_interpretations_use_the_actual_ding_source_identity() -> None:
    _, frontier, review = _admission_review(
        ChartPillars(
            year="丁巳",
            month="丙子",
            day="丙寅",
            hour="甲午",
        )
    )

    assert review.reviewed_demand_count == 1
    assessment = review.assessments[0]
    assert assessment.visible_stem == "丁"
    assert assessment.source_branch == "午"
    assert assessment.peer_branch == "子"
    assert assessment.demand_ref in {
        item.demand_ref
        for item in frontier.demands
        if item.dependency_status == "SCOPE_INVARIANT_RULE_DEMAND"
    }
    summaries = tuple(item.summary for item in assessment.interpretations)
    assert all("午中丁" in summary for summary in summaries)
    assert all("午中己" not in summary for summary in summaries)


def test_relation_effect_review_issuer_requires_all_target_demands() -> None:
    _, frontier, review = _admission_review(
        ChartPillars(
            year="己巳",
            month="丙子",
            day="丙寅",
            hour="甲午",
        )
    )

    assert review.reviewed_demand_count == 1
    with pytest.raises(
        ValueError,
        match=("relation_effect_review_target_demands_not_fully_assessed"),
    ):
        MingliRelationEffectAdmissionReviewEnvelope.issue(
            frontier=frontier,
            policy=bazi_relation_effect_admission_policy(),
            proposal=bazi_zi_wu_automatic_damage_proposal(),
            assessments=(),
        )


def test_relation_effect_review_issuer_rejects_resigned_proposal_drift() -> None:
    _, frontier, review = _admission_review(
        ChartPillars(
            year="己巳",
            month="丙子",
            day="丙寅",
            hour="甲午",
        )
    )
    policy = bazi_relation_effect_admission_policy()
    proposal = bazi_zi_wu_automatic_damage_proposal()
    assessment = review.assessments[0]

    claim_values = assessment.model_dump(
        mode="python",
        exclude={"assessment_ref", "assessment_hash"},
    )
    claim_values["proposal_claim"] = f"{assessment.proposal_claim} tamper:resigned-claim"
    resigned_claim = RelationEffectRuleAdmissionAssessment.issue(**claim_values)

    dimension_values = assessment.model_dump(
        mode="python",
        exclude={"assessment_ref", "assessment_hash"},
    )
    altered_dimension = assessment.dimension_assessments[0].model_copy(
        update={"submission_status": "UNSUPPORTED"}
    )
    dimension_values["dimension_assessments"] = (
        altered_dimension,
        *assessment.dimension_assessments[1:],
    )
    resigned_dimension = RelationEffectRuleAdmissionAssessment.issue(**dimension_values)

    for resigned in (resigned_claim, resigned_dimension):
        assert resigned.policy_ref == policy.policy_ref
        assert resigned.policy_hash == policy.policy_hash
        assert resigned.proposal_ref == proposal.proposal_ref
        assert resigned.proposal_hash == proposal.proposal_hash
        with pytest.raises(
            ValueError,
            match=("relation_effect_review_assessment_proposal_mismatch"),
        ):
            MingliRelationEffectAdmissionReviewEnvelope.issue(
                frontier=frontier,
                policy=policy,
                proposal=proposal,
                assessments=(resigned,),
            )
