from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from abu_v60.game.contracts import DreamPhase


class DreamSceneDefinition(BaseModel):
    """Stable presentation identity for one gameplay phase."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    scene_id: str = Field(min_length=1)
    scene_version: int = Field(ge=1)
    gameplay_id: str = Field(min_length=1)
    phase: DreamPhase
    layout_key: str = Field(min_length=1)


class DreamSceneRegistry:
    def __init__(self, scenes: tuple[DreamSceneDefinition, ...]) -> None:
        self._scenes = scenes
        identities = {(scene.gameplay_id, scene.phase) for scene in scenes}
        if len(identities) != len(scenes):
            raise ValueError("dream_scene_identity_not_unique")
        scene_ids = {scene.scene_id for scene in scenes}
        if len(scene_ids) != len(scenes):
            raise ValueError("dream_scene_id_not_unique")

    def resolve(self, *, gameplay_id: str, phase: DreamPhase) -> DreamSceneDefinition:
        scene = next(
            (
                item
                for item in self._scenes
                if item.gameplay_id == gameplay_id and item.phase == phase
            ),
            None,
        )
        if scene is None:
            raise ValueError("dream_scene_not_registered")
        return scene

    def public_manifest(self) -> list[dict[str, object]]:
        return [
            scene.model_dump(mode="json")
            for scene in sorted(self._scenes, key=lambda item: item.phase.value)
        ]


def life_tree_scene_registry() -> DreamSceneRegistry:
    gameplay_id = "life_tree_question_v1"
    return DreamSceneRegistry(
        tuple(
            DreamSceneDefinition(
                scene_id=f"v60.scene.life-tree.{phase.value.lower().replace('_', '-')}",
                scene_version=1,
                gameplay_id=gameplay_id,
                phase=phase,
                layout_key="picture_book_fixed_tree",
            )
            for phase in DreamPhase
        )
    )
