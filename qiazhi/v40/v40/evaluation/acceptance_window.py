from __future__ import annotations

from collections import Counter

from v40.contracts.base import ReleaseRecommendation, Topic
from v40.contracts.evaluation import (
    AcceptanceWindowCaseResult,
    AcceptanceWindowResult,
    EvaluationRunResult,
    EvaluationStatus,
    RealCaseRecord,
)
from v40.contracts.output import ExpressionTelemetry
from v40.contracts.runtime import RuntimeResult
from v40.evaluation.runner import evaluate_runtime_against_case


def build_acceptance_window_from_runtime(
    *,
    window_id: str,
    cases: list[RealCaseRecord],
    runtime: RuntimeResult,
    candidate_version: str = "v40-alpha",
    expression_telemetry: ExpressionTelemetry | None = None,
) -> tuple[list[EvaluationRunResult], AcceptanceWindowResult]:
    runs: list[EvaluationRunResult] = []
    case_results: list[AcceptanceWindowCaseResult] = []
    for case in cases:
        run = evaluate_runtime_against_case(
            run_id=f"{window_id}:{case.case_id}",
            case_spec=case.to_evaluation_case(),
            runtime=runtime,
            candidate_version=candidate_version,
            build_release_gate=True,
            expression_telemetry=expression_telemetry,
        )
        runs.append(run)
        case_results.append(_case_result_from_run(case=case, run=run, runtime=runtime))
    return runs, _window_result(
        window_id=window_id,
        candidate_version=candidate_version,
        case_results=case_results,
    )


def _case_result_from_run(
    *,
    case: RealCaseRecord,
    run: EvaluationRunResult,
    runtime: RuntimeResult,
) -> AcceptanceWindowCaseResult:
    metric = run.metric_summary
    domain_score = _domain_coverage_score(case=case, runtime=runtime)
    expression_score = round(
        metric.expression_acceptance_rate
        * (1.0 - metric.llm_boundary_violation_rate)
        * (1.0 - metric.surface_leakage_rate),
        4,
    )
    probe_score = metric.probe_yield_score
    if not any(outcome.requires_probe for outcome in case.expected_outcomes):
        probe_score = 1.0
    scores = [
        metric.assertion_calibration_score,
        metric.advice_grounding_rate,
        1.0 - metric.overclaim_rate,
        domain_score,
        probe_score,
        expression_score,
    ]
    overall = round(sum(scores) / len(scores), 4)
    failed_reasons = list(metric.failed_reasons)
    failed_reasons.extend(_rubric_failures(case, metric, domain_score, probe_score, expression_score))
    failed_reasons = sorted(set(failed_reasons))
    status = _case_status(metric.status, overall, failed_reasons)
    return AcceptanceWindowCaseResult(
        case_id=case.case_id,
        run_id=run.run_id,
        reading_id=run.reading_id,
        verdict_match_score=metric.assertion_calibration_score,
        advice_grounding_score=metric.advice_grounding_rate,
        overclaim_rate=metric.overclaim_rate,
        domain_coverage_score=domain_score,
        probe_usefulness_score=probe_score,
        llm_expression_clarity_score=expression_score,
        overall_score=overall,
        status=status,
        failed_reasons=failed_reasons,
        trainable_attribution_hints=_trainable_hints(case, failed_reasons),
    )


