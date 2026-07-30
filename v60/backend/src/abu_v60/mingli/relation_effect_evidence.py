from __future__ import annotations

from abu_v60.knowledge.relation_effect_bazi import (
    bazi_relation_effect_admission_policy,
    bazi_zi_wu_automatic_damage_proposal,
)
from abu_v60.knowledge.relation_effect_contracts import (
    BaziRelationEffectAdmissionPolicy,
    BaziRelationEffectRuleProposal,
)
from abu_v60.knowledge.service import KnowledgeAuthority
from abu_v60.mingli.reading import MingliReadingEnvelope
from abu_v60.mingli.relation_effect_admission import (
    MingliRelationEffectAdmissionProjector,
)
from abu_v60.mingli.relation_effect_admission_contracts import (
    MingliRelationEffectAdmissionReviewEnvelope,
    RelationEffectRuleAdmissionAssessment,
)
from abu_v60.mingli.relation_effect_evidence_contracts import (
    MingliRelationEffectEvidencePacketEnvelope,
    RelationEffectDemandEvidencePacket,
    RelationEffectEvidenceDimensionSlot,
)
from abu_v60.mingli.relation_effect_frontier_contracts import (
    MingliRelationEffectResearchFrontierEnvelope,
    RelationEffectRuleDemand,
)


