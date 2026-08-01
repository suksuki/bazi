from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from abu_v60.mingli.stage_contracts import MingliStageMode
from abu_v60.provenance import content_hash, stable_ref

MINGLI_NARRATION_REQUEST_VERSION = "v60.mingli-narration-request.001"
LEGACY_MINGLI_NARRATION_VERSION = "v60.mingli-narration.001"
MINGLI_NARRATION_VERSION = "v60.mingli-narration.002"
MINGLI_CUE_SET_REF = "v60.mingli-stage-guide-cues.001"


class MingliNarrationPrepareRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    request_version: Literal["v60.mingli-narration-request.001"] = (
        MINGLI_NARRATION_REQUEST_VERSION
    )
    subject_id: str = Field(min_length=1, max_length=240)
    stage_mode: MingliStageMode
    selected_year: int | None = Field(default=None, ge=1900, le=2200)
    expected_stage_projection_ref: str = Field(min_length=1)
    expected_stage_projection_hash: str = Field(min_length=64, max_length=64)
    cue_set_ref: Literal["v60.mingli-stage-guide-cues.001"] = MINGLI_CUE_SET_REF


class MingliNarrationCue(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    cue_id: Literal["STRUCTURE", "RELATION_BOUNDARY", "EVIDENCE_GAP", "TIME_LAYER"]
    text: str = Field(min_length=1, max_length=500)
    start_ms: int = Field(ge=0)
    end_ms: int = Field(gt=0)
    semantic_action: Literal[
        "PILLARS_PRESENT",
        "RELATIONS_PRESENT",
        "BOUNDARY_HOLD",
        "TIME_COORDINATES_PRESENT",
    ]

    @model_validator(mode="after")
    def cue_range_is_valid(self) -> MingliNarrationCue:
        if self.end_ms <= self.start_ms:
            raise ValueError("mingli_narration_cue_range_invalid")
        return self


class MingliNarrationAsset(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    narration_ref: str = Field(min_length=1)
    narration_hash: str = Field(min_length=64, max_length=64)
    narration_version: Literal[
        "v60.mingli-narration.001",
        "v60.mingli-narration.002",
    ] = MINGLI_NARRATION_VERSION
    requester_account_ref: str = Field(min_length=1)
    case_ref: str = Field(min_length=1)
    reading_ref: str | None = None
    source_scope: Literal["FORMAL_READING", "CANONICAL_SYNTHETIC_DEMO"]
    stage_projection_ref: str = Field(min_length=1)
    stage_projection_hash: str = Field(min_length=64, max_length=64)
    cue_set_ref: Literal["v60.mingli-stage-guide-cues.001"]
    script_ref: str = Field(min_length=1)
    script_hash: str = Field(min_length=64, max_length=64)
    actor_ref: Literal["ABU_NARRATOR_V1", "DUODUO_NARRATOR_V1"]
    voice_profile_ref: str = Field(min_length=1)
    voice_profile_hash: str = Field(min_length=64, max_length=64)
    voice_profile_status: Literal["OWNER_SELECTED", "AUDITION_CANDIDATE"]
    provider_profile_ref: str | None = Field(default=None, min_length=1)
    provider_profile_hash: str | None = Field(
        default=None,
        min_length=64,
        max_length=64,
    )
    provider_deployment_ref: str | None = Field(default=None, min_length=1)
    preparation_status: Literal["READY"]
    audio_mime_type: Literal["audio/wav"]
    audio_sha256: str = Field(min_length=64, max_length=64)
    audio_byte_length: int = Field(gt=0, le=8 * 1024 * 1024)
    duration_ms: int = Field(gt=0)
    sample_rate_hz: Literal[24000]
    channels: Literal[1]
    sample_width_bytes: Literal[2]
    cues: tuple[MingliNarrationCue, ...] = Field(min_length=4, max_length=4)
    clock_source: Literal["HTML_AUDIO_CURRENT_TIME"]
    refresh_policy: Literal["READY_AT_ZERO"]
    upstream_exposed_to_client: Literal[False]

    @model_validator(mode="after")
    def identity_and_cues_are_valid(self) -> MingliNarrationAsset:
        if self.source_scope == "FORMAL_READING" and self.reading_ref is None:
            raise ValueError("mingli_narration_formal_reading_required")
        expected_ids = ("STRUCTURE", "RELATION_BOUNDARY", "EVIDENCE_GAP", "TIME_LAYER")
        if tuple(cue.cue_id for cue in self.cues) != expected_ids:
            raise ValueError("mingli_narration_cue_order_invalid")
        if self.cues[0].start_ms != 0 or self.cues[-1].end_ms != self.duration_ms:
            raise ValueError("mingli_narration_cue_duration_mismatch")
        if any(
            left.end_ms != right.start_ms
            for left, right in zip(self.cues, self.cues[1:], strict=False)
        ):
            raise ValueError("mingli_narration_cues_not_contiguous")
        provider_identity = (
            self.provider_profile_ref,
            self.provider_profile_hash,
            self.provider_deployment_ref,
        )
        if self.narration_version == MINGLI_NARRATION_VERSION:
            if any(item is None for item in provider_identity):
                raise ValueError("mingli_narration_provider_identity_required")
        elif any(item is not None for item in provider_identity):
            raise ValueError("mingli_narration_legacy_provider_identity_embedded")
        identity = self.model_dump(mode="json", exclude={"narration_ref", "narration_hash"})
        if self.narration_version == LEGACY_MINGLI_NARRATION_VERSION:
            for field in (
                "provider_profile_ref",
                "provider_profile_hash",
                "provider_deployment_ref",
            ):
                identity.pop(field)
        if self.narration_hash != content_hash(identity):
            raise ValueError("mingli_narration_hash_mismatch")
        if self.narration_ref != stable_ref("v60-mingli-narration", identity):
            raise ValueError("mingli_narration_ref_mismatch")
        return self

    @classmethod
    def issue(cls, **values: Any) -> MingliNarrationAsset:
        identity = {
            **values,
            "narration_version": MINGLI_NARRATION_VERSION,
        }
        identity["cues"] = tuple(
            item.model_dump(mode="json") if isinstance(item, BaseModel) else item
            for item in identity["cues"]
        )
        return cls(
            narration_ref=stable_ref("v60-mingli-narration", identity),
            narration_hash=content_hash(identity),
            **identity,
        )


def narration_generation_key(
    *,
    narration_version: str,
    requester_account_ref: str,
    stage_projection_ref: str,
    stage_projection_hash: str,
    cue_set_ref: str,
    script_ref: str,
    script_hash: str,
    voice_profile_ref: str,
    voice_profile_hash: str,
    provider_profile_ref: str,
    provider_profile_hash: str,
    provider_deployment_ref: str,
) -> str:
    identity = {
        "requester_account_ref": requester_account_ref,
        "stage_projection_ref": stage_projection_ref,
        "stage_projection_hash": stage_projection_hash,
        "cue_set_ref": cue_set_ref,
        "script_ref": script_ref,
        "script_hash": script_hash,
        "voice_profile_ref": voice_profile_ref,
        "voice_profile_hash": voice_profile_hash,
        "provider_profile_ref": provider_profile_ref,
        "provider_profile_hash": provider_profile_hash,
    }
    if narration_version == MINGLI_NARRATION_VERSION:
        identity = {
            "narration_version": narration_version,
            **identity,
            "provider_deployment_ref": provider_deployment_ref,
        }
    elif narration_version != LEGACY_MINGLI_NARRATION_VERSION:
        raise ValueError("mingli_narration_generation_version_unsupported")
    return content_hash(identity)


class MingliNarrationReadyResponse(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    asset: MingliNarrationAsset
    audio_url: str = Field(min_length=1)
