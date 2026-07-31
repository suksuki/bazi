from __future__ import annotations

from sqlalchemy.engine import Engine

from abu_v60.media.mingli_narration_store import (
    MingliNarrationStore,
    StoredMingliNarration,
)
from abu_v60.media.tts import (
    Qwen3TTSProvider,
    TTSProviderError,
    TTSUnavailableError,
    merge_wav,
    provider_profile_hash,
)
from abu_v60.mingli.narration_catalog import script_for_projection, voice_profile
from abu_v60.mingli.narration_contracts import (
    MINGLI_NARRATION_VERSION,
    MingliNarrationAsset,
    MingliNarrationCue,
    MingliNarrationPrepareRequest,
    narration_generation_key,
)
from abu_v60.mingli.stage import MingliStageError, MingliStageService
from abu_v60.settings import Settings, settings


class MingliNarrationError(ValueError):
    pass


class MingliNarrationConflictError(MingliNarrationError):
    pass


class MingliNarrationService:
    def __init__(
        self,
        engine: Engine,
        *,
        runtime_settings: Settings | None = None,
        stages: MingliStageService | None = None,
        store: MingliNarrationStore | None = None,
        provider: Qwen3TTSProvider | None = None,
    ) -> None:
        self._settings = runtime_settings or settings
        self._stages = stages or MingliStageService(
            engine,
            runtime_settings=self._settings,
        )
        self._store = store or MingliNarrationStore(engine)
        self._provider = provider or Qwen3TTSProvider(
            enabled=self._settings.tts_enabled,
            url=self._settings.tts_url,
            timeout_seconds=self._settings.tts_timeout_seconds,
            max_audio_bytes=self._settings.tts_max_audio_bytes,
        )

    def prepare(
        self,
        *,
        account_ref: str,
        request: MingliNarrationPrepareRequest,
    ) -> StoredMingliNarration:
        try:
            projection = self._stages.project(
                account_ref=account_ref,
                subject_id=request.subject_id,
                stage_mode=request.stage_mode,
                selected_year=request.selected_year,
            )
        except MingliStageError as exc:
            raise MingliNarrationError(str(exc)) from exc
        if (
            projection.projection_ref != request.expected_stage_projection_ref
            or projection.projection_hash != request.expected_stage_projection_hash
        ):
            raise MingliNarrationConflictError("mingli_narration_stage_projection_stale")
        if projection.subject_kind == "HUMAN_OWNER" and projection.reading_ref is None:
            raise MingliNarrationConflictError("mingli_narration_formal_reading_not_ready")

        script = script_for_projection(projection)
        configured_speaker = (
            self._settings.tts_duoduo_voice
            if projection.narrator_actor_id == "DUODUO_NARRATOR_V1"
            else self._settings.tts_abu_voice
        )
        voice = voice_profile(
            projection.narrator_actor_id,
            speaker=configured_speaker,
            model=self._settings.tts_model,
        )
        provider_hash = provider_profile_hash(
            profile_ref=self._settings.tts_provider_profile_ref,
            model=self._settings.tts_model,
        )
        generation_key = narration_generation_key(
            narration_version=MINGLI_NARRATION_VERSION,
            requester_account_ref=account_ref,
            stage_projection_ref=projection.projection_ref,
            stage_projection_hash=projection.projection_hash,
            cue_set_ref=request.cue_set_ref,
            script_ref=script.script_ref,
            script_hash=script.script_hash,
            voice_profile_ref=voice.voice_profile_ref,
            voice_profile_hash=voice.voice_profile_hash,
            provider_profile_ref=self._settings.tts_provider_profile_ref,
            provider_profile_hash=provider_hash,
            provider_deployment_ref=self._settings.tts_provider_deployment_ref,
        )
        existing = self._store.by_generation_key(
            requester_account_ref=account_ref,
            generation_key=generation_key,
        )
        if existing is not None:
            return existing

        audio_segments = tuple(
            self._provider.synthesize(text=segment.text, speaker=voice.speaker)
            for segment in script.segments
        )
        merged = merge_wav(
            audio_segments,
            max_audio_bytes=self._settings.tts_max_audio_bytes,
        )
        cues: list[MingliNarrationCue] = []
        cumulative_frames = 0
        for script_segment, audio_segment in zip(
            script.segments,
            audio_segments,
            strict=True,
        ):
            start_ms = round(cumulative_frames * 1000 / merged.sample_rate_hz)
            cumulative_frames += audio_segment.frame_count
            end_ms = round(cumulative_frames * 1000 / merged.sample_rate_hz)
            cues.append(
                MingliNarrationCue(
                    cue_id=script_segment.cue_id,
                    text=script_segment.text,
                    start_ms=start_ms,
                    end_ms=end_ms,
                    semantic_action=script_segment.semantic_action,
                )
            )
        if cues[-1].end_ms != merged.duration_ms:
            cues[-1] = cues[-1].model_copy(update={"end_ms": merged.duration_ms})

        source_scope = (
            "FORMAL_READING"
            if projection.subject_kind == "HUMAN_OWNER"
            else "CANONICAL_SYNTHETIC_DEMO"
        )
        asset = MingliNarrationAsset.issue(
            requester_account_ref=account_ref,
            case_ref=projection.case_ref,
            reading_ref=projection.reading_ref,
            source_scope=source_scope,
            stage_projection_ref=projection.projection_ref,
            stage_projection_hash=projection.projection_hash,
            cue_set_ref=request.cue_set_ref,
            script_ref=script.script_ref,
            script_hash=script.script_hash,
            actor_ref=voice.actor_ref,
            voice_profile_ref=voice.voice_profile_ref,
            voice_profile_hash=voice.voice_profile_hash,
            voice_profile_status=voice.status,
            provider_profile_ref=self._settings.tts_provider_profile_ref,
            provider_profile_hash=provider_hash,
            provider_deployment_ref=self._settings.tts_provider_deployment_ref,
            preparation_status="READY",
            audio_mime_type="audio/wav",
            audio_sha256=merged.audio_sha256,
            audio_byte_length=len(merged.audio_bytes),
            duration_ms=merged.duration_ms,
            sample_rate_hz=merged.sample_rate_hz,
            channels=merged.channels,
            sample_width_bytes=merged.sample_width_bytes,
            cues=tuple(cues),
            clock_source="HTML_AUDIO_CURRENT_TIME",
            refresh_policy="READY_AT_ZERO",
            upstream_exposed_to_client=False,
        )
        return self._store.ensure(
            generation_key=generation_key,
            asset=asset,
            audio_bytes=merged.audio_bytes,
        )

    def owned_asset(
        self,
        *,
        account_ref: str,
        narration_ref: str,
    ) -> StoredMingliNarration | None:
        return self._store.owned_asset(
            requester_account_ref=account_ref,
            narration_ref=narration_ref,
        )


__all__ = [
    "MingliNarrationConflictError",
    "MingliNarrationError",
    "MingliNarrationService",
    "TTSProviderError",
    "TTSUnavailableError",
]
