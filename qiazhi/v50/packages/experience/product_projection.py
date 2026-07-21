from __future__ import annotations

from typing import Any, Literal

from pydantic import Field, model_validator

from experience.canvas import (
    CanvasContextPack,
    CanvasDiffSpec,
    CanvasRole,
    CanvasStage,
    MingliCanvasSpec,
)
from experience.canonical_scene import CanonicalProjectionEnvelope, CanonicalSceneIdentity
from experience.contracts import ExperienceModel
from experience.narration import NarrationManifest, SpeechAsset


CanvasLayer = Literal["generation_control", "combination", "conflict", "work_path"]
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
    experience_url: str


class ExperienceCasesResponse(ExperienceModel):
    status: Literal["experience_cases_ready"]
    cases: list[ExperienceCaseSummary]
    cognition_source: Literal["LifeCase"]
    legacy_report_used: Literal[False]


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
    available: bool
    count: int = Field(ge=0)


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


class CanvasRendererPolicy(ExperienceModel):
    read_only: Literal[True]
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
