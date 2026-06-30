from __future__ import annotations

from v40.contracts.base import ReleaseRecommendation, RoleKey
from v40.contracts.evaluation import ReleaseReadinessSummary
from v40.contracts.training import GlobalWeightVersion, WeightActivationReview


def build_weight_activation_review(
    *,
    review_id: str,
    weight_version: GlobalWeightVersion,
    release_readiness: ReleaseReadinessSummary,
    reviewed_by_role: RoleKey = "admin",
) -> WeightActivationReview:
    reasons: list[str] = []
    decision = ReleaseRecommendation.NEEDS_REVIEW
    if weight_version.active:
        reasons.append("weight_version_already_active")
        decision = ReleaseRecommendation.REJECT
    elif release_readiness.recommendation == ReleaseRecommendation.APPROVE:
        reasons.append("release_readiness_approved")
        decision = ReleaseRecommendation.APPROVE
    elif release_readiness.recommendation == ReleaseRecommendation.REJECT:
        reasons.append("release_readiness_rejected")
        decision = ReleaseRecommendation.REJECT
    else:
        reasons.append("release_readiness_needs_review")
    return WeightActivationReview(
        review_id=review_id,
        weight_version_id=weight_version.weight_version_id,
        release_readiness_id=release_readiness.readiness_id,
        reviewed_by_role=reviewed_by_role,
        decision=decision,
        reasons=reasons,
        activation_applied=False,
        production_write_allowed=False,
    )
