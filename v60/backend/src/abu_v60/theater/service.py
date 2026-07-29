from __future__ import annotations

from typing import Any

from abu_v60.context import ExperienceContextEnvelope, ExperienceUnit
from abu_v60.story.service import LifeStoryEngine


class TheaterProjector:
    """Render only committed story material selected by the LifeStoryEngine."""

    def __init__(self, story_engine: LifeStoryEngine | None = None) -> None:
        self._story_engine = story_engine or LifeStoryEngine()

    def project(
        self,
        *,
        context: ExperienceContextEnvelope,
    ) -> dict[str, Any]:
        evidence_refs = tuple(
            item.evidence_ref
            for item in (
                context.revealed_evidence
                if context.progress.revealed
                else context.baseline_evidence
            )
        )
        scene_plan = self._story_engine.plan_committed_scene(
            world_ref=context.lineage.world_ref,
            question_ref=context.lineage.question_ref,
            scene_ref=context.story.scene_ref,
            beat_text=context.story.theater_beat,
            content_key=context.story.content_key,
            phase=context.story.phase.value,
            disclosure=context.story.disclosure.value,
            evidence_refs=evidence_refs,
            world_event_ref=context.lineage.world_event_ref,
            decision_refs=context.decision_refs,
        )
        return {
            "context_ref": context.context_ref,
            "disclosure": context.disclosure_for(ExperienceUnit.THEATER).model_dump(mode="json"),
            "scene_ref": scene_plan.scene_ref,
            "story_version": scene_plan.story_version,
            "content_key": context.story.content_key,
            "phase": context.story.phase.value,
            "narrative_disclosure": context.story.disclosure.value,
            "beat": context.story.theater_beat,
            "evidence_refs": list(evidence_refs),
            "decision_refs": list(context.decision_refs),
            "future_outcome_visible": False,
            "revealed_outcome_visible": context.progress.revealed,
            "scene_plan": scene_plan.model_dump(mode="json"),
        }
