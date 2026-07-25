from __future__ import annotations

from typing import Any, Literal

from pydantic import Field, model_validator

from core.contracts import FormalInsightLifecycleState
from experience.canvas import (
    CanvasContextPack,
    CanvasDiffSpec,
    CanvasRole,
    CanvasStage,
    MingliCanvasSpec,
)
from experience.canonical_scene import CanonicalProjectionEnvelope, CanonicalSceneIdentity
from experience.contracts import ExperienceModel, MingliExperienceEnvelope
from experience.narration import NarrationManifest, SpeechAsset
from experience.workspace import CaseWorkspaceEnvelope


CanvasLayer = Literal[
    "overview",
    "five_element",
    "combination_conflict",
    "roots_reveal",
    "timing",
    "work_path",
]
CanvasVisibilityLayer = Literal["formal", "focus", "lab_audit"]
CanvasSceneSlotState = Literal["active", "inactive", "not_loaded"]
PathProjectionRejectionReason = Literal[
    "none",
    "no_cognitive_path",
    "natural_language_only",
    "candidate_not_committed",
    "missing_path_ref",
    "invalid_node_ref",
    "invalid_relation_ref",
    "relation_still_potential",
    "authority_not_allowed",
    "role_visibility_filtered",
    "timing_scope_mismatch",
]
CanvasChangeType = Literal[
    "introduced",
    "removed",
    "activated",
    "reinforced",
    "weakened",
    "blocked",
    "reopened",
    "unchanged",
]


class ExperienceCaseSummary(ExperienceModel):
    case_id: str
    profile_id: str | None
    display_name: str
    case_version: str
    status: str
    baseline_available: bool
    chart_ready: bool = False
    cognition_status: Literal["ready", "preparing", "chart_ready", "partial"] = "chart_ready"
    experience_url: str


class WorkspaceAccountSummary(ExperienceModel):
    display_name: str
    role: str


class WorkspaceCognitionState(ExperienceModel):
    status: Literal["ready", "preparing", "chart_ready", "partial"]
    message: str
    cache_hit: bool
    background_start_allowed: bool
    background_job_id: str = ""
    insight: FormalInsightLifecycleState = Field(
        default_factory=FormalInsightLifecycleState,
    )
    llm_calls_started_by_bootstrap: Literal[0] = 0
    tts_calls_started_by_bootstrap: Literal[0] = 0


class WorkspaceBootstrapBudget(ExperienceModel):
    api_requests: Literal[1] = 1
    llm_calls: Literal[0] = 0
    tts_calls: Literal[0] = 0
    domain_generations: Literal[0] = 0


class ExperienceWorkspaceBootstrapResponse(ExperienceModel):
    status: Literal["workspace_bootstrap_ready", "workspace_profile_required"]
    account: WorkspaceAccountSummary
    cases: list[ExperienceCaseSummary]
    selected_case_id: str = ""
    selected_profile_id: str = ""
    envelope: MingliExperienceEnvelope | None = None
    workspace: CaseWorkspaceEnvelope | None = None
    cognition: WorkspaceCognitionState
    request_budget: WorkspaceBootstrapBudget = Field(default_factory=WorkspaceBootstrapBudget)
    cognition_source: Literal["LifeCase"] = "LifeCase"
    chart_source: Literal["ChartWorldInstance"] = "ChartWorldInstance"
    legacy_report_used: Literal[False] = False


class NarrationStatus(ExperienceModel):
    status: Literal["ready", "missing"]
    speech_asset_id: str
    audio_url: str
    audio_format: str


class NarrationManifestResponse(ExperienceModel):
    status: Literal["narration_manifest_ready"]
    manifest: NarrationManifest
    speech_assets: dict[str, NarrationStatus]
    tts_called: Literal[False]
    llm_used: Literal[False]
    reasoner_used: Literal[False]


class SpeechAssetResponse(ExperienceModel):
    status: Literal["speech_asset_ready"]
    speech_asset: SpeechAsset
    cache_hit: bool
    tts_called: bool
    llm_used: Literal[False]
    reasoner_used: Literal[False]


class CanvasLayerProjection(ExperienceModel):
    layer_id: CanvasLayer
    label: str
    description: str
    relation_refs: list[str]
    formal_relation_refs: list[str]
    path_refs: list[str]
    formal_path_refs: list[str]
    available: bool
    count: int = Field(ge=0)
    formal_count: int = Field(ge=0)


