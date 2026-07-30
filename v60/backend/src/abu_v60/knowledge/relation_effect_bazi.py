from __future__ import annotations

from functools import lru_cache
from typing import Final

from abu_v60.knowledge.relation_effect_contracts import (
    BaziRelationEffectAdmissionPolicy,
    BaziRelationEffectRuleProposal,
    RelationEffectProposalDimension,
)

RELATION_EFFECT_ADMISSION_POLICY_ID: Final = (
    "v60.relation-effect-admission-boundary.v1"
)
RELATION_EFFECT_RULE_PROPOSAL_ID: Final = (
    "v60.relation-effect-proposal.zi-wu-automatic-damage.v1"
)


@lru_cache(maxsize=1)
def bazi_relation_effect_admission_policy(
) -> BaziRelationEffectAdmissionPolicy:
    return BaziRelationEffectAdmissionPolicy.issue(
        source_refs=(
            "owner-boundary:structure-membership-is-not-relation-effect",
            "owner-decision:V60_RELATION_EFFECT_RULE_PREFLIGHT_V1",
        )
    )


@lru_cache(maxsize=1)
def bazi_zi_wu_automatic_damage_proposal(
) -> BaziRelationEffectRuleProposal:
    return BaziRelationEffectRuleProposal.issue(
        claim=(
            "子午六冲成员命中后，自动判定午中同干来源受损，"
            "并据此判定该来源不可用。"
        ),
        dimension_submissions=(
            RelationEffectProposalDimension(
                dimension_id="APPLICABILITY_CONTEXT",
                status="PARTIAL",
                statement=(
                    "已限定本命、严格同干、子午六冲与支藏来源；"
                    "尚未定义地支成员关系如何传播到藏干及明干载体。"
                ),
            ),
            RelationEffectProposalDimension(
                dimension_id="EFFECT_DIRECTION",
                status="COMPETING",
                statement=(
                    "只扰动支关系、打开或暴露来源、损伤或移除来源"
                    "仍是互相竞争且均未准入的解释。"
                ),
            ),
            RelationEffectProposalDimension(
                dimension_id="COMPLETION_CONDITIONS",
                status="MISSING",
            ),
            RelationEffectProposalDimension(
                dimension_id="BLOCKING_CONDITIONS",
                status="MISSING",
            ),
            RelationEffectProposalDimension(
                dimension_id="COUNTER_EVIDENCE",
                status="MISSING",
            ),
            RelationEffectProposalDimension(
                dimension_id="PROFESSIONAL_PROVENANCE",
                status="MISSING",
            ),
        ),
    )
