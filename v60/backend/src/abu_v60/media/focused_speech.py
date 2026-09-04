from __future__ import annotations

import base64
import json
import re
from dataclasses import dataclass
from threading import Lock

from sqlalchemy.engine import Engine

from abu_v60.media.tts import Qwen3TTSProvider, WavAudio, merge_wav
from abu_v60.mingli.focused_pass_store import MingliFocusedPassStore
from abu_v60.mingli.narration_catalog import voice_profile
from abu_v60.mingli.stage import MingliStageError, MingliStageService
from abu_v60.mingli.stage_contracts import MingliStageMode
from abu_v60.settings import Settings, settings


class FocusedPassSpeechError(ValueError):
    pass


class FocusedPassSpeechNotFound(FocusedPassSpeechError):
    pass


class FocusedPassSpeechConflict(FocusedPassSpeechError):
    pass


FOCUSED_SPEECH_TIMELINE_VERSION = "v60.mingli-focused-speech-timeline.001"
FOCUSED_SPEECH_TIMELINE_HEADER = "X-Abu-Focused-Speech-Timeline"
_SUBTITLE_CUE_MAX_CHARACTERS = 64
_SUBTITLE_CUE_MIN_TAIL_CHARACTERS = 20


@dataclass(frozen=True, slots=True)
class FocusedPassSpeechCue:
    cue_index: int
    text: str
    start_ms: int
    end_ms: int

    def as_dict(self) -> dict[str, int | str]:
        return {
            "cue_index": self.cue_index,
            "text": self.text,
            "start_ms": self.start_ms,
            "end_ms": self.end_ms,
        }


