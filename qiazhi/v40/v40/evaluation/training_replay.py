from __future__ import annotations

from v40.contracts.base import ReleaseRecommendation
from v40.contracts.evaluation import EvaluationStatus, TrainingExampleReplayResult
from v40.contracts.runtime import RuntimeResult
from v40.contracts.training import LabelValue, TrainingExampleV2


POSITIVE_LABELS = {
    LabelValue.SUPPORTS,
    LabelValue.MATCHES_REALITY,
    LabelValue.GOOD_ADVICE,
    LabelValue.PROBE_HELPFUL,
    LabelValue.EXPRESSION_GOOD,
}
NEGATIVE_LABELS = {
    LabelValue.WEAKENS,
    LabelValue.MISMATCH,
    LabelValue.OVERCLAIMED,
    LabelValue.UNDERCLAIMED,
    LabelValue.BAD_ADVICE,
    LabelValue.PROBE_USELESS,
    LabelValue.EXPRESSION_BAD,
}


def replay_training_example(
    *,
    replay_id: str,
    training_example: TrainingExampleV2,
    runtime: RuntimeResult,
    candidate_version: str = "v40-alpha",
    include_source_example: bool = True,
) -> TrainingExampleReplayResult:
    runtime_targets = _runtime_target_ids(runtime)
    example_targets = _example_target_ids(training_example)
    matched = [target_id for target_id in example_targets if target_id in runtime_targets]
    missing = [target_id for target_id in example_targets if target_id not in runtime_targets]
    target_coverage = _ratio(len(matched), len(example_targets))
    positive_count = sum(1 for event in training_example.label_events if event.label in POSITIVE_LABELS)
    negative_count = sum(1 for event in training_example.label_events if event.label in NEGATIVE_LABELS)
    needs_probe_count = sum(1 for event in training_example.label_events if event.label == LabelValue.NEEDS_PROBE)
    overlay_refs = _overlay_refs(training_example)
    failed_reasons = _failed_reasons(
        training_example=training_example,
        target_coverage=target_coverage,
        example_targets=example_targets,
    )
    score = _alignment_score(
        target_coverage=target_coverage,
        has_labels=bool(training_example.label_events),
        has_overlay_or_target=bool(overlay_refs or example_targets),
        safe_boundaries=not (training_example.global_update_allowed or training_example.chart_fact_mutation_allowed),
    )
    if training_example.global_update_allowed or training_example.chart_fact_mutation_allowed or not training_example.label_events:
        status = EvaluationStatus.BLOCKED
    elif score >= 0.78 and target_coverage >= 0.7:
        status = EvaluationStatus.PASSED
    else:
        status = EvaluationStatus.REVIEW
    recommendation = ReleaseRecommendation.NEEDS_REVIEW
    if status == EvaluationStatus.PASSED:
        recommendation = ReleaseRecommendation.APPROVE
    elif status == EvaluationStatus.BLOCKED:
        recommendation = ReleaseRecommendation.REJECT
    return TrainingExampleReplayResult(
        replay_id=replay_id,
        example_id=training_example.example_id,
        reading_id=training_example.reading_id,
        candidate_version=candidate_version,
        target_count=len(example_targets),
        matched_target_ids=matched,
        missing_target_ids=missing,
        target_coverage_rate=target_coverage,
        local_overlay_ref_count=len(overlay_refs),
        positive_label_count=positive_count,
        negative_label_count=negative_count,
        needs_probe_count=needs_probe_count,
        feedback_alignment_score=score,
        status=status,
        failed_reasons=failed_reasons,
        recommendation=recommendation,
        production_write_allowed=False,
        chart_fact_mutation_allowed=False,
        source_example=training_example if include_source_example else None,
    )


