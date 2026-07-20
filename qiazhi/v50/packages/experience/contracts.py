from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


ExperienceMode = Literal["live", "time_shift", "solo", "replay"]
EnvelopeMode = Literal["personal_ready", "chart_facts_only", "observer"]
Visibility = Literal["public", "participant_private", "operator"]


class ExperienceModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class ParticipantScope(ExperienceModel):
    participant_ref: str = Field(min_length=1, max_length=160)
    privacy_level: Literal["anonymous", "account", "client_case"] = "anonymous"
    disclosure_level: Literal["observer", "chart_facts", "approved_insights"] = "observer"
    language: str = Field(default="zh-CN", min_length=2, max_length=20)


class EnvelopeSource(ExperienceModel):
    chart_version: str = Field(min_length=1, max_length=160)
    life_case_version: str | None = Field(default=None, max_length=160)
    case_ref: str | None = Field(default=None, max_length=180)
    temporal_snapshot_version: str | None = Field(default=None, max_length=160)
    generated_at: datetime
    expires_at: datetime
    source_hash: str = Field(min_length=32, max_length=128)

    @model_validator(mode="after")
    def validate_expiry(self) -> "EnvelopeSource":
        if self.expires_at <= self.generated_at:
            raise ValueError("envelope_expires_at_must_follow_generated_at")
        return self


class TopicScope(ExperienceModel):
    topic_id: str = Field(min_length=1, max_length=120)
    topic_version: str = Field(min_length=1, max_length=80)
    permitted_capabilities: list[str] = Field(default_factory=list)
    prohibited_capabilities: list[str] = Field(default_factory=list)


class HiddenStemFact(ExperienceModel):
    stem: str = Field(min_length=1, max_length=4)
    ten_god: str = Field(default="", max_length=40)
    element: Literal["wood", "fire", "earth", "metal", "water", ""] = ""
    polarity: Literal["yin", "yang", ""] = ""


class AllowedChartFact(ExperienceModel):
    fact_ref: str = Field(min_length=1, max_length=180)
    fact_type: str = Field(min_length=1, max_length=80)
    display_value: str = Field(min_length=1, max_length=300)
    visual_anchor: str = Field(default="", max_length=120)
    visibility: Literal["participant_private"] = "participant_private"
    pillar_slot: Literal["year", "month", "day", "hour", ""] = ""
    pillar_label: str = Field(default="", max_length=20)
    stem: str = Field(default="", max_length=4)
    branch: str = Field(default="", max_length=4)
    stem_element: Literal["wood", "fire", "earth", "metal", "water", ""] = ""
    stem_polarity: Literal["yin", "yang", ""] = ""
    branch_element: Literal["wood", "fire", "earth", "metal", "water", ""] = ""
    branch_polarity: Literal["yin", "yang", ""] = ""
    visible_ten_god: str = Field(default="", max_length=40)
    hidden_stems: list[HiddenStemFact] = Field(default_factory=list)


class ApprovedClaim(ExperienceModel):
    claim_ref: str = Field(min_length=1, max_length=180)
    category: str = Field(min_length=1, max_length=100)
    approved_meaning: str = Field(min_length=1, max_length=1200)
    spoken_summary: str = Field(default="", max_length=1200)
    subtitle_summary: str = Field(default="", max_length=1200)
    certainty: Literal["low", "medium", "high"]
    conditions: list[str] = Field(default_factory=list)
    counter_signals: list[str] = Field(default_factory=list)
    temporal_scope: str = Field(default="natal", max_length=120)
    evidence_refs: list[str] = Field(default_factory=list)
    visual_anchors: list[str] = Field(default_factory=list)
    permitted_uses: list[str] = Field(default_factory=lambda: ["private_dialogue", "private_subtitle"])


class ApprovedReasoningStep(ExperienceModel):
    step_ref: str = Field(min_length=1, max_length=180)
    premise: str = Field(min_length=1, max_length=1200)
    conclusion: str = Field(min_length=1, max_length=1200)
    source_refs: list[str] = Field(default_factory=list)
    visual_anchor: str = Field(min_length=1, max_length=120)


