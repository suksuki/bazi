from __future__ import annotations

from v40.contracts.base import Topic
from v40.contracts.signal import RuntimeSignal
from v40.contracts.training import (
    LabelTargetType,
    TrainableUpdateScope,
    TrainingAttribution,
    TrainingExampleV2,
    TrainingLabelEvent,
)


def build_training_example_from_labels(
    *,
    example_id: str,
    reading_id: str,
    label_events: list[TrainingLabelEvent],
    topic: Topic = Topic.UNKNOWN,
    input_snapshot_ref: str = "",
    runtime_output_ref: str = "",
    local_overlay_refs: list[str] | None = None,
) -> TrainingExampleV2:
    target_ids: list[str] = []
    seen: set[str] = set()
    for event in label_events:
        for target_id in event.target_ids:
            if target_id not in seen:
                seen.add(target_id)
                target_ids.append(target_id)
        for target_id in event.affected_trainable_refs:
            if target_id not in seen:
                seen.add(target_id)
                target_ids.append(target_id)
    return TrainingExampleV2(
        example_id=example_id,
        reading_id=reading_id,
        topic=topic,
        input_snapshot_ref=input_snapshot_ref,
        runtime_output_ref=runtime_output_ref,
        label_events=label_events,
        attribution_targets=target_ids,
        expected_update={
            "scope": "local_overlay_first",
            "global_update_requires_release_gate": True,
            "local_overlay_refs": local_overlay_refs or [],
            "local_overlay_count": len(local_overlay_refs or []),
        },
    )


def build_training_attribution_from_label(
    *,
    attribution_id: str,
    label_event: TrainingLabelEvent,
    signals: list[RuntimeSignal] | None = None,
    update_scope: TrainableUpdateScope = TrainableUpdateScope.LOCAL_OVERLAY,
) -> TrainingAttribution:
    signal_rows = signals or []
    signal_by_id = {signal.signal_id: signal for signal in signal_rows}
    signal_by_claim = {signal.claim_key: signal for signal in signal_rows if signal.claim_key}
    affected_signal_ids: list[str] = []
    affected_trainable_refs: list[str] = list(label_event.affected_trainable_refs)
    affected_branch_ids: list[str] = []
    affected_verdict_ids: list[str] = []
    affected_advice_ids: list[str] = []
    affected_probe_ids: list[str] = []

    def add_unique(target: list[str], value: str) -> None:
        if value and value not in target:
            target.append(value)

    def add_signal(signal: RuntimeSignal) -> None:
        add_unique(affected_signal_ids, signal.signal_id)
        for ref in signal.trainable_refs or signal.trainable_targets:
            add_unique(affected_trainable_refs, ref)

    for target_id in label_event.target_ids + label_event.also_supports + label_event.weakens:
        if target_id in signal_by_id:
            add_signal(signal_by_id[target_id])
        if target_id in signal_by_claim:
            add_signal(signal_by_claim[target_id])

    if label_event.target_type == LabelTargetType.SIGNAL:
        for target_id in label_event.target_ids:
            add_unique(affected_signal_ids, target_id)
    elif label_event.target_type == LabelTargetType.CLAIM:
        for target_id in label_event.target_ids:
            add_unique(affected_trainable_refs, f"claim_score.{target_id}")
    elif label_event.target_type == LabelTargetType.BRANCH:
        for target_id in label_event.target_ids:
            add_unique(affected_branch_ids, target_id)
    elif label_event.target_type == LabelTargetType.VERDICT:
        for target_id in label_event.target_ids:
            add_unique(affected_verdict_ids, target_id)
    elif label_event.target_type == LabelTargetType.ADVICE:
        for target_id in label_event.target_ids:
            add_unique(affected_advice_ids, target_id)
            add_unique(affected_trainable_refs, f"advice_priority.{target_id}")
    elif label_event.target_type == LabelTargetType.PROBE:
        for target_id in label_event.target_ids:
            add_unique(affected_probe_ids, target_id)
            add_unique(affected_trainable_refs, f"probe_voi.{target_id}")
    elif label_event.target_type == LabelTargetType.HIDDEN_ATTRIBUTE:
        for target_id in label_event.target_ids:
            add_unique(affected_trainable_refs, f"hidden_attribute.{target_id}")
    elif label_event.target_type == LabelTargetType.LLM_OUTPUT:
        for target_id in label_event.target_ids:
            add_unique(affected_trainable_refs, f"llm_acceptance.{target_id}")
    elif label_event.target_type == LabelTargetType.TRAINABLE_UNIT:
        for target_id in label_event.target_ids:
            add_unique(affected_trainable_refs, target_id)

    return TrainingAttribution(
        attribution_id=attribution_id,
        label_event_id=label_event.event_id,
        affected_signal_ids=affected_signal_ids,
        affected_trainable_refs=affected_trainable_refs,
        affected_branch_ids=affected_branch_ids,
        affected_verdict_ids=affected_verdict_ids,
        affected_advice_ids=affected_advice_ids,
        affected_probe_ids=affected_probe_ids,
        attribution_confidence=label_event.confidence,
        update_scope=update_scope,
        release_gate_required=True,
    )