def _runtime_target_ids(runtime: RuntimeResult) -> set[str]:
    targets: set[str] = {runtime.reading_id}
    if runtime.signal_registry:
        for signal in runtime.signal_registry.signals:
            targets.add(signal.signal_id)
            targets.update(signal.trainable_targets)
            targets.update(signal.evidence_refs)
    if runtime.decision_input:
        targets.add(runtime.decision_input.bundle_id)
        targets.update(runtime.decision_input.signal_ids)
        targets.update(runtime.decision_input.local_overlay_ids)
    if runtime.engine_result:
        targets.add(runtime.engine_result.reading_id)
        targets.add(runtime.engine_result.plan.plan_id)
        for result in runtime.engine_result.results:
            targets.add(result.result_id)
            for signal in result.signals:
                targets.add(signal.signal_id)
            for probe in result.probe_candidates:
                targets.add(str(probe.get("probe_id", "")))
    for branch in runtime.branches:
        targets.add(branch.branch_id)
        targets.update(branch.evidence_refs)
        targets.update(branch.counter_evidence_refs)
    for verdict in runtime.verdicts:
        targets.add(verdict.verdict_id)
        if verdict.primary_branch_id:
            targets.add(verdict.primary_branch_id)
        targets.update(verdict.alternative_branch_ids)
        targets.update(verdict.evidence_refs)
        targets.update(verdict.counter_evidence_refs)
        targets.update(verdict.next_probe_ids)
    for advice in runtime.advice_plans:
        targets.add(advice.advice_id)
        targets.update(advice.source_verdict_ids)
        targets.update(advice.evidence_refs)
    for probe in runtime.probes:
        targets.add(probe.probe_id)
        targets.update(probe.target_branch_ids)
        targets.update(probe.target_verdict_ids)
    if runtime.product_projection:
        for card in runtime.product_projection.verdict_cards:
            targets.add(card.card_id)
            targets.add(card.source_verdict_id)
        for card in runtime.product_projection.branch_cards:
            targets.add(card.card_id)
            if card.source_branch_id:
                targets.add(card.source_branch_id)
        for card in runtime.product_projection.advice_cards:
            targets.add(card.card_id)
            targets.add(card.source_advice_id)
    if runtime.expression_task:
        targets.add(runtime.expression_task.task_id)
        targets.update(runtime.expression_task.input_card_ids)
    if runtime.expression_result:
        targets.add(runtime.expression_result.result_id)
    if runtime.acceptance_result:
        targets.add(runtime.acceptance_result.result_id)
    for seed in runtime.conversation_seeds:
        targets.add(seed.seed_id)
        targets.update(seed.source_probe_ids)
        targets.update(seed.source_verdict_ids)
        targets.update(seed.source_advice_ids)
    return {target for target in targets if target}


def _example_target_ids(training_example: TrainingExampleV2) -> list[str]:
    ordered: list[str] = []
    seen: set[str] = set()
    for target_id in training_example.attribution_targets:
        if target_id and target_id not in seen:
            seen.add(target_id)
            ordered.append(target_id)
    for event in training_example.label_events:
        for target_id in event.target_ids:
            if target_id and target_id not in seen:
                seen.add(target_id)
                ordered.append(target_id)
    return ordered


def _overlay_refs(training_example: TrainingExampleV2) -> list[str]:
    raw = training_example.expected_update.get("local_overlay_refs", [])
    if isinstance(raw, list):
        return [str(item) for item in raw if str(item).strip()]
    return []


def _alignment_score(
    *,
    target_coverage: float,
    has_labels: bool,
    has_overlay_or_target: bool,
    safe_boundaries: bool,
) -> float:
    parts = [
        target_coverage * 0.55,
        (1.0 if has_labels else 0.0) * 0.2,
        (1.0 if has_overlay_or_target else 0.0) * 0.1,
        (1.0 if safe_boundaries else 0.0) * 0.15,
    ]
    return round(sum(parts), 4)


def _failed_reasons(
    *,
    training_example: TrainingExampleV2,
    target_coverage: float,
    example_targets: list[str],
) -> list[str]:
    failures: list[str] = []
    if not training_example.label_events:
        failures.append("training_example_has_no_labels")
    if not example_targets:
        failures.append("training_example_has_no_targets")
    if target_coverage < 0.7:
        failures.append("training_target_coverage_low")
    if training_example.global_update_allowed:
        failures.append("training_example_requests_global_update")
    if training_example.chart_fact_mutation_allowed:
        failures.append("training_example_requests_chart_fact_mutation")
    return failures


def _ratio(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return round(max(0.0, min(1.0, numerator / denominator)), 4)
