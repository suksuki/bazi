from __future__ import annotations

from collections import defaultdict

from v40.contracts.base import ReleaseRecommendation, Topic
from v40.contracts.training import (
    BatchTrainerV1Result,
    LabelValue,
    ThresholdChange,
    TrainablePolicyRegistry,
    TrainableUnit,
    TrainableUnitType,
    TrainableUpdateScope,
    TrainingAttribution,
    TrainingImpactDiff,
    TrainingLabelEvent,
    WeightChange,
)


POSITIVE_LABELS = {
    LabelValue.SUPPORTS,
    LabelValue.MATCHES_REALITY,
    LabelValue.UNDERCLAIMED,
    LabelValue.GOOD_ADVICE,
    LabelValue.NEEDS_PROBE,
    LabelValue.PROBE_HELPFUL,
    LabelValue.EXPRESSION_GOOD,
}

NEGATIVE_LABELS = {
    LabelValue.WEAKENS,
    LabelValue.MISMATCH,
    LabelValue.OVERCLAIMED,
    LabelValue.BAD_ADVICE,
    LabelValue.PROBE_USELESS,
    LabelValue.EXPRESSION_BAD,
}


def build_batch_trainer_v1(
    *,
    training_run_id: str,
    base_registry: TrainablePolicyRegistry,
    attributions: list[TrainingAttribution],
    label_events: list[TrainingLabelEvent] | None = None,
    candidate_policy_version: str,
) -> BatchTrainerV1Result:
    if not training_run_id.strip():
        raise ValueError("BatchTrainerV1 requires training_run_id")
    if not candidate_policy_version.strip():
        raise ValueError("BatchTrainerV1 requires candidate_policy_version")
    if not attributions:
        raise ValueError("BatchTrainerV1 requires attributions")

    label_by_id = {event.event_id: event for event in label_events or []}
    deltas = _aggregate_deltas(attributions=attributions, label_by_id=label_by_id)
    base_units = {unit.unit_id: unit for unit in base_registry.units}
    candidate_units: list[TrainableUnit] = []
    changed_weights: list[WeightChange] = []
    changed_thresholds: list[ThresholdChange] = []
    changed_probe_policies: list[str] = []
    changed_advice_priorities: list[str] = []

    for unit_id in sorted(set(base_units) | set(deltas)):
        base_unit = base_units.get(unit_id) or _default_unit(unit_id=unit_id, policy_version=base_registry.active_policy_version)
        after = _clamp(base_unit.current_value + deltas.get(unit_id, 0.0), base_unit.min_value, base_unit.max_value)
        candidate_unit = base_unit.model_copy(
            update={
                "current_value": round(after, 4),
                "policy_version": candidate_policy_version,
                "update_scope": TrainableUpdateScope.CANDIDATE_POLICY,
            }
        )
        candidate_units.append(candidate_unit)
        if abs(candidate_unit.current_value - base_unit.current_value) < 0.0001:
            continue
        reason = "batch_trainer_v1_aggregated_training_attribution"
        if candidate_unit.unit_type == TrainableUnitType.ASSERTION_THRESHOLD:
            changed_thresholds.append(
                ThresholdChange(target_id=unit_id, before=base_unit.current_value, after=candidate_unit.current_value, reason=reason)
            )
        else:
            changed_weights.append(
                WeightChange(target_id=unit_id, before=base_unit.current_value, after=candidate_unit.current_value, reason=reason)
            )
        if candidate_unit.unit_type == TrainableUnitType.PROBE_VOI:
            changed_probe_policies.append(unit_id)
        if candidate_unit.unit_type == TrainableUnitType.ADVICE_PRIORITY:
            changed_advice_priorities.append(unit_id)

    candidate_registry = TrainablePolicyRegistry(
        registry_id=f"{base_registry.registry_id}:active:{candidate_policy_version}",
        active_policy_version=candidate_policy_version,
        candidate_policy_version=candidate_policy_version,
        active=True,
        previous_registry_id=base_registry.registry_id,
        previous_policy_version=base_registry.active_policy_version,
        activated_by_training_run_id=training_run_id,
        rollback_available=True,
        units=candidate_units,
        immutable_fact_modules=base_registry.immutable_fact_modules,
    )
    impact = TrainingImpactDiff(
        training_run_id=training_run_id,
        base_version=base_registry.active_policy_version,
        candidate_version=candidate_policy_version,
        changed_weights=changed_weights,
        changed_thresholds=changed_thresholds,
        changed_probe_policies=changed_probe_policies,
        changed_advice_priorities=changed_advice_priorities,
        affected_signals=_unique(item for attr in attributions for item in attr.affected_signal_ids),
        affected_branches=_unique(item for attr in attributions for item in attr.affected_branch_ids),
        affected_verdicts=_unique(item for attr in attributions for item in attr.affected_verdict_ids),
        affected_advice=_unique(item for attr in attributions for item in attr.affected_advice_ids),
        affected_probes=_unique(item for attr in attributions for item in attr.affected_probe_ids),
        improvement_summary=[
            "candidate_policy_registry_created",
            f"changed_unit_count:{len(changed_weights) + len(changed_thresholds)}",
        ],
        risk_summary=_risk_summary(label_events or []),
        release_recommendation=ReleaseRecommendation.NEEDS_REVIEW,
    )
    return BatchTrainerV1Result(
        training_run_id=training_run_id,
        base_policy_version=base_registry.active_policy_version,
        candidate_policy_version=candidate_policy_version,
        label_event_count=len(label_events or []),
        attribution_count=len(attributions),
        changed_unit_count=len(changed_weights) + len(changed_thresholds),
        candidate_registry=candidate_registry,
        impact_diff=impact,
        active_policy_applied=True,
        rollback_registry_id=base_registry.registry_id,
        previous_policy_version=base_registry.active_policy_version,
    )