class CanvasSceneSlotProjection(ExperienceModel):
    position_index: int = Field(ge=0, le=5)
    slot_type: Literal[
        "natal_year",
        "natal_month",
        "natal_day",
        "natal_hour",
        "luck",
        "year",
    ]
    label: str
    state: CanvasSceneSlotState
    slot_ref: str
    stem_node_ref: str = ""
    branch_node_ref: str = ""
    stem: str = ""
    branch: str = ""
    hidden_stems: list[str] = Field(default_factory=list)
    immutable: bool


class CanvasChangeItem(ExperienceModel):
    target_ref: str
    object_type: str
    label: str
    before_state: str
    after_state: str
    reason_refs: list[str]


class CanvasChangeGroup(ExperienceModel):
    change_type: CanvasChangeType
    label: str
    count: int = Field(ge=0)
    items: list[CanvasChangeItem]


class CanvasStageProjection(ExperienceModel):
    stage: CanvasStage
    title: str
    summary: str
    spec: MingliCanvasSpec
    diff: CanvasDiffSpec | None
    context: CanvasContextPack
    scene_slots: list[CanvasSceneSlotProjection]
    layers: list[CanvasLayerProjection]
    default_layer_id: CanvasLayer
    change_groups: list[CanvasChangeGroup]


class ReadOnlyCanvasSource(ExperienceModel):
    chart_version_id: str
    life_case_id: str
    life_case_version: str
    cognitive_record_id: str
    luck_pillar: str
    luck_year_range: list[int]
    annual_pillar: str
    analysis_year: int | None
    timing_validation_status: str
    timing_publicly_supported: bool


class CanvasPathAvailability(ExperienceModel):
    status: Literal["available", "unavailable"]
    message: str
    committed_path_count: int = Field(ge=0)
    candidate_path_count: int = Field(ge=0)
    legacy_unresolved_count: int = Field(ge=0)
    disclosure_level: Literal["public", "professional", "audit"]
    professional_status: Literal[
        "confirmed",
        "not_confirmed",
        "natural_language_unstructured",
        "candidate_uncommitted",
        "reference_unresolved",
        "role_filtered",
        "not_available",
    ]
    diagnostic: "PathProjectionDiagnostic | None" = None


class PathProjectionDiagnostic(ExperienceModel):
    cognitive_path_present: bool
    structured_candidate_present: bool
    path_assertion_present: bool
    path_status: str
    node_refs_valid: bool
    relation_refs_valid: bool
    authority_status: str
    role_visible: bool
    projection_result: Literal["projected", "rejected", "not_available"]
    rejection_reason: PathProjectionRejectionReason


class CanvasRendererPolicy(ExperienceModel):
    read_only: Literal[True]
    available_visibility_layers: list[CanvasVisibilityLayer]
    default_visibility_layer: CanvasVisibilityLayer
    allowed_interactions: list[str]
    forbidden_interactions: list[str]


class ReadOnlySixPillarCanvas(ExperienceModel):
    schema_version: Literal["deepbazi.read_only_six_pillar_canvas.v1"]
    status: Literal["read_only_canvas_ready"]
    case_id: str
    role: CanvasRole
    stage_order: list[CanvasStage]
    default_stage: CanvasStage
    source: ReadOnlyCanvasSource
    canonical_scene: CanonicalSceneIdentity
    projection_envelope: CanonicalProjectionEnvelope
    path_availability: CanvasPathAvailability
    stages: dict[str, CanvasStageProjection]
    renderer_policy: CanvasRendererPolicy
    boundaries: list[str]
    llm_used: Literal[False]
    formal_state_writes: Literal[False]
    sandbox_mutations: Literal[False]

    @model_validator(mode="after")
    def validate_stage_projection(self) -> "ReadOnlySixPillarCanvas":
        if self.stage_order != ["natal", "luck", "year"]:
            raise ValueError("read_only_canvas_stage_order_invalid")
        if set(self.stages) != set(self.stage_order):
            raise ValueError("read_only_canvas_stage_projection_incomplete")
        if any(stage != projection.stage for stage, projection in self.stages.items()):
            raise ValueError("read_only_canvas_stage_identity_mismatch")
        return self


class CanvasContextResponse(ExperienceModel):
    status: Literal["canvas_context_ready"]
    context: CanvasContextPack
    llm_used: Literal[False]
    formal_state_writes: Literal[False]
