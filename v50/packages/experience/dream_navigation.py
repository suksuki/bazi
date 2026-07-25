from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import Field, model_validator

from experience.contracts import ExperienceModel


DREAM_RETURN_POLICY_VERSION = "deepbazi.dream_return_departure.v1"
DREAM_WORLD_SPACE_REF = "dream-world:canonical-grove:v1"
DREAM_GEOMETRY_VERSION = "dream-grove-geometry.v1"
DREAM_WORLD_VERSION = "dream-world.v1"
DREAM_ABU_WORLD_STATE_VERSION = "canonical-abu-world-state.v1"


class DreamRuntimeState(str, Enum):
    FIRST_VISIT = "FIRST_VISIT"
    RETURN_PREPARE = "RETURN_PREPARE"
    AUTH_REVALIDATING = "AUTH_REVALIDATING"
    WORLD_REHYDRATING = "WORLD_REHYDRATING"
    ANCHOR_INVALID_FALLBACK = "ANCHOR_INVALID_FALLBACK"
    LOCAL_MIST_REENTRY = "LOCAL_MIST_REENTRY"
    FOREST_ACTIVE = "FOREST_ACTIVE"
    MIRROR_ACTIVE = "MIRROR_ACTIVE"
    MIRROR_WITHDRAWING = "MIRROR_WITHDRAWING"
    DEPARTURE_INTENT = "DEPARTURE_INTENT"
    DEPARTURE_COMMITTING = "DEPARTURE_COMMITTING"
    DEPARTED = "DEPARTED"
    VISIT_SUSPENDED = "VISIT_SUSPENDED"
    RECOVERY_REHYDRATING = "RECOVERY_REHYDRATING"
    FAIL_CLOSED = "FAIL_CLOSED"


class DreamWorldPosition(ExperienceModel):
    x: float = Field(ge=0, le=100)
    y: float = Field(ge=0, le=100)


class DreamNavigationSample(ExperienceModel):
    world_projection_ref: str = Field(min_length=24, max_length=180)
    world_space_ref: str = Field(default=DREAM_WORLD_SPACE_REF, min_length=8, max_length=180)
    position: DreamWorldPosition
    camera_heading: float = Field(default=0, ge=-180, le=180)
    geometry_version: str = Field(default=DREAM_GEOMETRY_VERSION, min_length=8, max_length=100)


class TreeObservationAnchor(ExperienceModel):
    schema_version: Literal["deepbazi.dream_tree_observation_anchor.v1"] = (
        "deepbazi.dream_tree_observation_anchor.v1"
    )
    visit_id: str = Field(min_length=1, max_length=180)
    resident_scene_ref: str = Field(min_length=16, max_length=180)
    viewer_position: DreamWorldPosition
    camera_heading: float = Field(ge=-180, le=180)
    root_mirror_space_ref: str = Field(min_length=8, max_length=180)
    created_at: datetime


class DreamDepartureAnchor(ExperienceModel):
    schema_version: Literal["deepbazi.dream_departure_anchor.v1"] = (
        "deepbazi.dream_departure_anchor.v1"
    )
    anchor_id: str = Field(min_length=16, max_length=180)
    viewer_id: str = Field(min_length=1, max_length=180)
    case_namespace: str = Field(min_length=1, max_length=240)
    world_space_ref: str = Field(min_length=8, max_length=180)
    last_stable_forest_position: DreamWorldPosition
    camera_heading: float = Field(ge=-180, le=180)
    geometry_version: str = Field(min_length=8, max_length=100)
    source_visit_id: str = Field(min_length=1, max_length=180)
    visit_sequence: int = Field(ge=1)
    commit_sequence: int = Field(ge=1)
    anchor_version: int = Field(ge=1)
    departure_world_time: int = Field(ge=0)
    committed_at: datetime
    departure_commit_id: str = Field(min_length=16, max_length=180)
    departure_trigger: Literal["SPATIAL_BOUNDARY", "SEMANTIC_EXIT"]
    idempotency_key: str = Field(min_length=16, max_length=360)
    migration_status: Literal["not_applicable", "available", "consumed"] = "not_applicable"
    migration_capability_hash: str = Field(default="", max_length=64)
    migrated_to_anchor_id: str = Field(default="", max_length=180)

    @model_validator(mode="after")
    def validate_guest_migration_boundary(self) -> "DreamDepartureAnchor":
        if self.migration_status == "available" and len(self.migration_capability_hash) != 64:
            raise ValueError("dream_guest_anchor_capability_hash_required")
        if self.migration_status == "consumed" and not self.migrated_to_anchor_id:
            raise ValueError("dream_guest_anchor_migration_target_required")
        return self


class DreamRecoveryCheckpoint(ExperienceModel):
    schema_version: Literal["deepbazi.dream_recovery_checkpoint.v1"] = (
        "deepbazi.dream_recovery_checkpoint.v1"
    )
    recovery_checkpoint_id: str = Field(min_length=16, max_length=180)
    viewer_id: str = Field(min_length=1, max_length=180)
    case_namespace: str = Field(min_length=1, max_length=240)
    visit_id: str = Field(min_length=1, max_length=180)
    latest_safe_forest_position: DreamWorldPosition
    camera_heading: float = Field(ge=-180, le=180)
    geometry_version: str = Field(min_length=8, max_length=100)
    lease_epoch: int = Field(ge=1)
    recovery_sequence: int = Field(ge=1)
    updated_at: datetime
    expires_at: datetime