@dataclass(frozen=True, slots=True)
class PreparedFocusedPassSpeech:
    audio: WavAudio
    cues: tuple[FocusedPassSpeechCue, ...]

    def timeline_header_value(self) -> str:
        payload = {
            "timeline_version": FOCUSED_SPEECH_TIMELINE_VERSION,
            "duration_ms": self.audio.duration_ms,
            "cues": [cue.as_dict() for cue in self.cues],
        }
        raw = json.dumps(
            payload,
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8")
        return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


class FocusedPassSpeechService:
    """Speak only persisted, account-owned focused reading text."""

    def __init__(
        self,
        engine: Engine,
        *,
        runtime_settings: Settings | None = None,
        stages: MingliStageService | None = None,
        passes: MingliFocusedPassStore | None = None,
        provider: Qwen3TTSProvider | None = None,
    ) -> None:
        self._settings = runtime_settings or settings
        self._stages = stages or MingliStageService(
            engine,
            runtime_settings=self._settings,
        )
        self._passes = passes or MingliFocusedPassStore(engine)
        self._provider = provider or Qwen3TTSProvider(
            enabled=self._settings.tts_enabled,
            url=self._settings.tts_url,
            timeout_seconds=self._settings.tts_timeout_seconds,
            max_audio_bytes=self._settings.tts_max_audio_bytes,
        )
        self._cache: dict[str, PreparedFocusedPassSpeech] = {}
        self._cache_lock = Lock()

    def prepare(
        self,
        *,
        account_ref: str,
        subject_id: str,
        stage_mode: MingliStageMode = MingliStageMode.NATAL_4,
        selected_year: int | None = None,
        expected_stage_projection_ref: str,
        expected_stage_projection_hash: str,
        record_ref: str,
        expected_record_hash: str,
    ) -> PreparedFocusedPassSpeech:
        try:
            stage = self._stages.project(
                account_ref=account_ref,
                subject_id=subject_id,
                stage_mode=stage_mode,
                selected_year=selected_year,
            )
        except MingliStageError as exc:
            raise FocusedPassSpeechError(str(exc)) from exc
        if (
            stage.projection_ref != expected_stage_projection_ref
            or stage.projection_hash != expected_stage_projection_hash
        ):
            raise FocusedPassSpeechConflict("mingli_focused_speech_stage_stale")

        record = self._passes.owned_record(
            requester_account_ref=account_ref,
            record_ref=record_ref,
        )
        if record is None:
            raise FocusedPassSpeechNotFound("mingli_focused_speech_pass_not_found")
        if record.record_hash != expected_record_hash:
            raise FocusedPassSpeechConflict("mingli_focused_speech_pass_stale")
        if (
            record.case_ref != stage.case_ref
            or record.reading_ref != stage.reading_ref
            or record.reading_hash != stage.reading_hash
        ):
            raise FocusedPassSpeechConflict("mingli_focused_speech_lineage_mismatch")

        voice = voice_profile(
            "ABU_NARRATOR_V1",
            speaker=self._settings.tts_abu_voice,
            model=self._settings.tts_model,
        )
        cache_key = (
            f"{FOCUSED_SPEECH_TIMELINE_VERSION}:"
            f"{record.record_hash}:{voice.voice_profile_hash}"
        )
        with self._cache_lock:
            cached = self._cache.get(cache_key)
            if cached is not None:
                return cached
            segments = _speech_segments(record.pass_result.normalized_text)
            audio_segments = tuple(
                self._provider.synthesize(text=text, speaker=voice.speaker)
                for text in segments
            )
            audio = merge_wav(
                audio_segments,
                max_audio_bytes=self._settings.tts_max_audio_bytes,
            )
            cues: list[FocusedPassSpeechCue] = []
            cumulative_frames = 0
            for cue_index, (text, audio_segment) in enumerate(
                zip(segments, audio_segments, strict=True)
            ):
                start_ms = round(cumulative_frames * 1000 / audio.sample_rate_hz)
                cumulative_frames += audio_segment.frame_count
                end_ms = round(cumulative_frames * 1000 / audio.sample_rate_hz)
                cues.append(
                    FocusedPassSpeechCue(
                        cue_index=cue_index,
                        text=text,
                        start_ms=start_ms,
                        end_ms=end_ms,
                    )
                )
            if cues[-1].end_ms != audio.duration_ms:
                final = cues[-1]
                cues[-1] = FocusedPassSpeechCue(
                    cue_index=final.cue_index,
                    text=final.text,
                    start_ms=final.start_ms,
                    end_ms=audio.duration_ms,
                )
            prepared = PreparedFocusedPassSpeech(audio=audio, cues=tuple(cues))
            if len(self._cache) >= 24:
                self._cache.pop(next(iter(self._cache)))
            self._cache[cache_key] = prepared
            return prepared


def _speech_segments(value: str) -> tuple[str, ...]:
    text = re.sub(r"(?m)^\s{0,3}#{1,6}\s*", "", value)
    text = re.sub(r"\*\*|__|`", "", text)
    text = re.sub(r"(?m)^\s*(?:[-*+]|\d+[.)、])\s+", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        raise FocusedPassSpeechError("mingli_focused_speech_text_empty")

    sentences = re.findall(r"[^。！？；]+[。！？；]?", text)
    chunks = [
        chunk
        for sentence in (item.strip() for item in sentences if item.strip())
        for chunk in _subtitle_chunks(sentence)
    ]
    if not chunks:
        raise FocusedPassSpeechError("mingli_focused_speech_text_empty")
    return tuple(chunks)


def _subtitle_chunks(sentence: str) -> tuple[str, ...]:
    if len(sentence) <= _SUBTITLE_CUE_MAX_CHARACTERS:
        return (sentence,)
    clauses = [
        item.strip()
        for item in re.findall(r"[^，、：]+[，、：]?", sentence)
        if item.strip()
    ]
    units: list[str] = []
    for clause in clauses:
        while len(clause) > _SUBTITLE_CUE_MAX_CHARACTERS:
            split_at = _SUBTITLE_CUE_MAX_CHARACTERS
            if len(clause) - split_at < _SUBTITLE_CUE_MIN_TAIL_CHARACTERS:
                split_at = (len(clause) + 1) // 2
            units.append(clause[:split_at])
            clause = clause[split_at:]
        if clause:
            units.append(clause)

    grouped_units: list[list[str]] = []
    current: list[str] = []
    for unit in units:
        if current and sum(len(item) for item in current) + len(unit) > (
            _SUBTITLE_CUE_MAX_CHARACTERS
        ):
            grouped_units.append(current)
            current = [unit]
        else:
            current.append(unit)
    if current:
        grouped_units.append(current)

    if len(grouped_units) > 1:
        previous = grouped_units[-2]
        final = grouped_units[-1]
        while (
            len("".join(final)) < _SUBTITLE_CUE_MIN_TAIL_CHARACTERS
            and len(previous) > 1
            and len(previous[-1]) + len("".join(final))
            <= _SUBTITLE_CUE_MAX_CHARACTERS
        ):
            final.insert(0, previous.pop())
    return tuple("".join(group) for group in grouped_units)
