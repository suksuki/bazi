from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from abu_v60.dream.catalog import ActiveEpisodeCatalog
from abu_v60.dream.errors import DreamConflictError, DreamStateError
from abu_v60.dream.grove import DreamGroveRepository
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
    ) -> None:
        self._repository = repository
        self._grove = grove
        self._catalog_loader = catalog_loader
        self._opportunities = opportunities

    def select(
        self,
        connection: Any,
        *,
        account_ref: str,
        candidate_ref: str,
    ) -> GroveEncounterIntent | None:
        existing = self._repository.current_encounter(
            connection,
            account_ref=account_ref,
            for_update=True,
        )
        candidate = self._grove.candidate(
            connection,
            candidate_ref=candidate_ref,
        )
        if candidate is None:
            raise DreamStateError("dream_grove_candidate_not_found")
        if existing is not None:
            source_ref = self._opportunities.source_question_ref(
                connection,
                question_ref=existing["question_ref"],
            )
            if source_ref != candidate["question_ref"]:
                raise DreamConflictError("dream_grove_selection_already_committed")
            return None

        source_episode = self._catalog_loader(connection).for_question(
            str(candidate["question_ref"])
        )
        if not source_episode.entrypoint:
            raise DreamStateError("dream_grove_candidate_not_entrypoint")
        if (
            source_episode.actor_ref != candidate["actor_ref"]
            or source_episode.tree_ref != candidate["tree_ref"]
        ):
            raise DreamStateError("dream_grove_candidate_lineage_mismatch")
        try:
            episode = self._opportunities.materialize(
                connection,
                source_question_ref=source_episode.question_ref,
            )
        except DreamOpportunityError as exc:
            raise DreamStateError(str(exc)) from exc
        return GroveEncounterIntent(
            question_ref=episode.question_ref,
            actor_ref=episode.actor_ref,
            tree_ref=episode.tree_ref,
            causation_id=episode.baseline_event_ref,
        )
