from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import Field, model_validator

from experience.contracts import ExperienceModel
from experience.dream_navigation import (
    CanonicalAbuProjection,
    DreamAnchorResolution,
    DreamControlLeaseProjection,
    DreamRuntimeState,
    DreamWorldProjectionBinding,
    TreeObservationAnchor,
)


DREAM_PROJECTION_VERSION = "deepbazi.dream_projection.v1"
DREAM_PRIVACY_POLICY_VERSION = "deepbazi.dream_privacy.v1"
DREAM_SELECTION_POLICY_VERSION = "deepbazi.dream_selection.v1"
DREAM_VISIBILITY_POLICY = "dream.member.read_only.v1"
DREAM_PILOT_CONSENT_VERSION = "deepbazi.dream_pilot_consent.v1"
DREAM_FIRST_VISIT_POLICY_VERSION = "deepbazi.dream_encounter_first_visit.v1"
DREAM_VERIFICATION_COORDINATE_VERSION = "canonical-six-pillar-twelve-node.v1"

DreamSceneSubjectKind = Literal[
    "authorized_human",
    "canonical_npc",
    "legacy_unclassified",
]
DreamSceneSourceLabelKey = Literal[
    "dream.source.authorized_human",
    "dream.source.canonical_npc",
    "dream.source.unclassified",
]
DreamRevealKind = Literal["path", "relation", "node", "none"]
DreamRevealVisualMode = Literal[
    "path_sequence",
    "relation_directional",
    "relation_sync",
    "local_node",
    "natural_contact_only",
]
DreamVerificationLens = Literal[
    "overview",
    "five_element",
    "combination_conflict",
    "roots_reveal",
    "timing",
    "work_path",
]
DreamVerificationStage = Literal["natal", "luck", "year"]


class DreamVisitState(str, Enum):
    HOME_GROVE = "HOME_GROVE"
    PATH_OFFERED = "PATH_OFFERED"
    DREAM_ENTERING = "DREAM_ENTERING"
    ENCOUNTER_READY = "ENCOUNTER_READY"
    TREE_SELECTED = "TREE_SELECTED"
    TREE_OBSERVING = "TREE_OBSERVING"
    MIRROR_OPEN = "MIRROR_OPEN"
    COMPLETED = "COMPLETED"


class DreamAuditEvent(ExperienceModel):
    event_code: Literal[
        "dream_visit_created",
        "dream_visit_resumed",
        "dream_entry_accepted",
        "dream_encounter_viewed",
        "dream_tree_selected",
        "dream_tree_selection_changed",
        "dream_tree_observed",
        "dream_tree_revealed",
        "dream_mirror_opened",
        "dream_mirror_closed",
        "dream_visit_completed",
        "dream_control_lease_acquired",
        "dream_control_lease_taken_over",
        "dream_anchor_resolved",
        "dream_recovery_checkpointed",
        "dream_visit_suspended",
        "dream_visit_recovered",
        "dream_departure_intent_started",
        "dream_departure_intent_cancelled",
        "dream_departure_commit_requested",
        "dream_departure_committed",
        "dream_guest_anchor_migrated",
        "dream_error",
    ]
    occurred_at: datetime


class DreamSceneEligibilitySnapshot(ExperienceModel):
    grant_ref: str = Field(min_length=1, max_length=180)
    public_scene_ref: str = Field(min_length=16, max_length=180)
    source_hash: str = Field(min_length=64, max_length=64)
    source_version: str = Field(min_length=16, max_length=128)
    authorization_version: str = Field(min_length=1, max_length=80)
    privacy_policy_version: str = Field(min_length=1, max_length=80)
    subject_kind: DreamSceneSubjectKind = "legacy_unclassified"
    subject_ref: str = Field(default="", max_length=180)


