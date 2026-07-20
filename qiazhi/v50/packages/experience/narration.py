from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import Field, model_validator

from experience.contracts import ExperienceModel
from experience.experiments import MingliVisualCue


NarrationSegmentKind = Literal["thesis", "work_path", "condition", "uncertainty"]


class NarrationSegment(ExperienceModel):
    segment_id: str = Field(min_length=1, max_length=180)
    order: int = Field(ge=0)
    kind: NarrationSegmentKind
    title: str = Field(min_length=1, max_length=80)
    text: str = Field(min_length=1, max_length=1200)
    source_claim_refs: list[str] = Field(min_length=1)
    source_refs: list[str] = Field(default_factory=list)
    visual_anchor_ids: list[str] = Field(min_length=1)
    visual_cues: list[MingliVisualCue] = Field(default_factory=list)
    estimated_duration_seconds: int = Field(ge=1, le=60)


class NarrationManifest(ExperienceModel):
    schema_version: Literal["deepbazi.narration_manifest.v1"] = "deepbazi.narration_manifest.v1"
    manifest_id: str = Field(min_length=1, max_length=180)
    manifest_hash: str = Field(min_length=64, max_length=64)
    scope: Literal["participant_private"] = "participant_private"
    case_id: str = Field(min_length=1, max_length=180)
    chart_version: str = Field(min_length=1, max_length=180)
    life_case_version: str = Field(min_length=1, max_length=180)
    formal_insight_id: str = Field(min_length=1, max_length=180)
    narration_script_version: str = Field(min_length=1, max_length=120)
    mode: Literal["standard"] = "standard"
    language: str = Field(default="zh-CN", min_length=2, max_length=20)
    voice_id: str = Field(min_length=1, max_length=100)
    voice_version: str = Field(min_length=1, max_length=240)
    segments: list[NarrationSegment] = Field(min_length=1)
    compiled_at: datetime
    autoplay: Literal[False] = False
    page_available_without_audio: Literal[True] = True

    @model_validator(mode="after")
    def validate_segments(self) -> "NarrationManifest":
        ids = [item.segment_id for item in self.segments]
        orders = [item.order for item in self.segments]
        if len(ids) != len(set(ids)):
            raise ValueError("narration_segment_id_must_be_unique")
        if orders != sorted(orders) or len(orders) != len(set(orders)):
            raise ValueError("narration_segment_order_must_be_unique_and_sorted")
        return self


class SpeechAssetSource(ExperienceModel):
    case_id: str = Field(min_length=1, max_length=180)
    chart_version: str = Field(min_length=1, max_length=180)
    life_case_version: str = Field(min_length=1, max_length=180)
    formal_insight_id: str = Field(min_length=1, max_length=180)
    segment_id: str = Field(min_length=1, max_length=180)
    claim_refs: list[str] = Field(min_length=1)
    source_refs: list[str] = Field(default_factory=list)
    narration_script_version: str = Field(min_length=1, max_length=120)
    source_text_hash: str = Field(min_length=64, max_length=64)


class SpeechAssetVoice(ExperienceModel):
    voice_id: str = Field(min_length=1, max_length=100)
    voice_version: str = Field(min_length=1, max_length=240)
    tts_model_version: str = Field(min_length=1, max_length=240)
    language: str = Field(min_length=2, max_length=20)
    speaking_style: str = Field(min_length=1, max_length=120)
    speed: float = Field(default=1.0, ge=0.5, le=1.5)
    pronunciation_lexicon_version: str = Field(min_length=1, max_length=120)


class SpeechSubtitleItem(ExperienceModel):
    start_ms: int = Field(ge=0)
    end_ms: int = Field(gt=0)
    text: str = Field(min_length=1, max_length=1200)


class SpeechAssetMediaVariant(ExperienceModel):
    format: Literal["opus"] = "opus"
    mime_type: Literal["audio/ogg; codecs=opus"] = "audio/ogg; codecs=opus"
    audio_url: str = Field(min_length=1, max_length=500)
    audio_hash: str = Field(min_length=64, max_length=64)
    size_bytes: int = Field(ge=1)
    codec_profile_version: str = Field(min_length=1, max_length=120)


class SpeechAssetMedia(ExperienceModel):
    audio_url: str = Field(min_length=1, max_length=500)
    audio_hash: str = Field(min_length=64, max_length=64)
    duration_ms: int = Field(ge=1)
    sample_rate: int = Field(ge=8000, le=192000)
    format: Literal["wav"] = "wav"
    subtitle_track: list[SpeechSubtitleItem] = Field(min_length=1)
    size_bytes: int = Field(ge=1)
    playback_variants: list[SpeechAssetMediaVariant] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_playback_variants(self) -> "SpeechAssetMedia":
        formats = [item.format for item in self.playback_variants]
        if len(formats) != len(set(formats)):
            raise ValueError("speech_asset_playback_variant_format_must_be_unique")
        return self


class SpeechAsset(ExperienceModel):
    schema_version: Literal["deepbazi.speech_asset.v1"] = "deepbazi.speech_asset.v1"
    speech_asset_id: str = Field(min_length=1, max_length=180)
    scope: Literal["participant_private"] = "participant_private"
    source: SpeechAssetSource
    voice: SpeechAssetVoice
    media: SpeechAssetMedia
    status: Literal["ready"] = "ready"
    generated_at: datetime
    generation_seconds: float | None = Field(default=None, ge=0.0)
