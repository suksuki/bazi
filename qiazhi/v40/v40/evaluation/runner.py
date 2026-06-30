from __future__ import annotations

from v40.contracts.base import Topic
from v40.contracts.evaluation import (
    EvaluationCaseSpec,
    EvaluationRunResult,
    EvaluationStatus,
    MetricSummary,
)
from v40.contracts.output import AcceptanceStatus, ExpressionTelemetry
from v40.contracts.runtime import RuntimeResult
from v40.evaluation.release_gate import build_release_gate_from_metrics


def evaluate_runtime_against_case(
    *,
    run_id: str,
    case_spec: EvaluationCaseSpec,
    runtime: RuntimeResult,
    candidate_version: str = "",
    build_release_gate: bool = True,
    expression_telemetry: ExpressionTelemetry | None = None,
) -> EvaluationRunResult:
    metrics = build_metric_summary(case_spec=case_spec, runtime=runtime, expression_telemetry=expression_telemetry)
    release_gate = None
    if build_release_gate and candidate_version:
        release_gate = build_release_gate_from_metrics(
            metrics,
            gate_id=f"gate:{run_id}",
            candidate_version=candidate_version,
            regression_failures=metrics.failed_reasons,
        )
    return EvaluationRunResult(
        run_id=run_id,
        case_spec=case_spec,
        reading_id=runtime.reading_id,
        metric_summary=metrics,
        release_gate=release_gate,
        expression_telemetry=expression_telemetry,
        status=metrics.status,
    )


def build_metric_summary(
    *,
    case_spec: EvaluationCaseSpec,
    runtime: RuntimeResult,
    expression_telemetry: ExpressionTelemetry | None = None,
) -> MetricSummary:
    text_blob = _runtime_text_blob(runtime)
    evidence_score = _expected_signal_score(case_spec, runtime)
    assertion_score = _expected_verdict_score(case_spec, runtime, text_blob)
    overclaim_rate = _forbidden_assertion_rate(case_spec, text_blob)
    conflict_score = _conflict_score(case_spec, runtime)
    advice_score = _advice_score(case_spec, runtime, text_blob)
    probe_score = _probe_score(case_spec, runtime, text_blob)
    llm_violation_rate = 1.0 if any(verdict.llm_decision_authority for verdict in runtime.verdicts) else 0.0
    expression_acceptance_rate = _expression_acceptance_rate(expression_telemetry)
    expression_thinking_trace_rate = _expression_thinking_trace_rate(expression_telemetry)
    if _expression_boundary_failed(expression_telemetry):
        llm_violation_rate = 1.0
    leakage_rate = 0.0
    if runtime.product_projection and not runtime.product_projection.leakage_scan_passed:
        leakage_rate = 1.0
    scores = [
        evidence_score,
        assertion_score,
        conflict_score,
        advice_score,
        probe_score,
        1.0 - llm_violation_rate,
        expression_acceptance_rate,
        1.0 - leakage_rate,
        1.0 - overclaim_rate,
    ]
    overall = round(sum(scores) / len(scores), 4)
    failed_reasons = _failed_reasons(
        evidence_score=evidence_score,
        assertion_score=assertion_score,
        overclaim_rate=overclaim_rate,
        advice_score=advice_score,
        probe_score=probe_score,
        llm_violation_rate=llm_violation_rate,
        expression_acceptance_rate=expression_acceptance_rate,
        leakage_rate=leakage_rate,
    )
    if overclaim_rate or llm_violation_rate or leakage_rate:
        status = EvaluationStatus.BLOCKED
    elif overall >= 0.82:
        status = EvaluationStatus.PASSED
    else:
        status = EvaluationStatus.REVIEW
    return MetricSummary(
        case_id=case_spec.case_id,
        reading_id=runtime.reading_id,
        evidence_coverage_rate=evidence_score,
        overclaim_rate=overclaim_rate,
        assertion_calibration_score=assertion_score,
        conflict_resolution_score=conflict_score,
        advice_grounding_rate=advice_score,
        probe_yield_score=probe_score,
        llm_boundary_violation_rate=llm_violation_rate,
        expression_acceptance_rate=expression_acceptance_rate,
        expression_thinking_trace_rate=expression_thinking_trace_rate,
        surface_leakage_rate=leakage_rate,
        overall_score=overall,
        status=status,
        failed_reasons=failed_reasons,
    )


