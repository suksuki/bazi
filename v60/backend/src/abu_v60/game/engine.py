from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from abu_v60.game.contracts import (
    DreamCommand,
    DreamPhase,
    EncounterProgress,
    GameMutation,
)

LEAF_KEYS = ("evidence_leaf_world", "evidence_leaf_structure")
BRANCH_KEY = "structure_branch"
FLOWER_KEY = "question_flower"
FRUIT_KEY = "outcome_fruit"


class GameRuleError(ValueError):
    pass


class DreamGameEngine:
    """Pure encounter rules. Persistence and world outcomes stay outside this engine."""

    def progress(self, state: Mapping[str, Any]) -> EncounterProgress:
        return EncounterProgress.model_validate(state)

    def phase(self, state: Mapping[str, Any] | EncounterProgress) -> DreamPhase:
        progress = state if isinstance(state, EncounterProgress) else self.progress(state)
        if progress.reconciled:
            return DreamPhase.COMPLETED
        if progress.revealed:
            return DreamPhase.REVEALED
        if progress.world_settled:
            return DreamPhase.REVEAL_READY
        if progress.answer_sealed:
            return DreamPhase.WAITING_FOR_WORLD
        if progress.question_visible:
            return DreamPhase.QUESTION_OPEN
        return DreamPhase.OBSERVING

    def observe(
        self,
        *,
        state: Mapping[str, Any],
        organ_key: str,
        organs: Mapping[str, Mapping[str, Any]],
    ) -> GameMutation:
        progress = self.progress(state)
        if progress.answer_sealed:
            raise GameRuleError("observation_closed_after_answer_seal")

        observed = list(progress.observed_organs)
        question_visible = progress.question_visible
        organ_ref = str(organs[organ_key]["organ_ref"])
        if organ_key in LEAF_KEYS:
            if organ_ref not in observed:
                observed.append(organ_ref)
        elif organ_key == BRANCH_KEY:
            leaf_refs = {str(organs[key]["organ_ref"]) for key in LEAF_KEYS}
            if not leaf_refs.issubset(observed):
                raise GameRuleError("both_evidence_leaves_required")
            if organ_ref not in observed:
                observed.append(organ_ref)
        elif organ_key == FLOWER_KEY:
            branch_ref = str(organs[BRANCH_KEY]["organ_ref"])
            if branch_ref not in observed:
                raise GameRuleError("structure_branch_required")
            question_visible = True
        else:
            raise GameRuleError("organ_not_observable_in_current_state")

        next_progress = progress.model_copy(
            update={
                "observed_organs": tuple(observed),
                "question_visible": question_visible,
            }
        )
        return GameMutation(
            phase=self.phase(next_progress),
            progress=next_progress,
        )

    def available_commands(
        self,
        *,
        state: Mapping[str, Any],
        organs: Mapping[str, Mapping[str, Any]],
        encounter_completed: bool = False,
        continuation_available: bool = False,
    ) -> tuple[DreamCommand, ...]:
        progress = self.progress(state)
        if encounter_completed:
            commands = [DreamCommand.RETURN_TO_GROVE]
            if continuation_available:
                commands.insert(0, DreamCommand.CONTINUE_ENCOUNTER)
            return tuple(commands)
        if progress.reconciled:
            return ()
        if progress.revealed:
            return (DreamCommand.RECONCILE,)
        if progress.world_settled:
            return (DreamCommand.REVEAL,)
        if progress.answer_sealed:
            return ()
        if progress.question_visible:
            return (DreamCommand.SEAL_ANSWER,)

        observed = set(progress.observed_organs)
        leaf_refs = {str(organs[key]["organ_ref"]) for key in LEAF_KEYS}
        branch_ref = str(organs[BRANCH_KEY]["organ_ref"])
        commands: list[DreamCommand] = []
        if not leaf_refs.issubset(observed):
            commands.append(DreamCommand.OBSERVE_EVIDENCE)
        elif branch_ref not in observed:
            commands.append(DreamCommand.OBSERVE_STRUCTURE)
        else:
            commands.append(DreamCommand.OPEN_QUESTION)
        return tuple(commands)

    def assert_command_available(
        self,
        *,
        command: DreamCommand,
        state: Mapping[str, Any],
        organs: Mapping[str, Mapping[str, Any]],
        organ_key: str | None = None,
        encounter_completed: bool = False,
        continuation_available: bool = False,
    ) -> None:
        available = self.available_commands(
            state=state,
            organs=organs,
            encounter_completed=encounter_completed,
            continuation_available=continuation_available,
        )
        if command not in available:
            raise GameRuleError("dream_command_not_available")

        expected_organ_commands = {key: DreamCommand.OBSERVE_EVIDENCE for key in LEAF_KEYS} | {
            BRANCH_KEY: DreamCommand.OBSERVE_STRUCTURE,
            FLOWER_KEY: DreamCommand.OPEN_QUESTION,
        }
        if organ_key is None:
            if command in expected_organ_commands.values():
                raise GameRuleError("dream_command_target_required")
            return
        if expected_organ_commands.get(organ_key) is not command:
            raise GameRuleError("dream_command_target_mismatch")

    def public_organs(
        self,
        *,
        organs: Mapping[str, Mapping[str, Any]],
        state: Mapping[str, Any],
    ) -> list[dict[str, Any]]:
        progress = self.progress(state)
        observed = set(progress.observed_organs)
        leaves_complete = all(str(organs[key]["organ_ref"]) in observed for key in LEAF_KEYS)
        branch_complete = str(organs[BRANCH_KEY]["organ_ref"]) in observed
        output: list[dict[str, Any]] = []
        for key, organ in organs.items():
            visible = key in LEAF_KEYS or (key == BRANCH_KEY and leaves_complete)
            visible = visible or (
                key == FLOWER_KEY and branch_complete and not progress.answer_sealed
            )
            visible = visible or (key == FRUIT_KEY and progress.answer_sealed)
            organ_ref = str(organ["organ_ref"])
            status = (
                "HIDDEN"
                if not visible
                else "COMPLETED"
                if organ_ref in observed
                else "OPEN"
                if key == FLOWER_KEY and progress.question_visible
                else "MATURED"
                if key == FRUIT_KEY and progress.world_settled
                else "SEALED"
                if key == FRUIT_KEY and progress.answer_sealed
                else "AVAILABLE"
            )
            output.append({**organ, "key": key, "visible": visible, "status": status})
        return output
