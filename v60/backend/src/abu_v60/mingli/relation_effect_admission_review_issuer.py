from __future__ import annotations

from typing import Any

from abu_v60.knowledge.relation_effect_bazi import (
    bazi_relation_effect_admission_policy,
    bazi_zi_wu_automatic_damage_proposal,
)
from abu_v60.knowledge.relation_effect_contracts import (
    BaziRelationEffectAdmissionPolicy,
    BaziRelationEffectRuleProposal,
)
from abu_v60.mingli.relation_effect_frontier_contracts import (
    MingliRelationEffectResearchFrontierEnvelope,
    RelationEffectRuleDemand,
)
from abu_v60.provenance import content_hash, stable_ref


def is_zi_wu_automatic_damage_target(
    demand: RelationEffectRuleDemand,
) -> bool:
    return (
        demand.dependency_status == "SCOPE_INVARIANT_RULE_DEMAND"
        and demand.source_match_kind == "EXACT_IDENTITY"
        and demand.relation_type == "six_clash_membership"
        and demand.source_branch == "午"
        and demand.peer_branch == "子"
    )


def issue_relation_effect_admission_review(
    *,
    model_cls: Any,
    frontier: MingliRelationEffectResearchFrontierEnvelope,
    policy: BaziRelationEffectAdmissionPolicy,
    proposal: BaziRelationEffectRuleProposal,
    assessments: tuple[Any, ...],
) -> Any:
    from abu_v60.mingli.relation_effect_admission_contracts import (
        RELATION_EFFECT_ADMISSION_REVIEW_VERSION,
        RelationEffectRuleAdmissionAssessment,
    )

    frontier = MingliRelationEffectResearchFrontierEnvelope.model_validate(
        frontier.model_dump(mode="python")
    )
    policy = BaziRelationEffectAdmissionPolicy.model_validate(
        policy.model_dump(mode="python")
    )
    proposal = BaziRelationEffectRuleProposal.model_validate(
        proposal.model_dump(mode="python")
    )
    canonical_policy = bazi_relation_effect_admission_policy()
    canonical_proposal = bazi_zi_wu_automatic_damage_proposal()
    if (
        policy.policy_ref,
        policy.policy_hash,
        policy.policy_version,
    ) != (
        canonical_policy.policy_ref,
        canonical_policy.policy_hash,
        canonical_policy.policy_version,
    ):
        raise ValueError(
            "relation_effect_review_policy_not_canonical"
        )
    if (
        proposal.proposal_ref,
        proposal.proposal_hash,
        proposal.proposal_version,
    ) != (
        canonical_proposal.proposal_ref,
        canonical_proposal.proposal_hash,
        canonical_proposal.proposal_version,
    ):
        raise ValueError(
            "relation_effect_review_proposal_not_canonical"
        )

    validated_assessments = tuple(
        RelationEffectRuleAdmissionAssessment.model_validate(
            item.model_dump(mode="python")
        )
        for item in assessments
    )
    demands_by_ref = {
        item.demand_ref: item for item in frontier.demands
    }
    if len(demands_by_ref) != len(frontier.demands):
        raise ValueError(
            "relation_effect_review_frontier_demands_not_unique"
        )
    target_demand_refs = tuple(
        item.demand_ref
        for item in frontier.demands
        if is_zi_wu_automatic_damage_target(item)
    )
    assessed_demand_refs = tuple(
        item.demand_ref for item in validated_assessments
    )
    if (
        len(assessed_demand_refs) != len(set(assessed_demand_refs))
        or set(assessed_demand_refs) != set(target_demand_refs)
    ):
        raise ValueError(
            "relation_effect_review_target_demands_not_fully_assessed"
        )
    proposal_dimensions = tuple(
        (item.dimension_id, item.status)
        for item in proposal.dimension_submissions
    )
    for assessment in validated_assessments:
        demand = demands_by_ref.get(assessment.demand_ref)
        assessment_dimensions = tuple(
            (item.dimension_id, item.submission_status)
            for item in assessment.dimension_assessments
        )
        if (
            assessment.policy_ref != policy.policy_ref
            or assessment.policy_hash != policy.policy_hash
            or assessment.proposal_ref != proposal.proposal_ref
            or assessment.proposal_hash != proposal.proposal_hash
            or assessment.proposal_claim != proposal.claim
            or assessment_dimensions != proposal_dimensions
        ):
            raise ValueError(
                "relation_effect_review_assessment_proposal_mismatch"
            )
        if demand is None or _assessment_demand_identity(
            assessment
        ) != _frontier_demand_identity(demand):
            raise ValueError(
                "relation_effect_review_assessment_demand_mismatch"
            )

    assessment_payloads = tuple(
        item.model_dump(mode="json")
        for item in validated_assessments
    )
    assessed_demand_set = set(assessed_demand_refs)
    scope_invariant_demand_refs = tuple(
        item.demand_ref
        for item in frontier.demands
        if item.dependency_status
        == "SCOPE_INVARIANT_RULE_DEMAND"
    )
    match_scope_demand_refs = tuple(
        item.demand_ref
        for item in frontier.demands
        if item.dependency_status == "MATCH_SCOPE_RULE_FIRST"
    )
    identity = {
        "review_version": RELATION_EFFECT_ADMISSION_REVIEW_VERSION,
        "case_ref": frontier.case_ref,
        "chart_version_ref": frontier.chart_version_ref,
        "reading_ref": frontier.reading_ref,
        "reading_hash": frontier.reading_hash,
        "frontier_ref": frontier.frontier_ref,
        "frontier_hash": frontier.frontier_hash,
        "frontier_scope_invariant_demand_refs": (
            scope_invariant_demand_refs
        ),
        "frontier_match_scope_demand_refs": match_scope_demand_refs,
        "policy_ref": policy.policy_ref,
        "policy_hash": policy.policy_hash,
        "proposal_ref": proposal.proposal_ref,
        "proposal_hash": proposal.proposal_hash,
        "assessments": assessment_payloads,
        "reviewed_demand_count": len(assessment_payloads),
        "rejected_pre_admission_count": len(assessment_payloads),
        "admitted_effect_rule_count": 0,
        "deferred_match_scope_demand_refs": match_scope_demand_refs,
        "unreviewed_scope_invariant_demand_refs": tuple(
            demand_ref
            for demand_ref in scope_invariant_demand_refs
            if demand_ref not in assessed_demand_set
        ),
        "disposition": (
            "REJECTED_PRE_ADMISSION"
            if assessment_payloads
            else "NOT_TRIGGERED"
        ),
        "review_semantics": (
            "SHORTCUT_ADMISSION_REJECTION_NOT_EFFECT_NEGATION"
        ),
        "effect_status": "UNRESOLVED",
        "usability_status": "UNRESOLVED",
        "provider_invoked": False,
        "owner_professional_review_invoked": False,
        "knowledge_promotion_request_created": False,
        "gate_invoked": False,
        "decision_created": False,
        "selection_authority": False,
        "professional_verdict_allowed": False,
        "probability_claim_allowed": False,
        "canonical_write_allowed": False,
        "read_only": True,
    }
    return model_cls(
        review_ref=stable_ref(
            "v60-relation-effect-admission-review",
            identity,
        ),
        review_hash=content_hash(identity),
        **identity,
    )


def _assessment_demand_identity(assessment: Any) -> tuple[Any, ...]:
    return (
        assessment.source_review_ref,
        assessment.source_evidence_ref,
        assessment.intersection_ref,
        assessment.relation_fact_ref,
        assessment.carrier_ref,
        assessment.visible_slot,
        assessment.visible_stem,
        assessment.source_slot,
        assessment.source_branch,
        assessment.peer_slot,
        assessment.peer_branch,
        assessment.relation_type,
        assessment.source_match_kind,
    )


def _frontier_demand_identity(
    demand: RelationEffectRuleDemand,
) -> tuple[Any, ...]:
    return (
        demand.source_review_ref,
        demand.source_evidence_ref,
        demand.intersection_ref,
        demand.relation_fact_ref,
        demand.carrier_ref,
        demand.visible_slot,
        demand.visible_stem,
        demand.source_slot,
        demand.source_branch,
        demand.peer_slot,
        demand.peer_branch,
        demand.relation_type,
        demand.source_match_kind,
    )
