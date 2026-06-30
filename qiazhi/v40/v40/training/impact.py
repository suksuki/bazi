from __future__ import annotations

from v40.contracts.base import ReleaseRecommendation
from v40.contracts.evaluation import EvaluationRunResult, EvaluationStatus
from v40.contracts.training import TrainingImpactDiff


def build_training_impact_from_evaluation(
    *,
    evaluation_run: EvaluationRunResult,
    training_run_id: str,
    base_version: str,
    candidate_version: str,
) -> TrainingImpactDiff:
    metrics = evaluation_run.metric_summary
    expected_topics = sorted({item.topic.value for item in evaluation_run.case_spec.expected_verdicts})
    recommendation = ReleaseRecommendation.NEEDS_REVIEW
    if evaluation_run.status == EvaluationStatus.BLOCKED:
        recommendation = ReleaseRecommendation.REJECT
    elif evaluation_run.release_gate:
        recommendation = evaluation_run.release_gate.recommendation
    return TrainingImpactDiff(
        training_run_id=training_run_id,
        base_version=base_version,
        candidate_version=candidate_version,
        affected_verdicts=[f"topic:{topic}" for topic in expected_topics],
        golden_case_diff={
            "case_id": evaluation_run.case_spec.case_id,
            "overall_score": metrics.overall_score,
            "status": metrics.status.value,
            "failed_reasons": metrics.failed_reasons,
        },
        regression_failures=metrics.failed_reasons,
        improvement_summary=_improvement_summary(evaluation_run),
        risk_summary=_risk_summary(evaluation_run),
        release_recommendation=recommendation,
    )


def _improvement_summary(evaluation_run: EvaluationRunResult) -> list[str]:
    metrics = evaluation_run.metric_summary
    summary: list[str] = []
    if metrics.evidence_coverage_rate >= 0.8:
        summary.append("evidence_coverage_ready")
    if metrics.assertion_calibration_score >= 0.8:
        summary.append("assertion_calibration_ready")
    if metrics.advice_grounding_rate >= 0.8:
        summary.append("advice_grounding_ready")
    if not summary:
        summary.append("no_clear_improvement_detected")
    return summary


def _risk_summary(evaluation_run: EvaluationRunResult) -> list[str]:
    metrics = evaluation_run.metric_summary
    risks = list(metrics.failed_reasons)
    if metrics.overall_score < 0.82 and "overall_score_below_release_threshold" not in risks:
        risks.append("overall_score_below_release_threshold")
    return risks
