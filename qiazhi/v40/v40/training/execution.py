from __future__ import annotations

from v40.contracts.training import GlobalWeightVersion, WeightActivationExecution, WeightActivationReview


def build_weight_activation_execution(
    *,
    execution_id: str,
    review: WeightActivationReview,
    weight_version: GlobalWeightVersion,
    rollback_version_id: str,
    deactivated_weight_ids: list[str] | None = None,
) -> WeightActivationExecution:
    return WeightActivationExecution(
        execution_id=execution_id,
        review_id=review.review_id,
        weight_version_id=weight_version.weight_version_id,
        release_readiness_id=review.release_readiness_id,
        rollback_version_id=rollback_version_id,
        executed_by_role="admin",
        review_decision=review.decision,
        deactivated_weight_ids=deactivated_weight_ids or [],
        activation_applied=True,
        v40_weight_write_applied=True,
        v30_state_mutated=False,
        chart_fact_mutation_allowed=False,
    )
