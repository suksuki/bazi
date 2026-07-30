from __future__ import annotations

from collections.abc import Callable
from typing import Any

from sqlalchemy import text

from abu_v60.dream.catalog import ActiveEpisodeCatalog
from abu_v60.dream.persistence import DreamRepository
from abu_v60.experience import ExperienceProjectionComposer


class DreamEncounterCreator:
    """Create one admitted Encounter without expanding the Dream service owner."""

    def __init__(
        self,
        *,
        repository: DreamRepository,
        catalog_loader: Callable[[Any], ActiveEpisodeCatalog],
        experience: ExperienceProjectionComposer,
    ) -> None:
        self._repository = repository
        self._catalog_loader = catalog_loader
        self._experience = experience

    def create(
        self,
        *,
        connection: Any,
        account_ref: str,
        question_ref: str,
        actor_ref: str,
        tree_ref: str,
        causation_id: str,
    ) -> str:
        question = (
            connection.execute(
                text(
                    """
                    SELECT cutoff_tick
                    FROM story.question_instances
                    WHERE question_ref = :question_ref
                    """
                ),
                {"question_ref": question_ref},
            )
            .mappings()
            .one()
        )
        episode = self._catalog_loader(connection).for_question(question_ref)
        runtime_metadata = self._experience.question_metadata(
            question_ref=question_ref,
            runtime_metadata=episode.runtime_metadata.model_dump(mode="json"),
        )
        return self._repository.create_encounter(
            connection=connection,
            account_ref=account_ref,
            question_ref=question_ref,
            actor_ref=actor_ref,
            tree_ref=tree_ref,
            causation_id=causation_id,
            cutoff_tick=int(question["cutoff_tick"]),
            npc_choice_id=str(runtime_metadata["npc_choice_id"]),
        )
