from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import text

from abu_v60.provenance import canonical_json, content_hash


class LifeTreeAdmissionError(ValueError):
    pass


class LifeTreeDefinition(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    tree_ref: str = Field(min_length=1)
    actor_ref: str = Field(min_length=1)
    scene_ref: str = Field(min_length=1)
    initial_tree_version: Literal[1] = 1
    initial_state: str = Field(min_length=1)
    organs: dict[str, Any]


class LifeTreeAdmissionManifest(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    admission_version: Literal[
        "v60.life-tree-admission.001",
        "v60.life-tree-admission.backfill.001",
    ]
    tree_ref: str = Field(min_length=1)
    actor_ref: str = Field(min_length=1)
    scene_ref: str = Field(min_length=1)
    organ_set_hash: str = Field(min_length=64, max_length=64)


def validate_persisted_life_tree_admission(
    persisted: dict[str, Any],
) -> LifeTreeAdmissionManifest:
    try:
        manifest = LifeTreeAdmissionManifest.model_validate(persisted["admission_manifest_json"])
    except (KeyError, ValueError) as exc:
        raise LifeTreeAdmissionError("life_tree_admission_manifest_invalid") from exc
    if content_hash(manifest.model_dump(mode="json")) != persisted.get("admission_manifest_hash"):
        raise LifeTreeAdmissionError("life_tree_admission_manifest_hash_mismatch")
    expected = {
        "tree_ref": persisted["tree_ref"],
        "actor_ref": persisted["actor_ref"],
        "scene_ref": persisted["scene_ref"],
    }
    for key, value in expected.items():
        if getattr(manifest, key) != value:
            raise LifeTreeAdmissionError(f"life_tree_{key}_binding_mismatch")
    return manifest


class LifeTreeAdmissionService:
    """Dream-owned idempotent admission for one persistent semantic tree."""

    def admit(
        self,
        connection: Any,
        *,
        definition: LifeTreeDefinition,
    ) -> LifeTreeAdmissionManifest:
        manifest = LifeTreeAdmissionManifest(
            admission_version="v60.life-tree-admission.001",
            tree_ref=definition.tree_ref,
            actor_ref=definition.actor_ref,
            scene_ref=definition.scene_ref,
            organ_set_hash=content_hash(definition.organs),
        )
        manifest_hash = content_hash(manifest.model_dump(mode="json"))
        projection = {
            "tree_ref": definition.tree_ref,
            "actor_ref": definition.actor_ref,
            "scene_ref": definition.scene_ref,
            "tree_version": definition.initial_tree_version,
            "organs": definition.organs,
        }
        connection.execute(
            text(
                """
                INSERT INTO dream.life_trees
                    (tree_ref, actor_ref, scene_ref, tree_version,
                     state, organs_json, projection_hash,
                     admission_manifest_json, admission_manifest_hash)
                VALUES
                    (:tree_ref, :actor_ref, :scene_ref, :tree_version,
                     :state, CAST(:organs AS jsonb), :projection_hash,
                     CAST(:manifest AS jsonb), :manifest_hash)
                ON CONFLICT (tree_ref) DO NOTHING
                """
            ),
            {
                "tree_ref": definition.tree_ref,
                "actor_ref": definition.actor_ref,
                "scene_ref": definition.scene_ref,
                "tree_version": definition.initial_tree_version,
                "state": definition.initial_state,
                "organs": canonical_json(definition.organs),
                "projection_hash": content_hash(projection),
                "manifest": canonical_json(manifest.model_dump(mode="json")),
                "manifest_hash": manifest_hash,
            },
        )
        row = (
            connection.execute(
                text("SELECT * FROM dream.life_trees WHERE tree_ref = :tree_ref"),
                {"tree_ref": definition.tree_ref},
            )
            .mappings()
            .one()
        )
        try:
            persisted_manifest = validate_persisted_life_tree_admission(dict(row))
        except LifeTreeAdmissionError as exc:
            raise LifeTreeAdmissionError("life_tree_admission_conflict") from exc
        stable_identity_matches = (
            persisted_manifest.tree_ref == definition.tree_ref
            and persisted_manifest.actor_ref == definition.actor_ref
            and persisted_manifest.scene_ref == definition.scene_ref
        )
        if not stable_identity_matches or (
            persisted_manifest.admission_version == "v60.life-tree-admission.001"
            and persisted_manifest != manifest
        ):
            raise LifeTreeAdmissionError("life_tree_admission_conflict")
        return persisted_manifest
