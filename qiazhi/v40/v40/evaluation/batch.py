from __future__ import annotations

from collections import Counter

from v40.contracts.base import ReleaseRecommendation
from v40.contracts.evaluation import EvaluationBatchSummary, EvaluationCaseSpec, EvaluationRunResult, EvaluationStatus
from v40.contracts.runtime import RuntimeResult
from v40.evaluation.runner import evaluate_runtime_against_case


def evaluate_cases_against_runtime(
    *,
    batch_id: str,
    cases: list[EvaluationCaseSpec],
    runtime: RuntimeResult,
    candidate_version: str,
) -> tuple[list[EvaluationRunResult], EvaluationBatchSummary]:
    runs = [
        evaluate_runtime_against_case(
            run_id=f"{batch_id}:{case.case_id}",
            case_spec=case,
            runtime=runtime,
            candidate_version=candidate_version,
            build_release_gate=True,
        )
        for case in cases
    ]
    summary = build_evaluation_batch_summary(
        batch_id=batch_id,
        candidate_version=candidate_version,
        runs=runs,
    )
    return runs, summary


def build_evaluation_batch_summary(
    *,
    batch_id: str,
    candidate_version: str,
    runs: list[EvaluationRunResult],
) -> EvaluationBatchSummary:
    statuses = [run.status for run in runs]
    failed_reason_counts: Counter[str] = Counter()
    for run in runs:
        failed_reason_counts.update(run.metric_summary.failed_reasons)
    case_count = len(runs)
    average = 0.0
    if runs:
        average = round(sum(run.metric_summary.overall_score for run in runs) / len(runs), 4)
    blocked_count = statuses.count(EvaluationStatus.BLOCKED)
    review_count = statuses.count(EvaluationStatus.REVIEW)
    passed_count = statuses.count(EvaluationStatus.PASSED)
    recommendation = ReleaseRecommendation.NEEDS_REVIEW
    if blocked_count:
        recommendation = ReleaseRecommendation.REJECT
    elif case_count and passed_count == case_count:
        recommendation = ReleaseRecommendation.APPROVE
    return EvaluationBatchSummary(
        batch_id=batch_id,
        candidate_version=candidate_version,
        case_count=case_count,
        run_ids=[run.run_id for run in runs],
        passed_count=passed_count,
        review_count=review_count,
        blocked_count=blocked_count,
        average_overall_score=average,
        failed_reason_counts=dict(sorted(failed_reason_counts.items())),
        recommendation=recommendation,
    )