class CompetingHypothesis(ExperienceModel):
    hypothesis_ref: str = Field(min_length=1, max_length=180)
    approved_meaning: str = Field(min_length=1, max_length=1000)
    supporting_refs: list[str] = Field(default_factory=list)
    unresolved_reason: str = Field(default="", max_length=600)


class EnvelopeUncertainty(ExperienceModel):
    level: Literal["low", "medium", "high"] = "high"
    reasons: list[str] = Field(default_factory=list)


class EnvelopeFallback(ExperienceModel):
    mode: Literal["chart_facts_only", "observer"]
    allowed_content: list[str] = Field(default_factory=list)


class MingliExperienceEnvelope(ExperienceModel):
    envelope_id: str = Field(min_length=1, max_length=180)
    schema_version: Literal["deepbazi.mingli_experience_envelope.v1"] = (
        "deepbazi.mingli_experience_envelope.v1"
    )
    mode: EnvelopeMode
    participant_scope: ParticipantScope
    source: EnvelopeSource
    topic_scope: TopicScope
    allowed_chart_facts: list[AllowedChartFact] = Field(default_factory=list)
    approved_claims: list[ApprovedClaim] = Field(default_factory=list)
    approved_reasoning_steps: list[ApprovedReasoningStep] = Field(default_factory=list)
    competing_hypotheses: list[CompetingHypothesis] = Field(default_factory=list)
    uncertainty: EnvelopeUncertainty = Field(default_factory=EnvelopeUncertainty)
    must_not_say: list[str] = Field(default_factory=list)
    fallback: EnvelopeFallback

    @model_validator(mode="after")
    def validate_mode_disclosure(self) -> "MingliExperienceEnvelope":
        if self.mode == "personal_ready":
            if not self.source.life_case_version or not self.approved_claims:
                raise ValueError("personal_ready_requires_life_case_and_approved_claim")
            if self.participant_scope.disclosure_level != "approved_insights":
                raise ValueError("personal_ready_requires_approved_insights_disclosure")
        elif self.mode == "chart_facts_only":
            if not self.allowed_chart_facts:
                raise ValueError("chart_facts_only_requires_chart_facts")
            if self.approved_claims or self.approved_reasoning_steps or self.competing_hypotheses:
                raise ValueError("chart_facts_only_cannot_disclose_claims")
        elif (
            self.allowed_chart_facts
            or self.approved_claims
            or self.approved_reasoning_steps
            or self.competing_hypotheses
        ):
            raise ValueError("observer_envelope_cannot_disclose_case_content")
        return self


class TopicMetadata(ExperienceModel):
    topic_id: str = Field(min_length=1, max_length=120)
    version: str = Field(min_length=1, max_length=80)
    title: str = Field(min_length=1, max_length=160)
    purpose: str = Field(min_length=1, max_length=500)
    audience: list[str] = Field(default_factory=list)
    supported_modes: list[ExperienceMode] = Field(min_length=1)
    required_experience_capabilities: list[str] = Field(default_factory=list)
    knowledge_refs: list[str] = Field(default_factory=list)


class SceneTransition(ExperienceModel):
    event: str = Field(min_length=1, max_length=100)
    target: str = Field(min_length=1, max_length=120)


class SceneInteraction(ExperienceModel):
    kind: Literal["none", "choice", "text", "capsule", "ready_barrier", "mingli_experiment"] = "none"
    prompt: str = Field(default="", max_length=500)
    options: list[str] = Field(default_factory=list)
    required: bool = False


class SceneNode(ExperienceModel):
    node_id: str = Field(min_length=1, max_length=120)
    act: str = Field(min_length=1, max_length=80)
    dramatic_purpose: str = Field(min_length=1, max_length=400)
    visibility: Literal["public", "participant_private"]
    expected_duration_seconds: int = Field(default=20, ge=0, le=3600)
    cue_template_ids: list[str] = Field(default_factory=list)
    interaction: SceneInteraction = Field(default_factory=SceneInteraction)
    data_bindings: list[str] = Field(default_factory=list)
    transitions: list[SceneTransition] = Field(default_factory=list)
    timeout_behavior: Literal["wait", "advance", "fallback"] = "wait"
    fallback_node: str | None = None
    rejoin_node: str | None = None


