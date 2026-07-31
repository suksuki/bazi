from __future__ import annotations

import json
import urllib.error
import urllib.request
import wave
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from io import BytesIO

from abu_v60.provenance import content_hash


class TTSProviderError(RuntimeError):
    pass


class TTSUnavailableError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class WavAudio:
    audio_bytes: bytes
    duration_ms: int
    sample_rate_hz: int
    channels: int
    sample_width_bytes: int
    frame_count: int

    @property
    def audio_sha256(self) -> str:
        return content_hash_bytes(self.audio_bytes)


BinaryTransport = Callable[[str, dict[str, str], float, int], bytes]


class Qwen3TTSProvider:
    """Narrow server-side adapter for the dblife Qwen3-TTS proxy contract."""

    provider_profile_ref = "v60.qwen3-tts-proxy.001"

    def __init__(
        self,
        *,
        enabled: bool,
        url: str,
        timeout_seconds: float,
        max_audio_bytes: int,
        transport: BinaryTransport | None = None,
    ) -> None:
        self._enabled = enabled
        self._url = url
        self._timeout_seconds = timeout_seconds
        self._max_audio_bytes = max_audio_bytes
        self._transport = transport or _request_binary

    def synthesize(self, *, text: str, speaker: str) -> WavAudio:
        if not self._enabled:
            raise TTSUnavailableError("mingli_narration_tts_disabled")
        normalized = text.strip()
        if not normalized:
            raise TTSProviderError("mingli_narration_script_empty")
        if len(normalized) > 500:
            raise TTSProviderError("mingli_narration_segment_too_long")
        try:
            audio_bytes = self._transport(
                self._url,
                {
                    "text": normalized,
                    "speaker": speaker,
                    "language": "Chinese",
                },
                self._timeout_seconds,
                self._max_audio_bytes,
            )
        except TTSProviderError:
            raise
        except Exception as exc:
            raise TTSProviderError("mingli_narration_provider_failed") from exc
        return validate_wav(audio_bytes, max_audio_bytes=self._max_audio_bytes)


def validate_wav(audio_bytes: bytes, *, max_audio_bytes: int) -> WavAudio:
    if not audio_bytes or len(audio_bytes) > max_audio_bytes:
        raise TTSProviderError("mingli_narration_audio_size_invalid")
    if not audio_bytes.startswith(b"RIFF") or audio_bytes[8:12] != b"WAVE":
        raise TTSProviderError("mingli_narration_audio_not_wav")
    try:
        with wave.open(BytesIO(audio_bytes), "rb") as reader:
            channels = reader.getnchannels()
            sample_width = reader.getsampwidth()
            sample_rate = reader.getframerate()
            frame_count = reader.getnframes()
            compression = reader.getcomptype()
            frame_bytes = reader.readframes(frame_count)
    except (EOFError, wave.Error) as exc:
        raise TTSProviderError("mingli_narration_audio_wav_invalid") from exc
    if (
        channels != 1
        or sample_width != 2
        or sample_rate != 24000
        or compression != "NONE"
        or frame_count <= 0
        or len(frame_bytes) != frame_count * channels * sample_width
    ):
        raise TTSProviderError("mingli_narration_audio_format_unsupported")
    return WavAudio(
        audio_bytes=audio_bytes,
        duration_ms=round(frame_count * 1000 / sample_rate),
        sample_rate_hz=sample_rate,
        channels=channels,
        sample_width_bytes=sample_width,
        frame_count=frame_count,
    )


def merge_wav(segments: Sequence[WavAudio], *, max_audio_bytes: int) -> WavAudio:
    if not segments:
        raise TTSProviderError("mingli_narration_segments_required")
    first = segments[0]
    frames: list[bytes] = []
    for segment in segments:
        if (
            segment.sample_rate_hz != first.sample_rate_hz
            or segment.channels != first.channels
            or segment.sample_width_bytes != first.sample_width_bytes
        ):
            raise TTSProviderError("mingli_narration_segment_format_mismatch")
        with wave.open(BytesIO(segment.audio_bytes), "rb") as reader:
            frames.append(reader.readframes(reader.getnframes()))
    output = BytesIO()
    with wave.open(output, "wb") as writer:
        writer.setnchannels(first.channels)
        writer.setsampwidth(first.sample_width_bytes)
        writer.setframerate(first.sample_rate_hz)
        for payload in frames:
            writer.writeframes(payload)
    return validate_wav(output.getvalue(), max_audio_bytes=max_audio_bytes)


def content_hash_bytes(value: bytes) -> str:
    import hashlib

    return hashlib.sha256(value).hexdigest()


def provider_profile_hash(*, profile_ref: str, model: str) -> str:
    return content_hash(
        {
            "provider_profile_ref": profile_ref,
            "model": model,
            "protocol": "POST_JSON_TEXT_SPEAKER_LANGUAGE_TO_PCM_WAV",
        }
    )


def _request_binary(
    url: str,
    payload: dict[str, str],
    timeout_seconds: float,
    max_audio_bytes: int,
) -> bytes:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Accept": "audio/wav, application/octet-stream",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            declared_size = response.headers.get("Content-Length")
            if declared_size is not None and int(declared_size) > max_audio_bytes:
                raise TTSProviderError("mingli_narration_audio_size_invalid")
            payload_bytes = response.read(max_audio_bytes + 1)
    except (
        TimeoutError,
        ValueError,
        urllib.error.HTTPError,
        urllib.error.URLError,
    ) as exc:
        raise TTSProviderError("mingli_narration_provider_failed") from exc
    if len(payload_bytes) > max_audio_bytes:
        raise TTSProviderError("mingli_narration_audio_size_invalid")
    return payload_bytes