class EncounterSet(ExperienceModel):
    schema_version: Literal["deepbazi.dream_encounter_set.v1"] = (
        "deepbazi.dream_encounter_set.v1"
    )
    encounter_set_id: str = Field(min_length=1, max_length=180)
    visit_id: str = Field(min_length=1, max_length=180)
    scene_refs: list[str] = Field(min_length=3, max_length=3)
    selection_policy_version: str = Field(
        default=DREAM_SELECTION_POLICY_VERSION,
        min_length=1,
        max_length=80,
    )
    privacy_policy_version: str = Field(
        default=DREAM_PRIVACY_POLICY_VERSION,
        min_length=1,
        max_length=80,
    )
    eligibility_snapshot: list[DreamSceneEligibilitySnapshot] = Field(
        min_length=3,
        max_length=3,
    )
    created_at: datetime

    @model_validator(mode="after")
    def validate_three_distinct_scenes(self) -> "EncounterSet":
        if len(set(self.scene_refs)) != 3:
            raise ValueError("dream_encounter_requires_three_distinct_scenes")
        snapshot_refs = [item.public_scene_ref for item in self.eligibility_snapshot]
        if snapshot_refs != self.scene_refs:
            raise ValueError("dream_encounter_eligibility_snapshot_mismatch")
        return self


class DreamVisit(ExperienceModel):
    schema_version: Literal[
        "deepbazi.dream_visit.v1",
        "deepbazi.dream_visit.v2",
    ] = "deepbazi.dream_visit.v2"
    visit_id: str = Field(min_length=1, max_length=180)
    owner_user_id: str = Field(min_length=1, max_length=180)
    home_life_case_ref: str = Field(min_length=1, max_length=180)
    case_namespace: str = Field(default="", max_length=240)
    visit_sequence: int = Field(default=1, ge=1)
    is_return_visit: bool = False
    runtime_state: DreamRuntimeState = DreamRuntimeState.FIRST_VISIT
    world_projection: DreamWorldProjectionBinding | None = None
    anchor_resolution: DreamAnchorResolution | None = None
    tree_observation_anchor: TreeObservationAnchor | None = None
    recovery_checkpoint_ref: str = Field(default="", max_length=180)
    departure_anchor_ref: str = Field(default="", max_length=180)
    control_lease_ref: str = Field(default="", max_length=180)
    recovery_sequence: int = Field(default=0, ge=0)
    departure_commit_sequence: int = Field(default=0, ge=0)
    state: DreamVisitState = DreamVisitState.HOME_GROVE
    encounter_set: EncounterSet
    selected_scene_ref: str = Field(default="", max_length=180)
    prepared_onecanvas_view_ref: str = Field(default="", max_length=180)
    active_onecanvas_view_ref: str = Field(default="", max_length=180)
    active_verification_state: Literal["none", "focused", "quiet_overview"] = "none"
    last_committed_state: DreamVisitState = DreamVisitState.HOME_GROVE
    projection_version: str = Field(
        default=DREAM_PROJECTION_VERSION,
        min_length=1,
        max_length=100,
    )
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None = None
    row_version: int = Field(default=1, ge=1)
    audit_events: list[DreamAuditEvent] = Field(default_factory=list, max_length=128)

    @model_validator(mode="after")
    def validate_visit_identity(self) -> "DreamVisit":
        if self.encounter_set.visit_id != self.visit_id:
            raise ValueError("dream_visit_encounter_identity_mismatch")
        if self.selected_scene_ref and self.selected_scene_ref not in self.encounter_set.scene_refs:
            raise ValueError("dream_selected_scene_not_in_encounter")
        if self.state in {
            DreamVisitState.TREE_SELECTED,
            DreamVisitState.TREE_OBSERVING,
            DreamVisitState.MIRROR_OPEN,
        } and not self.selected_scene_ref:
            raise ValueError("dream_selected_scene_required_for_state")
        if self.case_namespace and not self.case_namespace.startswith("life-case:"):
            raise ValueError("dream_case_namespace_invalid")
        if self.world_projection is not None and self.case_namespace and (
            self.world_projection.case_namespace != self.case_namespace
            or self.world_projection.viewer_id != self.owner_user_id
        ):
            raise ValueError("dream_world_projection_visit_binding_mismatch")
        return self


