from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from abu_v60.dream.catalog import ActiveEpisodeCatalog
from abu_v60.dream.errors import DreamConflictError, DreamStateError
from abu_v60.dream.grove import (
    DreamGroveRepository,
    GroveCandidateDefinition,
)
from abu_v60.dream.grove_chapter_routing import (
    DreamGroveChapterRouter,
)
from abu_v60.dream.opportunity import (
    DreamOpportunityError,
    DreamOpportunityMaterializer,
)
from abu_v60.dream.persistence import DreamRepository


@dataclass(frozen=True, slots=True)
class GroveEncounterIntent:
    question_ref: str
    actor_ref: str
    tree_ref: str
    causation_id: str


class DreamGroveEncounterSelector:
    """Resolve one grove choice into a fresh Episode without owning encounters."""

    def __init__(
        self,
        *,
        repository: DreamRepository,
        grove: DreamGroveRepository,
        catalog_loader: Callable[[Any], ActiveEpisodeCatalog],
        opportunities: DreamOpportunityMaterializer,
        chapter_router: DreamGroveChapterRouter,
    ) -> None:
        self._repository = repository
        self._grove = grove
        self._catalog_loader = catalog_loader
        self._opportunities = opportunities
        self._chapter_router = chapter_router

    def project_candidates(
        self,
        connection: Any,
        *,
        account_ref: str,
        candidates: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        catalog = self._catalog_loader(connection)
        projected: list[dict[str, Any]] = []
        for candidate in candidates:
            definition = self._candidate_definition(
                connection,
                candidate_ref=str(candidate["candidate_ref"]),
                for_update=False,
            )
            if (
                candidate.get("candidate_hash")
                != definition.candidate_hash
                or candidate.get("tree_ref") != definition.tree_ref
            ):
                raise DreamStateError(
                    "dream_grove_candidate_projection_mismatch"
                )
            resolution = self._chapter_router.resolve(
                connection,
                account_ref=account_ref,
                candidate=definition,
                catalog=catalog,
            )
            projected.append(
                {
                    **candidate,
                    "chapter_route": resolution.route.model_dump(mode="json"),
                }
            )
        return projected

    def select(
        self,
        connection: Any,
        *,
        account_ref: str,
        candidate_ref: str,
    ) -> GroveEncounterIntent | None:
        self._chapter_router.lock_account(
            connection,
            account_ref=account_ref,
        )
        existing = self._repository.current_encounter(
            connection,
            account_ref=account_ref,
            for_update=True,
        )
        candidate = self._candidate_definition(
            connection,
            candidate_ref=candidate_ref,
            for_update=True,
        )
        catalog = self._catalog_loader(connection)
        if existing is not None:
            source_ref = self._opportunities.source_question_ref(
                connection,
                question_ref=existing["question_ref"],
            )
            if not catalog.is_reachable(
                candidate.question_ref,
                source_ref,
            ):
                raise DreamConflictError("dream_grove_selection_already_committed")
            return None

        resolution = self._chapter_router.resolve(
            connection,
            account_ref=account_ref,
            candidate=candidate,
            catalog=catalog,
        )
        if resolution.route.status == "STORY_CURRENTLY_COMPLETE":
            raise DreamStateError("dream_grove_story_currently_complete")
        source_episode = resolution.target_episode
        try:
            episode = self._opportunities.materialize(
                connection,
                source_question_ref=source_episode.question_ref,
                source_candidate_ref=candidate.candidate_ref,
                source_candidate_hash=candidate.candidate_hash,
                source_transition_ref=resolution.route.transition_ref,
                source_transition_hash=resolution.route.transition_hash,
                preceding_world_event_ref=(
                    resolution.preceding_world_event_ref
                ),
            )
        except DreamOpportunityError as exc:
            raise DreamStateError(str(exc)) from exc
        return GroveEncounterIntent(
            question_ref=episode.question_ref,
            actor_ref=episode.actor_ref,
            tree_ref=episode.tree_ref,
            causation_id=episode.baseline_event_ref,
        )

    def _candidate_definition(
        self,
        connection: Any,
        *,
        candidate_ref: str,
        for_update: bool,
    ) -> GroveCandidateDefinition:
        candidate = self._grove.candidate_definition(
            connection,
            candidate_ref=candidate_ref,
            for_update=for_update,
        )
        if candidate is None:
            raise DreamStateError("dream_grove_candidate_not_found")
        return candidate
