from __future__ import annotations

from v40.contracts.base import Topic
from v40.contracts.training import TrainingExampleV2, TrainingLabelEvent


def build_training_example_from_labels(
    *,
    example_id: str,
    reading_id: str,
    label_events: list[TrainingLabelEvent],
    topic: Topic = Topic.UNKNOWN,
    input_snapshot_ref: str = "",
    runtime_output_ref: str = "",
) -> TrainingExampleV2:
    target_ids: list[str] = []
    seen: set[str] = set()
    for event in label_events:
        for target_id in event.target_ids:
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
        },
    )