class DreamSceneGrant(ExperienceModel):
    schema_version: Literal["deepbazi.dream_scene_grant.v1"] = (
        "deepbazi.dream_scene_grant.v1"
    )
    grant_id: str = Field(min_length=1, max_length=180)
    case_id: str = Field(min_length=1, max_length=180)
    public_scene_ref: str = Field(min_length=16, max_length=180)
    purpose: Literal["dream_bridge_v1"] = "dream_bridge_v1"
    status: Literal["active", "withdrawn", "expired"] = "active"
    authorization_basis: str = Field(min_length=1, max_length=240)
    authorized_by_ref: str = Field(min_length=1, max_length=180)
    authorization_version: str = Field(min_length=1, max_length=80)
    authorization_sequence: int = Field(default=1, ge=1)
    subject_kind: DreamSceneSubjectKind = "legacy_unclassified"
    subject_ref: str = Field(default="", max_length=180)
    anonymization_policy_version: str = Field(
        default=DREAM_PRIVACY_POLICY_VERSION,
        min_length=1,
        max_length=80,
    )
    authorized_source_hash: str = Field(min_length=64, max_length=64)
    valid_from: datetime
    valid_until: datetime | None = None
    withdrawn_at: datetime | None = None
    revocable: Literal[True] = True
    created_at: datetime
    updated_at: datetime

    def is_active_at(self, value: datetime) -> bool:
        return (
            self.status == "active"
            and self.withdrawn_at is None
            and self.valid_from <= value
            and (self.valid_until is None or value < self.valid_until)
        )


class DreamFeatureStatus(ExperienceModel):
    schema_version: Literal["deepbazi.dream_feature_status.v1"] = (
        "deepbazi.dream_feature_status.v1"
    )
    enabled: bool
    available: bool
    resumable: bool
    eligible_scene_count: int = Field(ge=0)
    reason_code: str = Field(min_length=1, max_length=100)
    consent_state: Literal[
        "not_granted",
        "active",
        "withdrawn",
        "source_changed",
        "case_unavailable",
    ] = "not_granted"
    human_scene_eligible: bool = False
    canonical_npc_scene_count: int = Field(default=0, ge=0, le=2)
    composition_ready: bool = False
    projection_version: str = DREAM_PROJECTION_VERSION


class DreamConsentStatus(ExperienceModel):
    schema_version: Literal["deepbazi.dream_consent_status.v1"] = (
        "deepbazi.dream_consent_status.v1"
    )
    case_id: str = Field(min_length=1, max_length=180)
    state: Literal[
        "not_granted",
        "active",
        "withdrawn",
        "source_changed",
        "case_unavailable",
    ]
    consent_version: Literal[DREAM_PILOT_CONSENT_VERSION] = DREAM_PILOT_CONSENT_VERSION
    can_grant: bool
    can_withdraw: bool
    revocable: Literal[True] = True


class DreamVisitView(ExperienceModel):
    visit_id: str = Field(min_length=1, max_length=180)
    state: DreamVisitState
    selected_scene_ref: str = Field(default="", max_length=180)
    prepared_onecanvas_view_ref: str = Field(default="", max_length=180)
    active_onecanvas_view_ref: str = Field(default="", max_length=180)
    case_namespace: str = Field(default="", max_length=240)
    runtime_state: DreamRuntimeState = DreamRuntimeState.FIRST_VISIT
    is_return_visit: bool = False
    control_lease: DreamControlLeaseProjection | None = None
    anchor_resolution: DreamAnchorResolution | None = None
    world_projection_ref: str = Field(default="", max_length=180)
    canonical_abu: CanonicalAbuProjection | None = None
    recovery_sequence: int = Field(default=0, ge=0)
    departure_commit_sequence: int = Field(default=0, ge=0)
    allowed_actions: list[str] = Field(default_factory=list)
    projection_version: str = DREAM_PROJECTION_VERSION
    updated_at: datetime