class ActorCue(ExperienceModel):
    expression: str = Field(default="attentive", max_length=80)
    motion_asset: str = Field(default="", max_length=180)
    loop: bool = False


class StageCommand(ExperienceModel):
    command: Literal[
        "set_background",
        "highlight_visual_anchor",
        "show_chart_facts",
        "show_group_trace",
        "show_capsule",
        "clear_stage",
    ]
    source: str = Field(default="", max_length=240)
    asset_ref: str = Field(default="", max_length=180)


class VoiceCue(ExperienceModel):
    profile: str = Field(default="abu-main", max_length=100)
    mode: str = Field(default="companion", max_length=80)
    emotion: str = Field(default="calm", max_length=80)
    speed: float = Field(default=1.0, ge=0.5, le=1.5)
    audio_asset: str = Field(default="", max_length=180)


class SubtitleCue(ExperienceModel):
    style: str = Field(default="default", max_length=80)


class CueTemplate(ExperienceModel):
    template_id: str = Field(min_length=1, max_length=160)
    visibility: Literal["public", "participant_private"]
    semantic_intent: str = Field(min_length=1, max_length=120)
    required_claim_category: str = Field(default="", max_length=100)
    dialogue_template: str = Field(min_length=1, max_length=2400)
    subtitle_template: str = Field(min_length=1, max_length=2400)
    phrase_policy: str = Field(default="cautious_professional", max_length=100)
    voice: VoiceCue = Field(default_factory=VoiceCue)
    actor: ActorCue = Field(default_factory=ActorCue)
    stage: list[StageCommand] = Field(default_factory=list)
    subtitle: SubtitleCue = Field(default_factory=SubtitleCue)
    fallback_template_id: str | None = None


class DirectorScript(ExperienceModel):
    temporary_dialogue: dict[str, str] = Field(default_factory=dict)
    timing_notes: dict[str, str] = Field(default_factory=dict)


class AssetDefinition(ExperienceModel):
    asset_id: str = Field(min_length=1, max_length=180)
    kind: Literal["abu_motion", "background", "graph", "music", "sound", "image"]
    uri: str = Field(min_length=1, max_length=500)
    fallback_asset_id: str | None = None


class AssetManifest(ExperienceModel):
    assets: list[AssetDefinition] = Field(default_factory=list)


class TopicPolicies(ExperienceModel):
    privacy: str = Field(default="private_by_default", max_length=120)
    aggregation_minimum: int = Field(default=3, ge=2, le=100)
    personal_scene: str = Field(default="envelope_only", max_length=120)
    temporal_message: str = Field(default="explicit_consent", max_length=120)
    failure_behavior: str = Field(default="fallback_without_invention", max_length=160)


class TopicRelease(ExperienceModel):
    status: Literal["draft", "compiled", "approved"] = "draft"
    approved_by: str = Field(default="", max_length=160)
    package_hash: str = Field(default="", max_length=128)


class TopicPackage(ExperienceModel):
    schema_version: Literal["deepbazi.topic_package.v1"] = "deepbazi.topic_package.v1"
    topic: TopicMetadata
    entry_node: str = Field(min_length=1, max_length=120)
    fallback_entry_nodes: dict[EnvelopeMode, str]
    scene_nodes: list[SceneNode] = Field(min_length=1)
    cue_templates: list[CueTemplate] = Field(min_length=1)
    director_script: DirectorScript = Field(default_factory=DirectorScript)
    asset_manifest: AssetManifest = Field(default_factory=AssetManifest)
    policies: TopicPolicies = Field(default_factory=TopicPolicies)
    release: TopicRelease = Field(default_factory=TopicRelease)