class MingliRelationEffectEvidencePacketProjector:
    """Project evidence intake readiness without invoking a decision path."""

    def __init__(
        self,
        *,
        authority: KnowledgeAuthority | None = None,
    ) -> None:
        self._authority = authority or KnowledgeAuthority()

    def project(
        self,
        *,
        reading: MingliReadingEnvelope,
        frontier: MingliRelationEffectResearchFrontierEnvelope,
        admission_review: MingliRelationEffectAdmissionReviewEnvelope,
    ) -> MingliRelationEffectEvidencePacketEnvelope:
        reading = MingliReadingEnvelope.model_validate(
            reading.model_dump(mode="python")
        )
        frontier = MingliRelationEffectResearchFrontierEnvelope.model_validate(
            frontier.model_dump(mode="python")
        )
        review = MingliRelationEffectAdmissionReviewEnvelope.model_validate(
            admission_review.model_dump(mode="python")
        )
        policy, proposal = self._resolve_canonical_authority()
        self._validate_lineage(
            reading=reading,
            frontier=frontier,
            review=review,
            policy=policy,
            proposal=proposal,
        )
        canonical_review = MingliRelationEffectAdmissionProjector(
            authority=self._authority
        ).project(frontier=frontier)
        if review != canonical_review:
            raise ValueError(
                "relation_effect_evidence_admission_review_not_canonical"
            )

        demands_by_ref = {
            item.demand_ref: item for item in frontier.demands
        }
        demand_packets = tuple(
            self._demand_packet(
                assessment=assessment,
                demand=self._required_demand(
                    demands_by_ref=demands_by_ref,
                    demand_ref=assessment.demand_ref,
                ),
                policy=policy,
                proposal=proposal,
            )
            for assessment in review.assessments
        )
        return MingliRelationEffectEvidencePacketEnvelope.issue(
            case_ref=reading.case_ref,
            chart_version_ref=reading.chart_version_ref,
            reading_ref=reading.reading_ref,
            reading_hash=reading.reading_hash,
            frontier_ref=frontier.frontier_ref,
            frontier_hash=frontier.frontier_hash,
            admission_review_ref=review.review_ref,
            admission_review_hash=review.review_hash,
            policy_ref=policy.policy_ref,
            policy_hash=policy.policy_hash,
            proposal_ref=proposal.proposal_ref,
            proposal_hash=proposal.proposal_hash,
            demand_packets=demand_packets,
        )

    def _resolve_canonical_authority(
        self,
    ) -> tuple[
        BaziRelationEffectAdmissionPolicy,
        BaziRelationEffectRuleProposal,
    ]:
        expected_policy = bazi_relation_effect_admission_policy()
        expected_proposal = bazi_zi_wu_automatic_damage_proposal()
        policy = self._authority.resolve_relation_effect_admission_policy(
            policy_ref=expected_policy.policy_ref,
            policy_version=expected_policy.policy_version,
            expected_hash=expected_policy.policy_hash,
        )
        proposal = self._authority.resolve_relation_effect_rule_proposal(
            proposal_ref=expected_proposal.proposal_ref,
            proposal_version=expected_proposal.proposal_version,
            expected_hash=expected_proposal.proposal_hash,
        )
        policy = BaziRelationEffectAdmissionPolicy.model_validate(
            policy.model_dump(mode="python")
        )
        proposal = BaziRelationEffectRuleProposal.model_validate(
            proposal.model_dump(mode="python")
        )
        if (
            policy != expected_policy
            or proposal != expected_proposal
        ):
            raise ValueError(
                "relation_effect_evidence_authority_not_canonical"
            )
        if (
            policy.professionally_reviewed
            or policy.admitted_effect_rule_profile_refs
            or proposal.professionally_reviewed
            or proposal.professional_source_manifest
            or proposal.owner_review_receipt_ref is not None
            or proposal.owner_review_receipt_hash is not None
            or any(
                item.evidence_refs
                for item in proposal.dimension_submissions
            )
        ):
            raise ValueError(
                "relation_effect_evidence_professional_material_not_admitted"
            )
        return policy, proposal

    @staticmethod
    def _validate_lineage(
        *,
        reading: MingliReadingEnvelope,
        frontier: MingliRelationEffectResearchFrontierEnvelope,
        review: MingliRelationEffectAdmissionReviewEnvelope,
        policy: BaziRelationEffectAdmissionPolicy,
        proposal: BaziRelationEffectRuleProposal,
    ) -> None:
        if (
            frontier.case_ref,
            frontier.chart_version_ref,
            frontier.reading_ref,
            frontier.reading_hash,
        ) != (
            reading.case_ref,
            reading.chart_version_ref,
            reading.reading_ref,
            reading.reading_hash,
        ):
            raise ValueError(
                "relation_effect_evidence_frontier_reading_mismatch"
            )
        if (
            frontier.source_review_vector_ref,
            frontier.source_review_vector_hash,
        ) != (
            reading.source_review_vector_ref,
            reading.source_review_vector_hash,
        ):
            raise ValueError(
                "relation_effect_evidence_source_review_reading_mismatch"
            )
        if (
            review.case_ref,
            review.chart_version_ref,
            review.reading_ref,
            review.reading_hash,
            review.frontier_ref,
            review.frontier_hash,
        ) != (
            reading.case_ref,
            reading.chart_version_ref,
            reading.reading_ref,
            reading.reading_hash,
            frontier.frontier_ref,
            frontier.frontier_hash,
        ):
            raise ValueError(
                "relation_effect_evidence_review_lineage_mismatch"
            )
        if (
            review.policy_ref,
            review.policy_hash,
            review.proposal_ref,
            review.proposal_hash,
        ) != (
            policy.policy_ref,
            policy.policy_hash,
            proposal.proposal_ref,
            proposal.proposal_hash,
        ):
            raise ValueError(
                "relation_effect_evidence_review_authority_mismatch"
            )

    @staticmethod
    def _required_demand(
        *,
        demands_by_ref: dict[str, RelationEffectRuleDemand],
        demand_ref: str,
    ) -> RelationEffectRuleDemand:
        demand = demands_by_ref.get(demand_ref)
        if demand is None:
            raise ValueError(
                "relation_effect_evidence_assessment_demand_missing"
            )
        return demand

    @staticmethod
    def _demand_packet(
        *,
        assessment: RelationEffectRuleAdmissionAssessment,
        demand: RelationEffectRuleDemand,
        policy: BaziRelationEffectAdmissionPolicy,
        proposal: BaziRelationEffectRuleProposal,
    ) -> RelationEffectDemandEvidencePacket:
        if _assessment_demand_identity(
            assessment
        ) != _frontier_demand_identity(demand):
            raise ValueError(
                "relation_effect_evidence_assessment_demand_mismatch"
            )
        submissions_by_dimension = {
            item.dimension_id: item
            for item in proposal.dimension_submissions
        }
        dimension_slots = tuple(
            RelationEffectEvidenceDimensionSlot.issue(
                dimension_id=item.dimension_id,
                proposal_submission_status=(
                    submissions_by_dimension[item.dimension_id].status
                ),
                current_basis_refs=item.current_basis_refs,
            )
            for item in assessment.dimension_assessments
        )
        return RelationEffectDemandEvidencePacket.issue(
            assessment_ref=assessment.assessment_ref,
            assessment_hash=assessment.assessment_hash,
            demand_ref=demand.demand_ref,
            source_review_ref=demand.source_review_ref,
            source_evidence_ref=demand.source_evidence_ref,
            intersection_ref=demand.intersection_ref,
            relation_fact_ref=demand.relation_fact_ref,
            carrier_ref=demand.carrier_ref,
            visible_slot=demand.visible_slot,
            visible_stem=demand.visible_stem,
            source_slot=demand.source_slot,
            source_branch=demand.source_branch,
            peer_slot=demand.peer_slot,
            peer_branch=demand.peer_branch,
            relation_type="six_clash_membership",
            source_match_kind="EXACT_IDENTITY",
            policy_ref=policy.policy_ref,
            policy_hash=policy.policy_hash,
            proposal_ref=proposal.proposal_ref,
            proposal_hash=proposal.proposal_hash,
            dimension_slots=dimension_slots,
        )


def _assessment_demand_identity(
    assessment: RelationEffectRuleAdmissionAssessment,
) -> tuple[object, ...]:
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
) -> tuple[object, ...]:
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