class DreamTreeCard(ExperienceModel):
    scene_ref: str = Field(min_length=16, max_length=180)
    art_variant: Literal["mist", "brook", "ridge"]
    primary_element: Literal["wood", "fire", "earth", "metal", "water", "unknown"]
    climate_token: Literal["quiet", "luck_present", "year_present"]
    relation_tokens: list[
        Literal["relation_stable", "relation_awakened", "relation_effective"]
    ] = Field(default_factory=list)
    source_version: str = Field(min_length=16, max_length=128)
    source_kind: Literal["authorized_human", "canonical_npc"]
    source_label_key: DreamSceneSourceLabelKey
    resident_label: str = Field(min_length=1, max_length=80)
    autonomous_phase_ms: int = Field(ge=0, lt=60000)
    allowed_actions: list[Literal["select_tree"]] = Field(default_factory=lambda: ["select_tree"])


class DreamEncounterProjection(ExperienceModel):
    schema_version: Literal["deepbazi.dream_encounter_projection.v1"] = (
        "deepbazi.dream_encounter_projection.v1"
    )
    projection_version: str = DREAM_PROJECTION_VERSION
    projection_id: str = Field(min_length=16, max_length=180)
    visibility_policy: Literal["dream.member.read_only.v1"] = DREAM_VISIBILITY_POLICY
    state: Literal[DreamVisitState.ENCOUNTER_READY] = DreamVisitState.ENCOUNTER_READY
    trees: list[DreamTreeCard] = Field(min_length=3, max_length=3)
    allowed_actions: list[Literal["select_tree"]] = Field(default_factory=lambda: ["select_tree"])
    content_hash: str = Field(min_length=64, max_length=64)


class DreamTreeProjection(ExperienceModel):
    schema_version: Literal["deepbazi.dream_tree_projection.v1"] = (
        "deepbazi.dream_tree_projection.v1"
    )
    projection_version: str = DREAM_PROJECTION_VERSION
    projection_id: str = Field(min_length=16, max_length=180)
    source_refs: list[str] = Field(min_length=1, max_length=1)
    source_versions: dict[str, str]
    source_kind: Literal["authorized_human", "canonical_npc"]
    source_label_key: DreamSceneSourceLabelKey
    visibility_policy: Literal["dream.member.read_only.v1"] = DREAM_VISIBILITY_POLICY
    state: Literal[DreamVisitState.TREE_OBSERVING] = DreamVisitState.TREE_OBSERVING
    visual_tokens: dict[str, Any]
    relation_tokens: list[
        Literal["relation_stable", "relation_awakened", "relation_effective"]
    ] = Field(default_factory=list)
    work_path_state: Literal["unavailable_unconfirmed", "none_confirmed", "available"]
    work_path_message_key: Literal["dream.path.none_confirmed"] = "dream.path.none_confirmed"
    allowed_actions: list[Literal["open_mirror", "return_to_encounter"]] = Field(
        default_factory=lambda: ["open_mirror", "return_to_encounter"]
    )
    content_hash: str = Field(min_length=64, max_length=64)


