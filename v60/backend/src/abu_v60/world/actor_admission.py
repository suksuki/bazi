from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy import text

from abu_v60.provenance import canonical_json, content_hash


class WorldActorAdmissionError(ValueError):
    pass


class WorldActorDefinition(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    actor_ref: str = Field(min_length=1)
    world_ref: str = Field(min_length=1)
    case_ref: str = Field(min_length=1)
    actor_kind: str = Field(min_length=1)
    display_name: str = Field(min_length=1)
    branch: str = Field(min_length=1)
    initial_actor_version: Literal[1] = 1
    initial_timeline: dict[str, Any]
    initial_state: dict[str, Any]

    @model_validator(mode="after")
    def initial_state_is_complete(self) -> WorldActorDefinition:
        if self.initial_timeline.get("timeline_version") != 1:
            raise ValueError("world_actor_timeline_version_required")
        if not str(self.initial_state.get("location", "")).strip():
            raise ValueError("world_actor_location_required")
        return self


class WorldActorAdmissionManifest(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    admission_version: Literal["v60.world-actor-admission.001"]
    actor_ref: str = Field(min_length=1)
    world_ref: str = Field(min_length=1)
    case_ref: str = Field(min_length=1)
    actor_kind: str = Field(min_length=1)
    display_name: str = Field(min_length=1)
    branch: str = Field(min_length=1)
    identity_hash: str = Field(min_length=64, max_length=64)


def _identity_payload(definition: WorldActorDefinition) -> dict[str, str]:
    return {
        "actor_ref": definition.actor_ref,
        "world_ref": definition.world_ref,
        "case_ref": definition.case_ref,
        "actor_kind": definition.actor_kind,
        "display_name": definition.display_name,
        "branch": definition.branch,
    }


def validate_persisted_world_actor_admission(
    persisted: dict[str, Any],
) -> WorldActorAdmissionManifest:
    try:
        manifest = WorldActorAdmissionManifest.model_validate(persisted["admission_manifest_json"])
    except (KeyError, ValueError) as exc:
        raise WorldActorAdmissionError("world_actor_admission_manifest_invalid") from exc
    if content_hash(manifest.model_dump(mode="json")) != persisted.get("admission_manifest_hash"):
        raise WorldActorAdmissionError("world_actor_admission_manifest_hash_mismatch")
    identity = {
        "actor_ref": persisted["actor_ref"],
        "world_ref": persisted["world_ref"],
        "case_ref": persisted["case_ref"],
        "actor_kind": persisted["actor_kind"],
        "display_name": persisted["display_name"],
        "branch": persisted["branch"],
    }
    if content_hash(identity) != manifest.identity_hash:
        raise WorldActorAdmissionError("world_actor_identity_hash_mismatch")
    for key, value in identity.items():
        if getattr(manifest, key) != value:
            raise WorldActorAdmissionError(f"world_actor_{key}_binding_mismatch")
    return manifest


class WorldActorAdmissionService:
    """World-owned idempotent Actor identity admission."""

    def admit(
        self,
        connection: Any,
        *,
        definition: WorldActorDefinition,
    ) -> WorldActorAdmissionManifest:
        identity = _identity_payload(definition)
        manifest = WorldActorAdmissionManifest(
            admission_version="v60.world-actor-admission.001",
            **identity,
            identity_hash=content_hash(identity),
        )
        manifest_hash = content_hash(manifest.model_dump(mode="json"))
        state_hash = content_hash(
            {
                "timeline": definition.initial_timeline,
                "state": definition.initial_state,
            }
        )
        connection.execute(
            text(
                """
                INSERT INTO world.actors
                    (actor_ref, world_ref, case_ref, actor_kind, display_name,
                     branch, actor_version, timeline_json, state_json, state_hash,
                     admission_manifest_json, admission_manifest_hash)
                VALUES
                    (:actor_ref, :world_ref, :case_ref, :actor_kind, :display_name,
                     :branch, :actor_version, CAST(:timeline AS jsonb),
                     CAST(:state AS jsonb), :state_hash,
                     CAST(:manifest AS jsonb), :manifest_hash)
                ON CONFLICT (actor_ref) DO NOTHING
                """
            ),
            {
                **identity,
                "actor_version": definition.initial_actor_version,
                "timeline": canonical_json(definition.initial_timeline),
                "state": canonical_json(definition.initial_state),
                "state_hash": state_hash,
                "manifest": canonical_json(manifest.model_dump(mode="json")),
                "manifest_hash": manifest_hash,
            },
        )
        row = (
            connection.execute(
                text("SELECT * FROM world.actors WHERE actor_ref = :actor_ref"),
                {"actor_ref": definition.actor_ref},
            )
            .mappings()
            .one()
        )
        try:
            persisted_manifest = validate_persisted_world_actor_admission(dict(row))
        except WorldActorAdmissionError as exc:
            raise WorldActorAdmissionError("world_actor_admission_conflict") from exc
        if persisted_manifest != manifest:
            raise WorldActorAdmissionError("world_actor_admission_conflict")
        self._refresh_population(connection, world_ref=definition.world_ref)
        return manifest

    @staticmethod
    def _refresh_population(connection: Any, *, world_ref: str) -> None:
        connection.execute(
            text(
                """
                UPDATE world.worlds
                SET state_json = jsonb_set(
                        state_json,
                        '{actor_population}',
                        to_jsonb((
                            SELECT count(*)
                            FROM world.actors
                            WHERE actors.world_ref = :world_ref
                        ))
                    ),
                    updated_at = now()
                WHERE world_ref = :world_ref
                """
            ),
            {"world_ref": world_ref},
        )