class DreamControlLease(ExperienceModel):
    schema_version: Literal["deepbazi.dream_control_lease.v1"] = (
        "deepbazi.dream_control_lease.v1"
    )
    lease_id: str = Field(min_length=16, max_length=180)
    viewer_id: str = Field(min_length=1, max_length=180)
    case_namespace: str = Field(min_length=1, max_length=240)
    client_instance_id: str = Field(min_length=8, max_length=180)
    lease_epoch: int = Field(ge=1)
    fence_token: int = Field(ge=1)
    acquired_at: datetime
    real_expires_at: datetime
    status: Literal["active", "superseded", "released"] = "active"


class DreamControlCredential(ExperienceModel):
    client_instance_id: str = Field(min_length=8, max_length=180)
    lease_id: str = Field(min_length=16, max_length=180)
    lease_epoch: int = Field(ge=1)
    fence_token: int = Field(ge=1)


class DreamControlLeaseProjection(ExperienceModel):
    lease_id: str = Field(min_length=16, max_length=180)
    client_instance_id: str = Field(min_length=8, max_length=180)
    lease_epoch: int = Field(ge=1)
    fence_token: int = Field(ge=1)
    real_expires_at: datetime


class DreamWorldProjectionBinding(ExperienceModel):
    schema_version: Literal["deepbazi.dream_world_projection_binding.v1"] = (
        "deepbazi.dream_world_projection_binding.v1"
    )
    world_projection_ref: str = Field(min_length=24, max_length=180)
    viewer_id: str = Field(min_length=1, max_length=180)
    case_namespace: str = Field(min_length=1, max_length=240)
    authorization_version: str = Field(min_length=1, max_length=160)
    world_version: str = Field(default=DREAM_WORLD_VERSION, min_length=1, max_length=100)
    projection_version: str = Field(min_length=1, max_length=100)
    geometry_version: str = Field(default=DREAM_GEOMETRY_VERSION, min_length=1, max_length=100)
    issued_at: datetime
    expires_at: datetime


class DreamAnchorResolution(ExperienceModel):
    schema_version: Literal["deepbazi.dream_anchor_resolution.v1"] = (
        "deepbazi.dream_anchor_resolution.v1"
    )
    source: Literal[
        "departure_anchor",
        "recovery_checkpoint",
        "own_tree_safe_point",
        "formal_grove_entrance",
    ]
    world_space_ref: str = Field(default=DREAM_WORLD_SPACE_REF, min_length=8, max_length=180)
    position: DreamWorldPosition
    camera_heading: float = Field(ge=-180, le=180)
    geometry_version: str = Field(default=DREAM_GEOMETRY_VERSION, min_length=8, max_length=100)
    source_ref: str = Field(default="", max_length=180)
    fallback_reason: str = Field(default="", max_length=120)


class CanonicalAbuProjection(ExperienceModel):
    schema_version: Literal["deepbazi.canonical_abu_public_projection.v1"] = (
        "deepbazi.canonical_abu_public_projection.v1"
    )
    canonical_abu_ref: Literal["canonical-being:abu"] = "canonical-being:abu"
    identity_mode: Literal["CANONICAL_UNIQUE_BEING"] = "CANONICAL_UNIQUE_BEING"
    world_space_ref: str = Field(default=DREAM_WORLD_SPACE_REF, min_length=8, max_length=180)
    public_position: DreamWorldPosition
    public_action: Literal["resting", "walking", "elsewhere"]
    world_state_version: str = Field(
        default=DREAM_ABU_WORLD_STATE_VERSION,
        min_length=1,
        max_length=100,
    )
    private_content_included: Literal[False] = False


class DreamDepartureResult(ExperienceModel):
    schema_version: Literal["deepbazi.dream_departure_result.v1"] = (
        "deepbazi.dream_departure_result.v1"
    )
    departure_commit_id: str = Field(min_length=16, max_length=180)
    visit_id: str = Field(min_length=1, max_length=180)
    case_namespace: str = Field(min_length=1, max_length=240)
    commit_sequence: int = Field(ge=1)
    trigger: Literal["SPATIAL_BOUNDARY", "SEMANTIC_EXIT"]
    anchor: DreamDepartureAnchor
    waking_route: Literal["/experience"] = "/experience"
    idempotent_replay: bool = False


class DreamGuestAnchorMigrationResult(ExperienceModel):
    schema_version: Literal["deepbazi.dream_guest_anchor_migration_result.v1"] = (
        "deepbazi.dream_guest_anchor_migration_result.v1"
    )
    migrated: Literal[True] = True
    source_anchor_id: str = Field(min_length=16, max_length=180)
    target_anchor: DreamDepartureAnchor
    consumed_capability_hash: str = Field(min_length=64, max_length=64)


__all__ = [
    "DREAM_ABU_WORLD_STATE_VERSION",
    "DREAM_GEOMETRY_VERSION",
    "DREAM_RETURN_POLICY_VERSION",
    "DREAM_WORLD_SPACE_REF",
    "DREAM_WORLD_VERSION",
    "CanonicalAbuProjection",
    "DreamAnchorResolution",
    "DreamControlCredential",
    "DreamControlLease",
    "DreamControlLeaseProjection",
    "DreamDepartureAnchor",
    "DreamDepartureResult",
    "DreamGuestAnchorMigrationResult",
    "DreamNavigationSample",
    "DreamRecoveryCheckpoint",
    "DreamRuntimeState",
    "DreamWorldPosition",
    "DreamWorldProjectionBinding",
    "TreeObservationAnchor",
]