class DreamRevealProjection(ExperienceModel):
    schema_version: Literal["deepbazi.dream_reveal_projection.v1"] = (
        "deepbazi.dream_reveal_projection.v1"
    )
    projection_version: str = DREAM_PROJECTION_VERSION
    public_scene_ref: str = Field(min_length=16, max_length=180)
    source_version: str = Field(min_length=16, max_length=128)
    source_kind: Literal["authorized_human", "canonical_npc"]
    revealable_assertion_ref: str = Field(default="", max_length=240)
    reveal_kind: DreamRevealKind
    visual_mode: DreamRevealVisualMode
    authorized_statement: str = Field(default="", max_length=500)
    onecanvas_view_ref: str = Field(min_length=32, max_length=180)
    target_stage: DreamVerificationStage
    target_lens: DreamVerificationLens
    content_hash: str = Field(min_length=64, max_length=64)

    @model_validator(mode="after")
    def validate_reveal(self) -> "DreamRevealProjection":
        if self.reveal_kind == "none":
            if self.revealable_assertion_ref or self.visual_mode != "natural_contact_only":
                raise ValueError("dream_empty_reveal_contract_invalid")
        elif not self.revealable_assertion_ref:
            raise ValueError("dream_reveal_ref_required")
        return self


class DreamVerificationBinding(ExperienceModel):
    dream_projection_version: str = Field(min_length=1, max_length=100)
    source_version: str = Field(min_length=16, max_length=128)
    assertion_version: str = Field(min_length=16, max_length=128)
    life_case_version: str = Field(min_length=16, max_length=128)
    coordinate_version: Literal[DREAM_VERIFICATION_COORDINATE_VERSION] = (
        DREAM_VERIFICATION_COORDINATE_VERSION
    )
    target_stage: DreamVerificationStage
    target_lens: DreamVerificationLens


class DreamVerificationProjection(ExperienceModel):
    schema_version: Literal["deepbazi.dream_verification_projection.v1"] = (
        "deepbazi.dream_verification_projection.v1"
    )
    state: Literal["focused", "quiet_overview"]
    onecanvas_view_ref: str = Field(min_length=32, max_length=180)
    revealable_assertion_ref: str = Field(default="", max_length=240)
    reveal_kind: DreamRevealKind
    target_object_ref: str = Field(default="", max_length=260)
    verification_copy: Literal["刚才树中显露的，是命盘里的这一处。"] = (
        "刚才树中显露的，是命盘里的这一处。"
    )
    authorized_statement: str = Field(default="", max_length=500)
    binding: DreamVerificationBinding

    @model_validator(mode="after")
    def validate_verification(self) -> "DreamVerificationProjection":
        if self.state == "focused" and (
            self.reveal_kind == "none"
            or not self.revealable_assertion_ref
            or not self.target_object_ref
        ):
            raise ValueError("dream_focused_verification_requires_exact_target")
        if self.state == "quiet_overview" and self.target_object_ref:
            raise ValueError("dream_quiet_overview_cannot_select_target")
        return self


class DreamMirrorProjection(ExperienceModel):
    schema_version: Literal["deepbazi.dream_mirror_projection.v1"] = (
        "deepbazi.dream_mirror_projection.v1"
    )
    projection_version: str = DREAM_PROJECTION_VERSION
    public_scene_ref: str = Field(min_length=16, max_length=180)
    source_version: str = Field(min_length=16, max_length=128)
    source_kind: Literal["authorized_human", "canonical_npc"]
    source_label_key: DreamSceneSourceLabelKey
    work_path_state: Literal["unavailable_unconfirmed", "none_confirmed", "available"]
    work_path_message_key: Literal["dream.path.none_confirmed"] = "dream.path.none_confirmed"
    verification: DreamVerificationProjection
    canvas: dict[str, Any]
    content_hash: str = Field(min_length=64, max_length=64)


_ALLOWED_TRANSITIONS: dict[DreamVisitState, set[DreamVisitState]] = {
    DreamVisitState.HOME_GROVE: {DreamVisitState.PATH_OFFERED, DreamVisitState.COMPLETED},
    DreamVisitState.PATH_OFFERED: {DreamVisitState.DREAM_ENTERING, DreamVisitState.COMPLETED},
    DreamVisitState.DREAM_ENTERING: {DreamVisitState.ENCOUNTER_READY, DreamVisitState.COMPLETED},
    DreamVisitState.ENCOUNTER_READY: {DreamVisitState.TREE_SELECTED, DreamVisitState.COMPLETED},
    DreamVisitState.TREE_SELECTED: {DreamVisitState.TREE_OBSERVING, DreamVisitState.COMPLETED},
    DreamVisitState.TREE_OBSERVING: {
        DreamVisitState.MIRROR_OPEN,
        DreamVisitState.COMPLETED,
    },
    DreamVisitState.MIRROR_OPEN: {
        DreamVisitState.TREE_OBSERVING,
        DreamVisitState.COMPLETED,
    },
    DreamVisitState.COMPLETED: set(),
}


