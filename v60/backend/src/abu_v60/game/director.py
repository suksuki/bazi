from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from abu_v60.game.contracts import DreamEpisodeContract, GameplayScene
from abu_v60.game.engine import DreamGameEngine
from abu_v60.game.scenes import DreamSceneRegistry, life_tree_scene_registry
from abu_v60.provenance import content_hash


class EpisodeContractError(ValueError):
    pass


class DreamGameplayDirector:
    """Compose one persisted Episode contract with pure encounter rules."""

    def __init__(
        self,
        engine: DreamGameEngine | None = None,
        scenes: DreamSceneRegistry | None = None,
    ) -> None:
        self._engine = engine or DreamGameEngine()
        self._scenes = scenes or life_tree_scene_registry()

    def load_episode(
        self,
        *,
        payload: Mapping[str, Any],
        expected_hash: str,
        question_ref: str,
    ) -> DreamEpisodeContract:
        episode = DreamEpisodeContract.model_validate(payload)
        if episode.question_ref != question_ref:
            raise EpisodeContractError("episode_question_identity_mismatch")
        actual_hash = content_hash(episode.model_dump(mode="json"))
        if actual_hash != expected_hash:
            raise EpisodeContractError("episode_contract_hash_mismatch")
        return episode

    def scene(
        self,
        *,
        episode: DreamEpisodeContract,
        state: Mapping[str, Any],
        organs: Mapping[str, Mapping[str, Any]],
        encounter_completed: bool,
        continuation_label: str | None = None,
    ) -> GameplayScene:
        continuation_available = encounter_completed and continuation_label is not None
        phase = self._engine.phase(state)
        scene = self._scenes.resolve(
            gameplay_id=episode.gameplay_id,
            phase=phase,
        )
        return GameplayScene(
            gameplay_id=episode.gameplay_id,
            scene_id=scene.scene_id,
            scene_version=scene.scene_version,
            layout_key=scene.layout_key,
            episode_ref=episode.episode_ref,
            episode_version=episode.episode_version,
            content_key=episode.content_key,
            chapter=episode.chapter,
            phase=phase,
            available_commands=self._engine.available_commands(
                state=state,
                organs=organs,
                encounter_completed=encounter_completed,
                continuation_available=continuation_available,
            ),
            organs=tuple(self._engine.public_organs(organs=organs, state=state)),
            continuation_available=continuation_available,
            continuation_label=continuation_label,
        )
