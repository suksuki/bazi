from __future__ import annotations

import hashlib
import io
import json
import math
import os
import struct
import urllib.error
import urllib.request
import wave
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Protocol

from experience.compiler import canonical_hash
from experience.contracts import (
    MingliExperienceEnvelope,
    PerformanceCueInstance,
    PerformancePackage,
    VisemeTrackItem,
)
from experience.performance import compile_performance_package


DEFAULT_TTS_URL = "http://127.0.0.1:17860"
DEFAULT_VOICE_INSTRUCTION = "声音亲切沉稳，像一位可靠的年轻命理师；自然停顿，不要播音腔。"


class TheaterPerformanceError(RuntimeError):
    pass


@dataclass(frozen=True)
class SynthesizedSpeech:
    wav_bytes: bytes
    generation_seconds: float | None = None


class TheaterTTS(Protocol):
    voice_id: str
    voice_version: str

    def synthesize(self, text: str) -> SynthesizedSpeech: ...


class QwenTheaterTTS:
    def __init__(
        self,
        *,
        base_url: str,
        speaker: str,
        instruction: str,
        api_key: str = "",
        timeout_seconds: float = 180.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.voice_id = speaker
        self.instruction = instruction
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds
        instruction_hash = hashlib.sha256(instruction.encode("utf-8")).hexdigest()[:12]
        self.voice_version = f"qwen3-tts-0.6b-customvoice:{speaker}:{instruction_hash}"

    @classmethod
    def from_environment(cls) -> "QwenTheaterTTS":
        return cls(
            base_url=os.getenv("V50_TTS_BASE_URL", DEFAULT_TTS_URL).strip() or DEFAULT_TTS_URL,
            speaker=os.getenv("V50_ABU_TTS_SPEAKER", "Eric").strip() or "Eric",
            instruction=os.getenv("V50_ABU_TTS_INSTRUCT", DEFAULT_VOICE_INSTRUCTION).strip()
            or DEFAULT_VOICE_INSTRUCTION,
            api_key=os.getenv("V50_TTS_API_KEY", "").strip(),
            timeout_seconds=float(os.getenv("V50_TTS_TIMEOUT_SECONDS", "180")),
        )

    def synthesize(self, text: str) -> SynthesizedSpeech:
        if not text.strip():
            raise TheaterPerformanceError("tts_text_required")
        if len(text) > 2200:
            raise TheaterPerformanceError("performance_dialogue_too_long")
        body = json.dumps(
            {
                "text": text,
                "speaker": self.voice_id,
                "instruct": self.instruction,
                "language": "Chinese",
            },
            ensure_ascii=False,
        ).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["X-API-Key"] = self.api_key
        request = urllib.request.Request(f"{self.base_url}/tts", data=body, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                wav_bytes = response.read()
                generated = response.headers.get("X-Gen-Seconds")
        except (urllib.error.URLError, TimeoutError) as exc:
            raise TheaterPerformanceError(f"tts_unavailable:{exc}") from exc
        if not wav_bytes.startswith(b"RIFF") or b"WAVE" not in wav_bytes[:16]:
            raise TheaterPerformanceError("tts_response_is_not_wav")
        return SynthesizedSpeech(
            wav_bytes=wav_bytes,
            generation_seconds=float(generated) if generated else None,
        )


class PerformancePackageRepository:
    """File-backed immutable package store for frozen media and replay."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def package_path(self, package_id: str) -> Path:
        return self.root / f"{_safe_id(package_id)}.json"

    def audio_path(self, package_id: str) -> Path:
        return self.root / f"{_safe_id(package_id)}.wav"

    def get(self, package_id: str) -> PerformancePackage | None:
        path = self.package_path(package_id)
        if not path.exists():
            return None
        return PerformancePackage.model_validate_json(path.read_text(encoding="utf-8"))

    def save(self, package: PerformancePackage, audio_bytes: bytes) -> None:
        audio_path = self.audio_path(package.package_id)
        package_path = self.package_path(package.package_id)
        if audio_path.exists() or package_path.exists():
            existing = self.get(package.package_id)
            if not existing or existing.package_hash != package.package_hash:
                raise TheaterPerformanceError("immutable_performance_package_conflict")
            return
        audio_tmp = audio_path.with_suffix(".wav.tmp")
        package_tmp = package_path.with_suffix(".json.tmp")
        audio_tmp.write_bytes(audio_bytes)
        package_tmp.write_text(package.model_dump_json(indent=2), encoding="utf-8")
        audio_tmp.replace(audio_path)
        package_tmp.replace(package_path)


class TheaterPerformanceService:
    def __init__(self, *, repository: PerformancePackageRepository, tts: TheaterTTS) -> None:
        self.repository = repository
        self.tts = tts

    @classmethod
    def from_environment(cls) -> "TheaterPerformanceService":
        media_root = Path(
            os.getenv("V50_THEATER_MEDIA_DIR", "/tmp/deepbazi-v50-theater-performance")
        ).expanduser()
        return cls(repository=PerformancePackageRepository(media_root), tts=QwenTheaterTTS.from_environment())

    def prepare(
        self,
        *,
        cue: PerformanceCueInstance,
        envelope: MingliExperienceEnvelope | None,
    ) -> PerformancePackage:
        package_key = canonical_hash(
            {
                "cue_hash": cue.cue_hash,
                "voice_version": self.tts.voice_version,
                "compiler_version": "performance-package-compiler.v1",
            }
        )
        package_id = f"performance-{package_key[:24]}"
        existing = self.repository.get(package_id)
        if existing:
            audio_path = self.repository.audio_path(package_id)
            if not audio_path.exists() or _sha256(audio_path.read_bytes()) != existing.audio.sha256:
                raise TheaterPerformanceError("frozen_performance_audio_missing_or_corrupt")
            return existing

        speech = self.tts.synthesize(cue.final_dialogue)
        speech_start_ms = 900
        audio_bytes = _pad_wav(speech.wav_bytes, lead_ms=speech_start_ms, trail_ms=420)
        sample_rate, duration_ms = _wav_metadata(audio_bytes)
        audio_hash = _sha256(audio_bytes)
        viseme_track = _audio_rms_visemes(audio_bytes)
        package = compile_performance_package(
            package_id=package_id,
            cue=cue,
            envelope=envelope,
            audio_uri=f"/api/v50/theater/performance/{package_id}/audio",
            audio_sha256=audio_hash,
            duration_ms=duration_ms,
            sample_rate=sample_rate,
            speech_start_ms=speech_start_ms,
            voice_id=self.tts.voice_id,
            voice_version=self.tts.voice_version,
            viseme_track=viseme_track,
            frozen_at=datetime.now(timezone.utc),
        )
        self.repository.save(package, audio_bytes)
        return package


def _pad_wav(wav_bytes: bytes, *, lead_ms: int, trail_ms: int) -> bytes:
    source = io.BytesIO(wav_bytes)
    with wave.open(source, "rb") as reader:
        channels = reader.getnchannels()
        sample_width = reader.getsampwidth()
        sample_rate = reader.getframerate()
        frames = reader.readframes(reader.getnframes())
    silence_frame = b"\x00" * channels * sample_width
    lead_frames = silence_frame * round(sample_rate * lead_ms / 1000)
    trail_frames = silence_frame * round(sample_rate * trail_ms / 1000)
    target = io.BytesIO()
    with wave.open(target, "wb") as writer:
        writer.setnchannels(channels)
        writer.setsampwidth(sample_width)
        writer.setframerate(sample_rate)
        writer.writeframes(lead_frames + frames + trail_frames)
    return target.getvalue()


def _wav_metadata(wav_bytes: bytes) -> tuple[int, int]:
    with wave.open(io.BytesIO(wav_bytes), "rb") as reader:
        sample_rate = reader.getframerate()
        duration_ms = max(1, round(reader.getnframes() / sample_rate * 1000))
    return sample_rate, duration_ms


def _audio_rms_visemes(wav_bytes: bytes, *, window_ms: int = 80) -> list[VisemeTrackItem]:
    with wave.open(io.BytesIO(wav_bytes), "rb") as reader:
        if reader.getsampwidth() != 2:
            return []
        channels = reader.getnchannels()
        sample_rate = reader.getframerate()
        frames_per_window = max(1, round(sample_rate * window_ms / 1000))
        rms_rows: list[tuple[int, float]] = []
        at_ms = 0
        while True:
            raw = reader.readframes(frames_per_window)
            if not raw:
                break
            samples = [value[0] for value in struct.iter_unpack("<h", raw)]
            if channels > 1:
                samples = samples[::channels]
            rms = math.sqrt(sum(sample * sample for sample in samples) / max(1, len(samples)))
            rms_rows.append((at_ms, rms))
            at_ms += window_ms
    nonzero = sorted(value for _, value in rms_rows if value > 30)
    reference = nonzero[min(len(nonzero) - 1, round(len(nonzero) * 0.9))] if nonzero else 1.0
    rows: list[VisemeTrackItem] = []
    previous_shape = ""
    previous_at = -1000
    for at_ms, rms in rms_rows:
        openness = min(1.0, rms / max(reference, 1.0))
        shape = "closed" if openness < 0.08 else "small" if openness < 0.48 else "wide"
        if shape != previous_shape or at_ms - previous_at >= 240:
            rows.append(
                VisemeTrackItem(
                    at_ms=at_ms,
                    shape=shape,
                    openness=round(openness, 3),
                )
            )
            previous_shape = shape
            previous_at = at_ms
    return rows


def _safe_id(value: str) -> str:
    if not value or any(character not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_" for character in value):
        raise TheaterPerformanceError("invalid_performance_package_id")
    return value


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()