def transition_visit(visit: DreamVisit, target: DreamVisitState, *, at: datetime) -> DreamVisit:
    if target == visit.state:
        return visit
    if target not in _ALLOWED_TRANSITIONS[visit.state]:
        raise ValueError(f"dream_transition_not_allowed:{visit.state.value}:{target.value}")
    return visit.model_copy(update={
        "state": target,
        "last_committed_state": target,
        "updated_at": at,
        "completed_at": at if target == DreamVisitState.COMPLETED else visit.completed_at,
        "row_version": visit.row_version + 1,
    })


def visit_view(
    visit: DreamVisit,
    *,
    control_lease: DreamControlLeaseProjection | None = None,
    canonical_abu: CanonicalAbuProjection | None = None,
) -> DreamVisitView:
    actions = {
        DreamVisitState.HOME_GROVE: ["enter"],
        DreamVisitState.PATH_OFFERED: ["enter"],
        DreamVisitState.DREAM_ENTERING: ["enter"],
        DreamVisitState.ENCOUNTER_READY: ["view_encounter", "select_tree"],
        DreamVisitState.TREE_SELECTED: ["observe_tree"],
        DreamVisitState.TREE_OBSERVING: ["observe_tree", "open_mirror"],
        DreamVisitState.MIRROR_OPEN: ["observe_tree", "close_mirror"],
        DreamVisitState.COMPLETED: [],
    }[visit.state]
    return DreamVisitView(
        visit_id=visit.visit_id,
        state=visit.state,
        selected_scene_ref=visit.selected_scene_ref,
        prepared_onecanvas_view_ref=visit.prepared_onecanvas_view_ref,
        active_onecanvas_view_ref=visit.active_onecanvas_view_ref,
        case_namespace=visit.case_namespace,
        runtime_state=visit.runtime_state,
        is_return_visit=visit.is_return_visit,
        control_lease=control_lease,
        anchor_resolution=visit.anchor_resolution,
        world_projection_ref=(
            visit.world_projection.world_projection_ref
            if visit.world_projection is not None
            else ""
        ),
        canonical_abu=canonical_abu,
        recovery_sequence=visit.recovery_sequence,
        departure_commit_sequence=visit.departure_commit_sequence,
        allowed_actions=actions,
        projection_version=visit.projection_version,
        updated_at=visit.updated_at,
    )


__all__ = [
    "DREAM_PRIVACY_POLICY_VERSION",
    "DREAM_PILOT_CONSENT_VERSION",
    "DREAM_FIRST_VISIT_POLICY_VERSION",
    "DREAM_PROJECTION_VERSION",
    "DREAM_SELECTION_POLICY_VERSION",
    "DREAM_VISIBILITY_POLICY",
    "DREAM_VERIFICATION_COORDINATE_VERSION",
    "DreamAuditEvent",
    "DreamConsentStatus",
    "DreamEncounterProjection",
    "DreamFeatureStatus",
    "DreamMirrorProjection",
    "DreamRevealProjection",
    "DreamSceneEligibilitySnapshot",
    "DreamSceneGrant",
    "DreamTreeCard",
    "DreamTreeProjection",
    "DreamVerificationBinding",
    "DreamVerificationProjection",
    "DreamVisit",
    "DreamVisitState",
    "DreamVisitView",
    "EncounterSet",
    "transition_visit",
    "visit_view",
]