def _aggregate_deltas(*, attributions: list[TrainingAttribution], label_by_id: dict[str, TrainingLabelEvent]) -> dict[str, float]:
    deltas: dict[str, float] = defaultdict(float)
    for attribution in attributions:
        event = label_by_id.get(attribution.label_event_id)
        direction = _label_direction(event.label if event else None)
        confidence = event.confidence if event else attribution.attribution_confidence
        scope_multiplier = 0.65 if event and event.local_only else 1.0
        delta = round(direction * max(confidence, attribution.attribution_confidence, 0.5) * 0.06 * scope_multiplier, 4)
        for ref in attribution.affected_trainable_refs:
            if _is_fact_ref(ref):
                continue
            deltas[ref] += delta
    return {key: _clamp(value, -0.12, 0.12) for key, value in deltas.items() if abs(value) >= 0.0001}


def _label_direction(label: LabelValue | None) -> float:
    if label in POSITIVE_LABELS:
        return 1.0
    if label in NEGATIVE_LABELS:
        return -1.0
    return 0.0


def _default_unit(*, unit_id: str, policy_version: str) -> TrainableUnit:
    unit_type = _unit_type(unit_id)
    return TrainableUnit(
        unit_id=unit_id,
        module=_module_for(unit_type),
        unit_type=unit_type,
        domain=_domain_for(unit_id),
        claim_key=_claim_key(unit_id),
        default_value=0.5,
        current_value=0.5,
        min_value=0.0,
        max_value=1.0,
        update_scope=TrainableUpdateScope.CANDIDATE_POLICY,
        policy_version=policy_version,
    )


def _unit_type(unit_id: str) -> TrainableUnitType:
    prefix = unit_id.split(".", 1)[0]
    mapping = {
        "source_weight": TrainableUnitType.SOURCE_WEIGHT,
        "signal_weight": TrainableUnitType.SOURCE_WEIGHT,
        "rule_weight": TrainableUnitType.RULE_WEIGHT,
        "path_weight": TrainableUnitType.PATH_WEIGHT,
        "claim_score": TrainableUnitType.CLAIM_SCORE,
        "hidden_attribute": TrainableUnitType.CLAIM_SCORE,
        "conflict_policy": TrainableUnitType.CONFLICT_POLICY,
        "assertion_threshold": TrainableUnitType.ASSERTION_THRESHOLD,
        "threshold": TrainableUnitType.ASSERTION_THRESHOLD,
        "advice_priority": TrainableUnitType.ADVICE_PRIORITY,
        "probe_voi": TrainableUnitType.PROBE_VOI,
        "probe_policy": TrainableUnitType.PROBE_VOI,
        "llm_acceptance": TrainableUnitType.LLM_ACCEPTANCE,
    }
    return mapping.get(prefix, TrainableUnitType.CLAIM_SCORE)


def _module_for(unit_type: TrainableUnitType) -> str:
    mapping = {
        TrainableUnitType.SOURCE_WEIGHT: "signal_registry",
        TrainableUnitType.RULE_WEIGHT: "rule_engine",
        TrainableUnitType.PATH_WEIGHT: "path_engine",
        TrainableUnitType.CLAIM_SCORE: "domain_verdict_adapter",
        TrainableUnitType.CONFLICT_POLICY: "decision_engine",
        TrainableUnitType.ASSERTION_THRESHOLD: "decision_engine",
        TrainableUnitType.ADVICE_PRIORITY: "advice_engine",
        TrainableUnitType.PROBE_VOI: "hidden_factor_probe_engine",
        TrainableUnitType.LLM_ACCEPTANCE: "llm_expression",
    }
    return mapping[unit_type]


def _domain_for(unit_id: str) -> Topic:
    for topic in Topic:
        if f".{topic.value}" in unit_id or unit_id.endswith(topic.value):
            return topic
    return Topic.UNKNOWN


def _claim_key(unit_id: str) -> str:
    return unit_id.split(".", 1)[1] if "." in unit_id else unit_id


def _is_fact_ref(ref: str) -> bool:
    lower = ref.lower()
    return lower.startswith("fact.") or "_fact" in lower or "chart_fact" in lower or "bazi_fact_engine" in lower


def _risk_summary(label_events: list[TrainingLabelEvent]) -> list[str]:
    risks = ["candidate_policy_requires_replay_release_gate"]
    if any(event.local_only for event in label_events):
        risks.append("local_feedback_downweighted_until_batch_validation")
    if any(not event.local_only and not event.requires_batch_review for event in label_events):
        risks.append("non_local_feedback_without_batch_review_detected")
    return risks


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _unique(values) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            result.append(value)
    return result
