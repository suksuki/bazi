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
from abu_v60.mingli.relation_effect_admission_contracts import (
    MingliRelationEffectAdmissionReviewEnvelope,
    RelationEffectCompetingInterpretation,
    RelationEffectDimensionAssessment,
    RelationEffectRuleAdmissionAssessment,
)
from abu_v60.mingli.relation_effect_admission_review_issuer import (
    is_zi_wu_automatic_damage_target,
)
from abu_v60.mingli.relation_effect_frontier_contracts import (
    RELATION_EFFECT_RESEARCH_FRONTIER_VERSION,
    MingliRelationEffectResearchFrontierEnvelope,
    RelationEffectRuleDemand,
)

_INTERPRETATION_TEMPLATES = (
    (
        "RELATION_MEMBERSHIP_DISTURBANCE_ONLY",
        "只确认子午属于六冲成员，不把成员关系自动传播成午中{identity}的作用。",
    ),
    (
        "SOURCE_OPEN_OR_EXPOSE",
        "冲可能被解释为打开或暴露午中{identity}；当前没有准入条件支持。",
    ),
    (
        "SOURCE_DAMAGE_OR_REMOVE",
        "冲可能被解释为损伤或移除午中{identity}；当前没有准入条件支持。",
    ),
)
_DIMENSION_GAPS = {
    "APPLICABILITY_CONTEXT": (
        "只有本盘坐标与严格同干来源；仍缺支关系向藏干、明干传播的"
        "适用谓词。"
    ),
    "EFFECT_DIRECTION": (
        "扰动、打开或暴露、损伤或移除仍是竞争解释，不能选择方向。"
    ),
    "COMPLETION_CONDITIONS": (
        "成员关系出现不等于作用完成；没有可执行的完成条件。"
    ),
    "BLOCKING_CONDITIONS": (
        "没有精确到该作用原子的合、会、距离、时令或其他阻断谓词。"
    ),
    "COUNTER_EVIDENCE": (
        "没有逐项对应本候选规则的反例证据类型与撤销条件。"
    ),
    "PROFESSIONAL_PROVENANCE": (
        "没有命题级来源清单、版本章节定位及专业审阅回执。"
    ),
}


class MingliRelationEffectAdmissionProjector:
    """Reject one concrete shortcut before it can become knowledge."""

    def __init__(
        self,
        *,
        authority: KnowledgeAuthority | None = None,
    ) -> None:
        self._authority = authority or KnowledgeAuthority()

    def project(
        self,
        *,
        frontier: MingliRelationEffectResearchFrontierEnvelope,
    ) -> MingliRelationEffectAdmissionReviewEnvelope:
        frontier = MingliRelationEffectResearchFrontierEnvelope.model_validate(
            frontier.model_dump(mode="python")
        )
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
        if (
            frontier.frontier_version
            != RELATION_EFFECT_RESEARCH_FRONTIER_VERSION
        ):
            raise ValueError(
                "relation_effect_admission_frontier_version_not_supported"
            )
        self._validate_policy_and_proposal(
            policy=policy,
            proposal=proposal,
        )

        eligible = tuple(
            demand
            for demand in frontier.demands
            if is_zi_wu_automatic_damage_target(demand)
        )
        assessments = tuple(
            sorted(
                (
                    self._assessment(
                        demand=demand,
                        frontier=frontier,
                        policy=policy,
                        proposal=proposal,
                    )
                    for demand in eligible
                ),
                key=lambda item: item.assessment_ref,
            )
        )
        return MingliRelationEffectAdmissionReviewEnvelope.issue(
            frontier=frontier,
            policy=policy,
            proposal=proposal,
            assessments=assessments,
        )

    @staticmethod
    def _validate_policy_and_proposal(
        *,
        policy: BaziRelationEffectAdmissionPolicy,
        proposal: BaziRelationEffectRuleProposal,
    ) -> None:
        if (
            policy.professionally_reviewed
            or policy.effect_conclusion_allowed
            or policy.source_usability_conclusion_allowed
            or policy.admitted_effect_rule_profile_refs
        ):
            raise ValueError(
                "relation_effect_admission_policy_authority_invalid"
            )
        if (
            proposal.professionally_reviewed
            or proposal.professional_source_manifest
            or proposal.owner_review_receipt_ref is not None
            or proposal.owner_review_receipt_hash is not None
            or all(
                item.status == "VERIFIED"
                for item in proposal.dimension_submissions
            )
        ):
            raise ValueError(
                "relation_effect_admission_proposal_must_remain_unadmitted"
            )

    @classmethod
    def _assessment(
        cls,
        *,
        demand: RelationEffectRuleDemand,
        frontier: MingliRelationEffectResearchFrontierEnvelope,
        policy: BaziRelationEffectAdmissionPolicy,
        proposal: BaziRelationEffectRuleProposal,
    ) -> RelationEffectRuleAdmissionAssessment:
        basis_by_dimension = {
            "APPLICABILITY_CONTEXT": (
                demand.source_evidence_ref,
                demand.relation_fact_ref,
                demand.intersection_ref,
            ),
            "EFFECT_DIRECTION": (
                demand.relation_fact_ref,
                proposal.proposal_ref,
            ),
            "COMPLETION_CONDITIONS": (),
            "BLOCKING_CONDITIONS": (
                frontier.prerequisite_ref,
                frontier.refusal_receipt_ref,
            ),
            "COUNTER_EVIDENCE": (
                frontier.source_review_vector_ref,
                frontier.refusal_receipt_ref,
            ),
            "PROFESSIONAL_PROVENANCE": (
                policy.policy_ref,
                proposal.proposal_ref,
            ),
        }
        dimensions = tuple(
            RelationEffectDimensionAssessment(
                dimension_id=submission.dimension_id,
                submission_status=submission.status,
                current_basis_refs=basis_by_dimension[
                    submission.dimension_id
                ],
                gap=_DIMENSION_GAPS[submission.dimension_id],
                satisfied=False,
            )
            for submission in proposal.dimension_submissions
        )
        interpretations = tuple(
            RelationEffectCompetingInterpretation.issue(
                interpretation_id=interpretation_id,
                summary=summary,
            )
            for interpretation_id, summary_template in (
                _INTERPRETATION_TEMPLATES
            )
            for summary in (
                summary_template.format(identity=demand.visible_stem),
            )
        )
        return RelationEffectRuleAdmissionAssessment.issue(
            demand_ref=demand.demand_ref,
            source_review_ref=demand.source_review_ref,
            source_evidence_ref=demand.source_evidence_ref,
            intersection_ref=demand.intersection_ref,
            relation_fact_ref=demand.relation_fact_ref,
            carrier_ref=demand.carrier_ref,
            visible_slot=demand.visible_slot,
            visible_stem=demand.visible_stem,
            source_slot=demand.source_slot,
            source_branch="午",
            peer_slot=demand.peer_slot,
            peer_branch="子",
            relation_type="six_clash_membership",
            source_match_kind="EXACT_IDENTITY",
            policy_ref=policy.policy_ref,
            policy_hash=policy.policy_hash,
            proposal_ref=proposal.proposal_ref,
            proposal_hash=proposal.proposal_hash,
            proposal_claim=proposal.claim,
            interpretations=interpretations,
            dimension_assessments=dimensions,
        )