class CompiledTopic(ExperienceModel):
    schema_version: Literal["deepbazi.compiled_topic.v1"] = "deepbazi.compiled_topic.v1"
    topic: TopicMetadata
    entry_node: str
    fallback_entry_nodes: dict[EnvelopeMode, str]
    scene_nodes: dict[str, SceneNode]
    cue_templates: dict[str, CueTemplate]
    assets: dict[str, AssetDefinition]
    policies: TopicPolicies
    source_hash: str
    content_hash: str
    compiled_at: datetime


class FinalActorCommand(ExperienceModel):
    expression: str
    motion_asset: str = ""
    loop: bool = False


class PerformanceCueInstance(ExperienceModel):
    schema_version: Literal["deepbazi.performance_cue_instance.v1"] = (
        "deepbazi.performance_cue_instance.v1"
    )
    cue_instance_id: str
    template_id: str
    participant_run_id: str | None = None
    visibility: Literal["public", "participant_private"]
    final_dialogue: str
    final_ssml: str = ""
    final_subtitle: str
    subtitle_timing: list[dict[str, Any]] = Field(default_factory=list)
    final_actor_commands: list[FinalActorCommand] = Field(default_factory=list)
    final_stage_commands: list[StageCommand] = Field(default_factory=list)
    final_audio_asset: str = ""
    claim_refs: list[str] = Field(default_factory=list)
    envelope_id: str | None = None
    envelope_hash: str | None = None
    generator_version: str = "deterministic-cue-renderer.v1"
    model_version: str = "none"
    phrase_policy_version: str = "cautious_professional.v1"
    review_status: Literal["validated", "rejected"] = "validated"
    frozen_at: datetime
    cue_hash: str


class PerformanceAudioTrack(ExperienceModel):
    uri: str = Field(min_length=1, max_length=500)
    sha256: str = Field(min_length=64, max_length=64)
    duration_ms: int = Field(gt=0, le=600_000)
    sample_rate: int = Field(gt=0, le=192_000)
    speech_start_ms: int = Field(default=0, ge=0)
    voice_id: str = Field(min_length=1, max_length=100)
    voice_version: str = Field(min_length=1, max_length=180)


class SubtitleTrackItem(ExperienceModel):
    start_ms: int = Field(ge=0)
    end_ms: int = Field(gt=0)
    text: str = Field(min_length=1, max_length=1200)
    claim_refs: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_timing(self) -> "SubtitleTrackItem":
        if self.end_ms <= self.start_ms:
            raise ValueError("subtitle_end_must_follow_start")
        return self


class VisemeTrackItem(ExperienceModel):
    at_ms: int = Field(ge=0)
    shape: Literal["closed", "small", "wide"]
    openness: float = Field(ge=0.0, le=1.0)
    source: Literal["audio_rms"] = "audio_rms"


class ActorTrackItem(ExperienceModel):
    at_ms: int = Field(ge=0)
    action: Literal[
        "enter",
        "speak",
        "push_report",
        "point_chart",
        "point_path",
        "serious",
        "listen",
    ]
    expression: str = Field(default="attentive", max_length=80)
    target: str = Field(default="", max_length=120)


class PerformanceStageTrackItem(ExperienceModel):
    at_ms: int = Field(ge=0)
    action: Literal[
        "reset",
        "reveal_chart_fact",
        "reveal_reasoning_step",
        "highlight_approved_path",
        "show_unresolved_condition",
    ]
    target_ref: str = Field(default="", max_length=180)
    visual_anchor: str = Field(default="", max_length=120)


class CameraTrackItem(ExperienceModel):
    at_ms: int = Field(ge=0)
    framing: Literal["wide", "actor", "chart", "path", "choice"]


class PerformanceStageSnapshot(ExperienceModel):
    chart_facts: list[AllowedChartFact] = Field(default_factory=list)
    approved_claim: ApprovedClaim | None = None
    reasoning_steps: list[ApprovedReasoningStep] = Field(default_factory=list)
    unresolved_text: str = Field(default="", max_length=1200)
    unresolved_refs: list[str] = Field(default_factory=list)