def _runtime_text_blob(runtime: RuntimeResult) -> str:
    chunks: list[str] = []
    for verdict in runtime.verdicts:
        chunks.append(verdict.headline)
        chunks.extend(verdict.allowed_assertions)
        chunks.extend(verdict.forbidden_assertions)
    for advice in runtime.advice_plans:
        chunks.extend(advice.action_points)
        chunks.extend(advice.avoid_points)
        chunks.extend(advice.condition_points)
    for probe in runtime.probes:
        chunks.append(probe.question)
    if runtime.product_projection:
        for card in runtime.product_projection.verdict_cards:
            chunks.extend([card.title, card.primary_text])
            chunks.extend(card.advice_points)
        for card in runtime.product_projection.advice_cards:
            chunks.append(card.title)
            chunks.extend(card.action_points)
            chunks.extend(card.avoid_points)
            chunks.extend(card.condition_points)
    return "\n".join(chunk for chunk in chunks if chunk)


def _expected_signal_score(case_spec: EvaluationCaseSpec, runtime: RuntimeResult) -> float:
    expected = case_spec.expected_signals
    if not expected:
        return 1.0 if runtime.signal_registry and runtime.signal_registry.signals else 0.6
    signals = runtime.signal_registry.signals if runtime.signal_registry else []
    matched = 0
    for item in expected:
        candidates = [signal for signal in signals if signal.topic == item.topic and signal.confidence >= item.min_confidence]
        if not item.claim_keywords:
            if candidates:
                matched += 1
            continue
        if any(all(keyword in signal.claim for keyword in item.claim_keywords) for signal in candidates):
            matched += 1
    required_count = max(1, sum(1 for item in expected if item.required))
    return _ratio(matched, required_count)


def _expected_verdict_score(case_spec: EvaluationCaseSpec, runtime: RuntimeResult, text_blob: str) -> float:
    expected = case_spec.expected_verdicts
    if not expected:
        return 1.0 if runtime.verdicts else 0.0
    matched = 0
    for item in expected:
        topic_verdicts = [verdict for verdict in runtime.verdicts if _topic_matches(verdict.topic, item.topic)]
        if not topic_verdicts:
            continue
        evidence_ok = any(len(verdict.evidence_refs) >= item.min_evidence_count for verdict in topic_verdicts)
        assertion_ok = any(verdict.assertion_level in item.allowed_assertion_levels for verdict in topic_verdicts)
        keywords_ok = True
        if item.expected_keywords:
            keywords_ok = any(keyword in text_blob for keyword in item.expected_keywords)
        if evidence_ok and assertion_ok and keywords_ok:
            matched += 1
    return _ratio(matched, len(expected))


def _forbidden_assertion_rate(case_spec: EvaluationCaseSpec, text_blob: str) -> float:
    forbidden = case_spec.forbidden_assertions
    if not forbidden:
        return 0.0
    hit_count = sum(1 for item in forbidden if item.text and item.text in text_blob)
    return _ratio(hit_count, len(forbidden))


def _conflict_score(case_spec: EvaluationCaseSpec, runtime: RuntimeResult) -> float:
    conflict_cases = [item for item in case_spec.expected_verdicts if item.requires_conflict_handling]
    if not conflict_cases:
        return 1.0
    handled = 0
    for item in conflict_cases:
        for verdict in runtime.verdicts:
            if not _topic_matches(verdict.topic, item.topic):
                continue
            if verdict.alternative_branch_ids or verdict.counter_evidence_refs or verdict.next_probe_ids:
                handled += 1
                break
    return _ratio(handled, len(conflict_cases))


