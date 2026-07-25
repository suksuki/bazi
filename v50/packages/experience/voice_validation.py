from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import Field, model_validator

from experience.contracts import ExperienceModel


VoiceValidationArm = Literal["text_only", "text_and_abu_voice"]
VoiceValidationEventType = Literal[
    "workspace_viewed",
    "narration_requested",
    "audio_ready",
    "playback_started",
    "playback_paused",
    "playback_resumed",
    "playback_stopped",
    "chapter_jump",
    "chapter_replayed",
    "narration_completed",
    "comprehension_opened",
    "comprehension_submitted",
]


class VoiceValidationInteractionEvent(ExperienceModel):
    client_event_id: str = Field(min_length=1, max_length=180)
    event_type: VoiceValidationEventType
    occurred_at: datetime
    elapsed_since_session_ms: int = Field(ge=0, le=86_400_000)
    segment_id: str = Field(default="", max_length=180)
    playback_position_ms: int | None = Field(default=None, ge=0, le=3_600_000)
    request_wait_ms: int | None = Field(default=None, ge=0, le=3_600_000)
    cache_hit: bool | None = None


class VoiceComprehensionSubmission(ExperienceModel):
    submitted_at: datetime
    consent_confirmed: Literal[True] = True
    whole_chart_summary: str = Field(min_length=1, max_length=1000)
    work_path_summary: str = Field(min_length=1, max_length=1000)
    key_condition_summary: str = Field(min_length=1, max_length=1000)
    uncertainty_summary: str = Field(min_length=1, max_length=1000)
    natural_followup_question: str = Field(default="", max_length=1000)
    fatigue_score: int = Field(ge=1, le=5)
    professional_trust_delta: int = Field(ge=-2, le=2)
    abu_long_term_listening_score: int | None = Field(default=None, ge=1, le=5)


class VoiceComprehensionAnalystReview(ExperienceModel):
    reviewed_at: datetime
    reviewer_ref: str = Field(min_length=1, max_length=180)
    whole_chart_accuracy: int = Field(ge=0, le=2)
    work_path_accuracy: int = Field(ge=0, le=2)
    condition_accuracy: int = Field(ge=0, le=2)
    uncertainty_accuracy: int = Field(ge=0, le=2)
    anchor_task_passed: bool
    notes: str = Field(default="", max_length=2000)


class VoiceValidationSession(ExperienceModel):
    schema_version: Literal["deepbazi.voice_comprehension_session.v1"] = (
        "deepbazi.voice_comprehension_session.v1"
    )
    session_id: str = Field(min_length=1, max_length=180)
    experiment_version: Literal["abu-voice-comprehension.v1"] = "abu-voice-comprehension.v1"
    participant_ref: str = Field(min_length=1, max_length=180)
    case_id: str = Field(min_length=1, max_length=180)
    manifest_id: str = Field(min_length=1, max_length=180)
    manifest_hash: str = Field(min_length=64, max_length=64)
    arm: VoiceValidationArm
    assignment_hash: str = Field(min_length=64, max_length=64)
    privacy_scope: Literal["participant_private_research"] = "participant_private_research"
    raw_birth_data_stored: Literal[False] = False
    started_at: datetime
    status: Literal["active", "submitted"] = "active"
    interactions: list[VoiceValidationInteractionEvent] = Field(default_factory=list)
    comprehension: VoiceComprehensionSubmission | None = None
    analyst_review: VoiceComprehensionAnalystReview | None = None

    @model_validator(mode="after")
    def validate_completion(self) -> "VoiceValidationSession":
        if self.status == "submitted" and self.comprehension is None:
            raise ValueError("submitted_voice_validation_requires_comprehension")
        event_ids = [item.client_event_id for item in self.interactions]
        if len(event_ids) != len(set(event_ids)):
            raise ValueError("voice_validation_event_id_must_be_unique")
        return self
