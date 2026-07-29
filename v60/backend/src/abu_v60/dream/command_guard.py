from __future__ import annotations

from collections.abc import Callable
from typing import Any

from sqlalchemy import text

from abu_v60.dream.catalog import ActiveEpisodeCatalog
from abu_v60.dream.errors import DreamConflictError, DreamStateError
from abu_v60.game import (
    DreamCommandEnvelope,
    DreamGameEngine,
    GameRuleError,
)


class DreamCommandGuard:
    """Owns command identity, version and gameplay availability checks."""

    def __init__(
        self,
        *,
        game: DreamGameEngine,
        catalog_loader: Callable[[Any], ActiveEpisodeCatalog],
    ) -> None:
        self._game = game
        self._catalog_loader = catalog_loader

    @staticmethod
    def assert_identity(
        *,
        encounter: dict[str, Any],
        envelope: DreamCommandEnvelope,
    ) -> None:
        if encounter["encounter_ref"] != envelope.encounter_ref:
            raise DreamConflictError("dream_command_encounter_mismatch")

    @staticmethod
    def assert_version(
        *,
        encounter: dict[str, Any],
        envelope: DreamCommandEnvelope,
    ) -> None:
        if int(encounter["version"]) != envelope.expected_version:
            raise DreamConflictError("dream_command_version_conflict")

    def assert_available(
        self,
        *,
        connection: Any,
        encounter: dict[str, Any],
        envelope: DreamCommandEnvelope,
        organ_key: str | None,
        organs: dict[str, Any] | None = None,
        catalog: ActiveEpisodeCatalog | None = None,
    ) -> None:
        if organs is None:
            organs = connection.execute(
                text(
                    """
                    SELECT organ_set_json
                    FROM story.question_instances
                    WHERE question_ref = :question_ref
                    """
                ),
                {"question_ref": encounter["question_ref"]},
            ).scalar_one()
        active_catalog = catalog or self._catalog_loader(connection)
        try:
            self._game.assert_command_available(
                command=envelope.command,
                state=encounter["state_json"],
                organs=organs,
                organ_key=organ_key,
                encounter_completed=encounter["status"] == "COMPLETED",
                continuation_available=(
                    active_catalog.next_episode(encounter["question_ref"]) is not None
                ),
            )
        except GameRuleError as exc:
            raise DreamStateError(str(exc)) from exc
