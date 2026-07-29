from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from abu_v60.abu import AbuSaysProjector
from abu_v60.context import (
    ExperienceContextEnvelope,
    ExperienceUnit,
    build_experience_context,
)
from abu_v60.lab import LabProjector
from abu_v60.mingli.projection import MingliWorkspaceProjector
from abu_v60.story.service import LifeStoryEngine
from abu_v60.theater import TheaterProjector


class ExperienceProjectionComposer:
    """Compose five read models from one canonical Case/world lineage."""

    def __init__(self) -> None:
        self._story = LifeStoryEngine()
        self._abu = AbuSaysProjector()
        self._theater = TheaterProjector(self._story)
        self._mingli = MingliWorkspaceProjector()
        self._lab = LabProjector()

    def question_metadata(
        self,
        *,
        question_ref: str,
        runtime_metadata: Mapping[str, Any] | None,
    ) -> dict[str, Any]:
        return self._story.episode_runtime_metadata(
            question_ref=question_ref,
            runtime_metadata=runtime_metadata,
        )

    def compose(
        self,
        *,
        context: ExperienceContextEnvelope,
    ) -> dict[str, Any]:
        projections = {
            "dream": {
                "authority": "DREAM_GAME_ENGINE",
                "world_ref": context.lineage.world_ref,
                "question_ref": context.lineage.question_ref,
                "content_key": context.story.content_key,
                "journey_title": context.story.title,
                "journey_status": context.story.status_line,
                "context_ref": context.context_ref,
                "disclosure": context.disclosure_for(ExperienceUnit.DREAM).model_dump(mode="json"),
            },
            "mingli": self._mingli.project(context=context),
            "abu": self._abu.project(context=context),
            "theater": self._theater.project(context=context),
            "lab": self._lab.project(context=context),
        }
        context_refs = {str(projection["context_ref"]) for projection in projections.values()}
        if context_refs != {context.context_ref}:
            raise ValueError("product_unit_context_lineage_diverged")
        return projections

    def build_context(self, **values: Any) -> ExperienceContextEnvelope:
        context = build_experience_context(**values)
        if {
            disclosure.unit
            for disclosure in (context.disclosure_for(unit) for unit in ExperienceUnit)
        } != set(ExperienceUnit):
            raise ValueError("experience_context_disclosure_incomplete")
        return context
