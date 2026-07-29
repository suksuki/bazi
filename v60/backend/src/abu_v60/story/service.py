from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from abu_v60.provenance import stable_ref
from abu_v60.story.contracts import ScenePlan, StoryBeat, StoryBeatKind
from abu_v60.system_manifest import STORY_ENGINE_VERSION


class StoryContractError(ValueError):
    pass


class LifeStoryEngine:
    """Compile already-authorized semantic material into deterministic scene plans."""

    def episode_runtime_metadata(
        self,
        *,
        question_ref: str,
        runtime_metadata: Mapping[str, Any] | None,
    ) -> dict[str, Any]:
        metadata = dict(runtime_metadata or {})
        required = (
            "baseline_event_ref",
            "npc_choice_id",
            "flower_name",
            "fruit_name",
        )
        if any(not metadata.get(key) for key in required):
            raise StoryContractError(f"question_runtime_metadata_incomplete:{question_ref}")
        metadata.setdefault("return_label", None)
        return metadata

    def plan_committed_scene(
        self,
        *,
        world_ref: str,
        question_ref: str,
        scene_ref: str,
        beat_text: str,
        content_key: str,
        phase: str,
        disclosure: str,
        evidence_refs: Sequence[str],
        world_event_ref: str,
        decision_refs: Sequence[str] = (),
    ) -> ScenePlan:
        source_refs = tuple(evidence_refs)
        beats = tuple(
            StoryBeat(
                beat_ref=stable_ref(
                    "v60-story-beat",
                    {
                        "question_ref": question_ref,
                        "source_ref": evidence_ref,
                        "position": index,
                    },
                ),
                kind=StoryBeatKind.OBSERVATION,
                source_ref=evidence_ref,
            )
            for index, evidence_ref in enumerate(source_refs)
        )
        closing_beat = StoryBeat(
            beat_ref=stable_ref(
                "v60-story-beat",
                {
                    "question_ref": question_ref,
                    "scene_ref": scene_ref,
                    "content_key": content_key,
                    "phase": phase,
                    "disclosure": disclosure,
                },
            ),
            kind={
                "OBSERVING": StoryBeatKind.OBSERVATION,
                "QUESTION_OPEN": StoryBeatKind.QUESTION,
                "WAITING_FOR_WORLD": StoryBeatKind.DECISION,
                "REVEAL_READY": StoryBeatKind.WORLD_CHANGE,
                "REVEALED": StoryBeatKind.REVEAL,
                "COMPLETED": StoryBeatKind.DEPARTURE,
            }[phase],
            source_ref=(
                decision_refs[0]
                if decision_refs
                else world_event_ref
                if phase == "REVEAL_READY"
                else question_ref
            ),
            dialogue_intent=beat_text,
        )
        return ScenePlan(
            scene_ref=scene_ref,
            story_version=STORY_ENGINE_VERSION,
            world_ref=world_ref,
            source_event_refs=source_refs,
            decision_refs=tuple(decision_refs),
            beats=(*beats, closing_beat),
        )