class PerformancePackage(ExperienceModel):
    schema_version: Literal["deepbazi.performance_package.v1"] = "deepbazi.performance_package.v1"
    package_id: str = Field(min_length=1, max_length=180)
    cue_instance_id: str = Field(min_length=1, max_length=180)
    participant_run_id: str | None = Field(default=None, max_length=180)
    visibility: Literal["public", "participant_private"]
    dialogue: str = Field(min_length=1, max_length=6000)
    audio: PerformanceAudioTrack
    subtitle_track: list[SubtitleTrackItem] = Field(min_length=1)
    viseme_track: list[VisemeTrackItem] = Field(default_factory=list)
    actor_track: list[ActorTrackItem] = Field(default_factory=list)
    stage_track: list[PerformanceStageTrackItem] = Field(default_factory=list)
    camera_track: list[CameraTrackItem] = Field(default_factory=list)
    music_track: list[dict[str, Any]] = Field(default_factory=list)
    stage_snapshot: PerformanceStageSnapshot = Field(default_factory=PerformanceStageSnapshot)
    actor_renderer_contract_version: str = "abu-actor-renderer.v1"
    actor_asset_version: str = Field(default="webp-fallback.v1", max_length=180)
    envelope_id: str | None = Field(default=None, max_length=180)
    envelope_hash: str | None = Field(default=None, max_length=128)
    claim_refs: list[str] = Field(default_factory=list)
    cue_hash: str = Field(min_length=32, max_length=128)
    frozen_at: datetime
    package_hash: str = Field(min_length=32, max_length=128)


class TheaterSession(ExperienceModel):
    schema_version: Literal["deepbazi.theater_session.v1"] = "deepbazi.theater_session.v1"
    session_id: str
    topic_id: str
    topic_version: str
    topic_hash: str
    mode: ExperienceMode
    status: Literal["lobby", "running", "paused", "completed", "cancelled"] = "lobby"
    current_public_node_id: str
    active_private_node_id: str | None = None
    last_private_node_id: str | None = None
    sequence: int = 0
    participant_count: int = 0
    created_at: datetime
    updated_at: datetime


class ParticipantRun(ExperienceModel):
    schema_version: Literal["deepbazi.participant_run.v1"] = "deepbazi.participant_run.v1"
    participant_run_id: str
    session_id: str
    participant_ref: str
    access_token_hash: str = ""
    envelope_id: str
    envelope_mode: EnvelopeMode
    current_node_id: str
    status: Literal["joined", "private_scene", "at_barrier", "completed", "left"] = "joined"
    private_answers: dict[str, str] = Field(default_factory=dict)
    frozen_cue_ids: list[str] = Field(default_factory=list)
    joined_at: datetime
    updated_at: datetime


class TheaterEvent(ExperienceModel):
    schema_version: Literal["deepbazi.theater_event.v1"] = "deepbazi.theater_event.v1"
    event_id: str
    session_id: str
    sequence: int = Field(ge=1)
    event_type: str = Field(min_length=1, max_length=120)
    scope: Visibility
    participant_run_id: str | None = None
    node_id: str = ""
    cue_instance_id: str | None = None
    cue_hash: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)
    occurred_at: datetime


class TopicExploration(ExperienceModel):
    schema_version: Literal["deepbazi.topic_exploration.v1"] = "deepbazi.topic_exploration.v1"
    exploration_id: str
    participant_run_id: str
    topic_id: str
    responses: dict[str, str] = Field(default_factory=dict)
    capsule_message: str = ""
    experiment_kind: str = Field(default="", max_length=120)
    base_snapshot_hash: str = Field(default="", max_length=64)
    selected_node_ids: list[str] = Field(default_factory=list)
    sandbox_result_refs: list[str] = Field(default_factory=list)
    observations: list[str] = Field(default_factory=list)
    open_question: str = Field(default="", max_length=1200)
    restored_original: bool = False
    capability_trace: list[Literal["visual_only", "deterministic_structure", "reasoning_required"]] = Field(default_factory=list)
    life_case_version_observed: str = Field(default="", max_length=180)
    case_local_only: bool = True
    writes_life_case: Literal[False] = False
    created_at: datetime