def _advice_score(case_spec: EvaluationCaseSpec, runtime: RuntimeResult, text_blob: str) -> float:
    expected = case_spec.expected_advice
    if not expected:
        return 1.0 if runtime.advice_plans or (runtime.product_projection and runtime.product_projection.advice_cards) else 0.6
    matched = 0
    for item in expected:
        topic_advice = [advice for advice in runtime.advice_plans if _topic_matches(advice.topic, item.topic)]
        has_action = not item.requires_action or any(advice.action_points for advice in topic_advice)
        has_avoid = not item.requires_avoid or any(advice.avoid_points for advice in topic_advice)
        has_condition = not item.requires_condition or any(advice.condition_points for advice in topic_advice)
        has_keyword = not item.must_include_any or any(keyword in text_blob for keyword in item.must_include_any)
        if topic_advice and has_action and has_avoid and has_condition and has_keyword:
            matched += 1
    return _ratio(matched, len(expected))


def _probe_score(case_spec: EvaluationCaseSpec, runtime: RuntimeResult, text_blob: str) -> float:
    expected = [probe for probe in case_spec.expected_probes if probe.required]
    if not expected:
        return 1.0
    matched = 0
    for item in expected:
        topic_probes = [probe for probe in runtime.probes if _topic_matches(probe.topic, item.topic)]
        keyword_ok = not item.expected_keywords or any(keyword in text_blob for keyword in item.expected_keywords)
        target_ok = not item.target or any(item.target in probe.target_verdict_ids for probe in topic_probes)
        if topic_probes and keyword_ok and target_ok:
            matched += 1
    return _ratio(matched, len(expected))


def _failed_reasons(
    *,
    evidence_score: float,
    assertion_score: float,
    overclaim_rate: float,
    advice_score: float,
    probe_score: float,
    llm_violation_rate: float,
    expression_acceptance_rate: float,
    leakage_rate: float,
) -> list[str]:
    failures: list[str] = []
    if evidence_score < 0.8:
        failures.append("evidence_coverage_low")
    if assertion_score < 0.8:
        failures.append("assertion_calibration_low")
    if overclaim_rate > 0.0:
        failures.append("forbidden_assertion_hit")
    if advice_score < 0.8:
        failures.append("advice_grounding_low")
    if probe_score < 0.8:
        failures.append("probe_yield_low")
    if llm_violation_rate > 0.0:
        failures.append("llm_boundary_violation")
    if expression_acceptance_rate < 1.0:
        failures.append("expression_acceptance_not_accepted")
    if leakage_rate > 0.0:
        failures.append("surface_leakage")
    return failures


def _expression_acceptance_rate(telemetry: ExpressionTelemetry | None) -> float:
    if telemetry is None:
        return 1.0
    return 1.0 if telemetry.accepted and telemetry.acceptance_status == AcceptanceStatus.ACCEPTED else 0.0


def _expression_thinking_trace_rate(telemetry: ExpressionTelemetry | None) -> float:
    if telemetry is None or telemetry.execution_mode != "ollama":
        return 0.0
    return 1.0 if telemetry.thinking_trace_available and telemetry.thinking_trace_chars > 0 else 0.0


def _expression_boundary_failed(telemetry: ExpressionTelemetry | None) -> bool:
    if telemetry is None:
        return False
    return bool(
        telemetry.llm_decision_authority
        or telemetry.leakage_hits
        or telemetry.overclaim_hits
        or telemetry.chart_fact_mutation_detected
    )


def _topic_matches(actual: Topic, expected: Topic) -> bool:
    return expected == Topic.UNKNOWN or actual == expected


def _ratio(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 1.0
    return round(max(0.0, min(1.0, numerator / denominator)), 4)
