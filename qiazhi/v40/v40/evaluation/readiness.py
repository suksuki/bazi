from __future__ import annotations

from collections import Counter

from v40.contracts.base import ReleaseRecommendation
from v40.contracts.evaluation import EvaluationBatchSummary, ReleaseReadinessSummary, TrainingReplayBatchSummary


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


def build_release_readiness_from_evidence_batches(
    *,
    readiness_id: str,
    candidate_version: str,
    evaluation_batches: list[EvaluationBatchSummary],
    replay_batches: list[TrainingReplayBatchSummary],
) -> ReleaseReadinessSummary:
    reason_counts: Counter[str] = Counter()
    for batch in evaluation_batches:
        reason_counts.update({f"evaluation:{key}": value for key, value in batch.failed_reason_counts.items()})
    for batch in replay_batches:
        reason_counts.update({f"replay:{key}": value for key, value in batch.failed_reason_counts.items()})
    if not evaluation_batches:
        reason_counts["missing_evaluation_batch"] += 1
    if not replay_batches:
        reason_counts["missing_replay_batch"] += 1

    batch_ids = [f"evaluation:{batch.batch_id}" for batch in evaluation_batches]
    batch_ids.extend(f"replay:{batch.batch_id}" for batch in replay_batches)
    batch_count = len(batch_ids)
    all_recommendations = [batch.recommendation for batch in evaluation_batches]
    all_recommendations.extend(batch.recommendation for batch in replay_batches)

    approved_count = sum(1 for recommendation in all_recommendations if recommendation == ReleaseRecommendation.APPROVE)
    rejected_count = sum(
        1 for recommendation in all_recommendations if recommendation in {ReleaseRecommendation.REJECT, ReleaseRecommendation.ROLLBACK}
    )
    review_count = batch_count - approved_count - rejected_count
    scores = [batch.average_overall_score for batch in evaluation_batches]
    scores.extend(_replay_batch_score(batch) for batch in replay_batches)
    average = round(sum(scores) / len(scores), 4) if scores else 0.0

    recommendation = ReleaseRecommendation.NEEDS_REVIEW
    if rejected_count:
        recommendation = ReleaseRecommendation.REJECT
    elif (
        evaluation_batches
        and replay_batches
        and batch_count
        and approved_count == batch_count
        and average >= 0.82
        and not reason_counts
    ):
        recommendation = ReleaseRecommendation.APPROVE

    return ReleaseReadinessSummary(
        readiness_id=readiness_id,
        candidate_version=candidate_version,
        batch_count=batch_count,
        batch_ids=batch_ids,
        approved_batch_count=approved_count,
        review_batch_count=review_count,
        rejected_batch_count=rejected_count,
        average_batch_score=average,
        failed_reason_counts=dict(sorted(reason_counts.items())),
        recommendation=recommendation,
        boundary="release_readiness_summary_aggregates_evaluation_and_replay_batches_without_activation",
    )


def _replay_batch_score(batch: TrainingReplayBatchSummary) -> float:
    return round((batch.average_feedback_alignment_score + batch.average_target_coverage_rate) / 2, 4)
