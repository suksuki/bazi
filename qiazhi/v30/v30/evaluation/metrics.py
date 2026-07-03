from __future__ import annotations

from v30.evaluation.contracts import AdviceEvalResult, MetricSummary, ProbeEvalResult, VerdictEvalResult


def build_metric_summary(
    *,
    verdict_eval: VerdictEvalResult,
    advice_eval: AdviceEvalResult,
    probe_eval: ProbeEvalResult,
) -> MetricSummary:
    failed = [
        *verdict_eval.failed_reasons,
        *advice_eval.failed_reasons,
        *probe_eval.failed_reasons,
    ]
    overall = round(
        verdict_eval.evidence_coverage_rate * 0.18
        + (1.0 - verdict_eval.overclaim_rate) * 0.18
        + verdict_eval.assertion_calibration_score * 0.16
        + verdict_eval.conflict_resolution_score * 0.1
        + advice_eval.advice_grounding_rate * 0.16
        + advice_eval.actionability_score * 0.1
        + probe_eval.probe_yield_score * 0.08
        + advice_eval.assertion_boundary_score * 0.04,
        3,
    )
    status = "passed" if not failed and overall >= 0.72 else "blocked"
    return MetricSummary(
        case_id=verdict_eval.case_id,
        reading_id=verdict_eval.reading_id,
        evidence_coverage_rate=verdict_eval.evidence_coverage_rate,
        overclaim_rate=verdict_eval.overclaim_rate,
        assertion_calibration_score=verdict_eval.assertion_calibration_score,
        advice_grounding_rate=advice_eval.advice_grounding_rate,
        probe_yield_score=probe_eval.probe_yield_score,
        llm_drift_rate=0.0,
        overall_score=overall,
        status=status,
        failed_reasons=failed,
    )