def _window_result(
    *,
    window_id: str,
    candidate_version: str,
    case_results: list[AcceptanceWindowCaseResult],
) -> AcceptanceWindowResult:
    statuses = [result.status for result in case_results]
    failed_reason_counts: Counter[str] = Counter()
    for result in case_results:
        failed_reason_counts.update(result.failed_reasons)
    blocked_count = statuses.count(EvaluationStatus.BLOCKED)
    review_count = statuses.count(EvaluationStatus.REVIEW)
    passed_count = statuses.count(EvaluationStatus.PASSED)
    recommendation = ReleaseRecommendation.NEEDS_REVIEW
    if blocked_count:
        recommendation = ReleaseRecommendation.REJECT
    elif case_results and passed_count == len(case_results):
        recommendation = ReleaseRecommendation.APPROVE
    return AcceptanceWindowResult(
        window_id=window_id,
        candidate_version=candidate_version,
        case_count=len(case_results),
        case_results=case_results,
        run_ids=[result.run_id for result in case_results],
        passed_count=passed_count,
        review_count=review_count,
        blocked_count=blocked_count,
        average_verdict_match_score=_average([result.verdict_match_score for result in case_results]),
        average_advice_grounding_score=_average([result.advice_grounding_score for result in case_results]),
        average_overclaim_rate=_average([result.overclaim_rate for result in case_results]),
        average_domain_coverage_score=_average([result.domain_coverage_score for result in case_results]),
        average_probe_usefulness_score=_average([result.probe_usefulness_score for result in case_results]),
        average_llm_expression_clarity_score=_average(
            [result.llm_expression_clarity_score for result in case_results]
        ),
        average_overall_score=_average([result.overall_score for result in case_results]),
        failed_reason_counts=dict(sorted(failed_reason_counts.items())),
        recommendation=recommendation,
    )


def _domain_coverage_score(*, case: RealCaseRecord, runtime: RuntimeResult) -> float:
    expected = {outcome.topic for outcome in case.expected_outcomes if outcome.topic != Topic.UNKNOWN}
    if not expected:
        return 1.0
    actual = {verdict.topic for verdict in runtime.verdicts}
    if runtime.product_projection:
        actual.update(card.topic for card in runtime.product_projection.verdict_cards)
        actual.update(card.topic for card in runtime.product_projection.advice_cards)
    matched = sum(1 for topic in expected if topic in actual or topic == runtime.request.topic)
    return round(matched / max(1, len(expected)), 4)


def _rubric_failures(
    case: RealCaseRecord,
    metric,
    domain_score: float,
    probe_score: float,
    expression_score: float,
) -> list[str]:
    rubric = case.rubric
    failures: list[str] = []
    if metric.assertion_calibration_score < rubric.min_verdict_match_score:
        failures.append("real_case_verdict_match_low")
    if metric.advice_grounding_rate < rubric.min_advice_grounding_score:
        failures.append("real_case_advice_grounding_low")
    if metric.overclaim_rate > rubric.max_overclaim_rate:
        failures.append("real_case_overclaim_hit")
    if domain_score < rubric.min_domain_coverage_score:
        failures.append("real_case_domain_coverage_low")
    if probe_score < rubric.min_probe_usefulness_score:
        failures.append("real_case_probe_usefulness_low")
    if expression_score < rubric.min_llm_expression_clarity_score:
        failures.append("real_case_llm_expression_clarity_low")
    return failures


def _case_status(base_status: EvaluationStatus, overall: float, failed_reasons: list[str]) -> EvaluationStatus:
    if base_status == EvaluationStatus.BLOCKED or any("overclaim" in reason for reason in failed_reasons):
        return EvaluationStatus.BLOCKED
    if failed_reasons or overall < 0.78:
        return EvaluationStatus.REVIEW
    return EvaluationStatus.PASSED


def _trainable_hints(case: RealCaseRecord, failed_reasons: list[str]) -> list[str]:
    topics = sorted({outcome.topic.value for outcome in case.expected_outcomes})
    hints: list[str] = []
    if any("verdict" in reason or "assertion" in reason for reason in failed_reasons):
        hints.extend(f"domain_verdict_adapter:{topic}:claim_score" for topic in topics)
    if any("advice" in reason for reason in failed_reasons):
        hints.extend(f"advice_engine:{topic}:advice_priority" for topic in topics)
    if any("probe" in reason for reason in failed_reasons):
        hints.extend(f"hidden_factor_probe_engine:{topic}:probe_voi" for topic in topics)
    if any("expression" in reason or "llm" in reason for reason in failed_reasons):
        hints.append("llm_expression:style_policy")
    if any("domain" in reason for reason in failed_reasons):
        hints.extend(f"signal_registry:{topic}:source_weight" for topic in topics)
    return sorted(set(hints))


def _average(values: list[float]) -> float:
    if not values:
        return 0.0
    return round(sum(values) / len(values), 4)
