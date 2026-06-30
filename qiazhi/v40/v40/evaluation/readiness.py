from __future__ import annotations

from collections import Counter

from v40.contracts.base import ReleaseRecommendation
from v40.contracts.evaluation import EvaluationBatchSummary, ReleaseReadinessSummary


def build_release_readiness_from_batches(
    *,
    readiness_id: str,
    candidate_version: str,
    batches: list[EvaluationBatchSummary],
) -> ReleaseReadinessSummary:
    reason_counts: Counter[str] = Counter()
    for batch in batches:
        reason_counts.update(batch.failed_reason_counts)
    batch_count = len(batches)
    approved_count = sum(1 for batch in batches if batch.recommendation == ReleaseRecommendation.APPROVE)
    rejected_count = sum(1 for batch in batches if batch.recommendation in {ReleaseRecommendation.REJECT, ReleaseRecommendation.ROLLBACK})
    review_count = batch_count - approved_count - rejected_count
    average = 0.0
    if batches:
        average = round(sum(batch.average_overall_score for batch in batches) / len(batches), 4)
    recommendation = ReleaseRecommendation.NEEDS_REVIEW
    if rejected_count:
        recommendation = ReleaseRecommendation.REJECT
    elif batch_count and approved_count == batch_count and average >= 0.82 and not reason_counts:
        recommendation = ReleaseRecommendation.APPROVE
    return ReleaseReadinessSummary(
        readiness_id=readiness_id,
        candidate_version=candidate_version,
        batch_count=batch_count,
        batch_ids=[batch.batch_id for batch in batches],
        approved_batch_count=approved_count,
        review_batch_count=review_count,
        rejected_batch_count=rejected_count,
        average_batch_score=average,
        failed_reason_counts=dict(sorted(reason_counts.items())),
        recommendation=recommendation,
    )
