from __future__ import annotations

from typing import Any

from sqlalchemy import text

from abu_v60.dream.command_guard import DreamCommandGuard
from abu_v60.dream.errors import DreamStateError
from abu_v60.dream.persistence import DreamRepository
from abu_v60.game import DreamCommandEnvelope, DreamGameEngine
from abu_v60.world.service import WorldContinuityEngine


class DreamGroveDepartureCoordinator:
    """Archive one completed or expired Encounter before Grove re-entry."""

    def __init__(
        self,
        *,
        repository: DreamRepository,
        command_guard: DreamCommandGuard,
        game: DreamGameEngine,
        world: WorldContinuityEngine,
    ) -> None:
        self._repository = repository
        self._command_guard = command_guard
        self._game = game
        self._world = world

    def execute(
        self,
        connection: Any,
        *,
        account_ref: str,
        envelope: DreamCommandEnvelope,
    ) -> None:
        if self._repository.command_replayed(
            connection=connection,
            account_ref=account_ref,
            envelope=envelope,
        ):
            return
        encounter = self._repository.locked_encounter(
            connection,
            account_ref=account_ref,
        )
        self._command_guard.assert_identity(
            encounter=encounter,
            envelope=envelope,
        )
        self._command_guard.assert_version(
            encounter=encounter,
            envelope=envelope,
        )
        expired_at_tick = self._expired_unsealed_tick(
            connection=connection,
            encounter=encounter,
        )
        if encounter["status"] != "COMPLETED" and expired_at_tick is None:
            raise DreamStateError("return_to_grove_requires_completed_encounter")
        if expired_at_tick is None:
            self._command_guard.assert_available(
                connection=connection,
                encounter=encounter,
                envelope=envelope,
                organ_key=None,
            )
            state = (
                self._game.progress(encounter["state_json"])
                .model_copy(update={"departed_to_grove": True})
                .as_state_json()
            )
            result_status = "COMPLETED"
        else:
            state = {
                **dict(encounter["state_json"]),
                "departed_to_grove": True,
                "expired_unsealed": True,
                "expired_at_tick": expired_at_tick,
                "expiration_reason": "QUESTION_WINDOW_CLOSED",
            }
            result_status = str(encounter["status"])
        self._repository.write_encounter_state(
            connection=connection,
            encounter=encounter,
            status=result_status,
            state=state,
        )
        self._repository.record_command_receipt(
            connection=connection,
            account_ref=account_ref,
            envelope=envelope,
            result_encounter_ref=encounter["encounter_ref"],
        )

    def _expired_unsealed_tick(
        self,
        *,
        connection: Any,
        encounter: dict[str, Any],
    ) -> int | None:
        state = encounter["state_json"]
        if (
            encounter["status"] != "QUESTION_OPEN"
            or state.get("question_visible") is not True
            or state.get("answer_sealed") is True
        ):
            return None
        question = (
            connection.execute(
                text(
                    """
                    SELECT question.due_tick, event.event_json
                    FROM story.question_instances AS question
                    JOIN world.events AS event
                      ON event.world_event_ref = question.world_event_ref
                    WHERE question.question_ref = :question_ref
                    """
                ),
                {"question_ref": encounter["question_ref"]},
            )
            .mappings()
            .one()
        )
        if question["event_json"].get("opportunity_cycle_ref") is None:
            return None
        current_tick = self._world.current_tick(connection)
        return current_tick if current_tick >= int(question["due_tick"]) else None
