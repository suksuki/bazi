from __future__ import annotations

import hashlib
import io
import os
import shutil
import subprocess
import threading
import wave
from datetime import datetime, timezone
from pathlib import Path

from experience.canonical_scene import CanonicalProjectionEnvelope
from experience.compiler import canonical_hash
from experience.contracts import (
    ApprovedClaim,
    ApprovedReasoningStep,
    EnvelopeUncertainty,
    MingliExperienceEnvelope,
)
from experience.experiments import MingliVisualCue
from experience.narration import (
    NarrationManifest,
    NarrationSegment,
    SpeechAsset,
    SpeechAssetMedia,
    SpeechAssetMediaVariant,
    SpeechAssetSource,
    SpeechAssetVoice,
    SpeechSubtitleItem,
)
from product.theater_performance import QwenTheaterTTS, TheaterTTS


NARRATION_SCRIPT_VERSION = "baseline-narration.zh.v1"
PRONUNCIATION_LEXICON_VERSION = "mingli-zh.v1"
SPEAKING_STYLE = "calm_companion"
OPUS_CODEC_PROFILE_VERSION = "opus-voice-48k-v1"


class AbuNarrationError(RuntimeError):
    pass


class FfmpegOpusTranscoder:
    def __init__(self, binary: str = "ffmpeg") -> None:
        resolved = shutil.which(binary)
        if not resolved:
            raise AbuNarrationError("ffmpeg_not_available_for_opus")
        self.binary = resolved
        self.profile_version = OPUS_CODEC_PROFILE_VERSION

    def transcode(self, wav_bytes: bytes) -> bytes:
        completed = subprocess.run(
            [
                self.binary,
                "-hide_banner",
                "-loglevel",
                "error",
                "-f",
                "wav",
                "-i",
                "pipe:0",
                "-map_metadata",
                "-1",
                "-c:a",
                "libopus",
                "-application",
                "voip",
                "-b:a",
                "48k",
                "-vbr",
                "on",
                "-compression_level",
                "10",
                "-f",
                "ogg",
                "pipe:1",
            ],
            input=wav_bytes,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if completed.returncode != 0 or not completed.stdout.startswith(b"OggS"):
            detail = completed.stderr.decode("utf-8", errors="replace")[-400:]
            raise AbuNarrationError(f"opus_transcode_failed:{detail}")
        return completed.stdout


class SpeechAssetRepository:
    """Immutable private speech assets keyed by cognition and voice versions."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def metadata_path(self, speech_asset_id: str) -> Path:
        return self.root / f"{_safe_id(speech_asset_id)}.json"

    def audio_path(self, speech_asset_id: str) -> Path:
        return self.root / f"{_safe_id(speech_asset_id)}.wav"

    def variant_path(self, speech_asset_id: str, media_format: str) -> Path:
        if media_format != "opus":
            raise AbuNarrationError("unsupported_speech_asset_variant")
        return self.root / f"{_safe_id(speech_asset_id)}.opus"

    def get(self, speech_asset_id: str) -> SpeechAsset | None:
        path = self.metadata_path(speech_asset_id)
        if not path.exists():
            return None
        asset = SpeechAsset.model_validate_json(path.read_text(encoding="utf-8"))
        audio_path = self.audio_path(speech_asset_id)
        if not audio_path.exists() or _sha256(audio_path.read_bytes()) != asset.media.audio_hash:
            raise AbuNarrationError("speech_asset_audio_missing_or_corrupt")
        for variant in asset.media.playback_variants:
            variant_path = self.variant_path(speech_asset_id, variant.format)
            if not variant_path.exists() or _sha256(variant_path.read_bytes()) != variant.audio_hash:
                raise AbuNarrationError("speech_asset_variant_missing_or_corrupt")
        return asset

    def save(
        self,
        asset: SpeechAsset,
        audio_bytes: bytes,
        *,
        variant_bytes: dict[str, bytes] | None = None,
    ) -> None:
        variant_bytes = variant_bytes or {}
        metadata_path = self.metadata_path(asset.speech_asset_id)
        audio_path = self.audio_path(asset.speech_asset_id)
        if metadata_path.exists() or audio_path.exists():
            existing = self.get(asset.speech_asset_id)
            if not existing or existing != asset:
                raise AbuNarrationError("immutable_speech_asset_conflict")
            return
        audio_tmp = audio_path.with_suffix(".wav.tmp")
        metadata_tmp = metadata_path.with_suffix(".json.tmp")
        audio_tmp.write_bytes(audio_bytes)
        variant_tmps: list[tuple[Path, Path]] = []
        for variant in asset.media.playback_variants:
            payload = variant_bytes.get(variant.format)
            if payload is None or _sha256(payload) != variant.audio_hash:
                raise AbuNarrationError("speech_asset_variant_payload_mismatch")
            variant_path = self.variant_path(asset.speech_asset_id, variant.format)
            variant_tmp = variant_path.with_suffix(f".{variant.format}.tmp")
            variant_tmp.write_bytes(payload)
            variant_tmps.append((variant_tmp, variant_path))
        metadata_tmp.write_text(asset.model_dump_json(indent=2), encoding="utf-8")
        audio_tmp.replace(audio_path)
        for variant_tmp, variant_path in variant_tmps:
            variant_tmp.replace(variant_path)
        metadata_tmp.replace(metadata_path)


class AbuNarrationService:
    def __init__(
        self,
        *,
        repository: SpeechAssetRepository,
        tts: TheaterTTS,
        opus_transcoder: FfmpegOpusTranscoder | None = None,
    ) -> None:
        self.repository = repository
        self.tts = tts
        self.opus_transcoder = opus_transcoder
        self._generation_lock = threading.Lock()

    @classmethod
    def from_environment(cls) -> "AbuNarrationService":
        root = Path(
            os.getenv("V50_NARRATION_MEDIA_DIR", "/tmp/deepbazi-v50-narration")
        ).expanduser()
        opus_enabled = os.getenv("V50_NARRATION_OPUS_ENABLED", "1").strip().lower() not in {
            "0",
            "false",
            "no",
        }
        transcoder = None
        if opus_enabled:
            try:
                transcoder = FfmpegOpusTranscoder(
                    os.getenv("V50_FFMPEG_BINARY", "ffmpeg").strip() or "ffmpeg"
                )
            except AbuNarrationError:
                transcoder = None
        return cls(
            repository=SpeechAssetRepository(root),
            tts=QwenTheaterTTS.from_environment(),
            opus_transcoder=transcoder,
        )

    def compile_manifest(
        self,
        projection: CanonicalProjectionEnvelope,
    ) -> NarrationManifest:
        if projection.projection_kind != "abu":
            raise AbuNarrationError("canonical_abu_projection_required")
        try:
            claims = [
                ApprovedClaim.model_validate(item)
                for item in projection.payload.get("approved_claims") or []
            ]
            reasoning_steps = [
                ApprovedReasoningStep.model_validate(item)
                for item in projection.payload.get("approved_reasoning_steps") or []
            ]
            uncertainty = EnvelopeUncertainty.model_validate(
                projection.payload.get("uncertainty") or {}
            )
        except Exception as exc:  # noqa: BLE001 - projection boundary rejects malformed data.
            raise AbuNarrationError("canonical_abu_projection_invalid") from exc
        baseline = next((item for item in claims if item.category == "baseline"), None)
        if baseline is None:
            raise AbuNarrationError("canonical_baseline_claim_not_available")
        segments = _compile_segments(
            baseline=baseline,
            reasoning_steps=reasoning_steps,
            uncertainty=uncertainty,
        )
        if not segments:
            raise AbuNarrationError("narration_has_no_approved_segments")
        identity = projection.scene_identity
        stable = {
            "scope": "participant_private",
            "case_id": identity.case_ref,
            "chart_version": identity.chart_version_id,
            "life_case_version": identity.life_case_version,
            "formal_insight_id": baseline.claim_ref,
            "narration_script_version": NARRATION_SCRIPT_VERSION,
            "mode": "standard",
            "language": "zh-CN",
            "voice_id": self.tts.voice_id,
            "voice_version": self.tts.voice_version,
            "segments": [item.model_dump(mode="json") for item in segments],
            "compiled_at": identity.source_updated_at.isoformat(),
            "autoplay": False,
            "page_available_without_audio": True,
        }
        manifest_hash = canonical_hash({
            "scene_id": identity.scene_id,
            "projection_hash": projection.projection_hash,
            "manifest": stable,
        })
        return NarrationManifest(
            manifest_id=f"narration-{manifest_hash[:24]}",
            manifest_hash=manifest_hash,
            **stable,
        )

    def compile_chart_facts_manifest(
        self,
        envelope: MingliExperienceEnvelope,
    ) -> NarrationManifest:
        """Narrate deterministic chart facts when no formal baseline exists yet."""

        facts = [item for item in envelope.allowed_chart_facts if item.fact_type == "pillar"]
        if len(facts) != 4 or envelope.source.case_ref is None:
            raise AbuNarrationError("deterministic_four_pillars_not_available")
        pillar_text = "，".join(
            f"{item.pillar_label}是{item.stem}{item.branch}"
            for item in facts
        )
        day = next((item for item in facts if item.pillar_slot == "day"), facts[2])
        refs = [item.fact_ref for item in facts]
        segments = [
            NarrationSegment(
                segment_id="chart-facts-four-pillars",
                order=0,
                kind="thesis",
                title="先看四柱",
                text=f"我们先看已经确定的命盘底图。{pillar_text}。",
                source_claim_refs=["deterministic:four-pillars"],
                source_refs=refs,
                visual_anchor_ids=["four-pillars"],
                estimated_duration_seconds=12,
            ),
            NarrationSegment(
                segment_id="chart-facts-boundary",
                order=1,
                kind="uncertainty",
                title="先守住事实边界",
                text=(
                    f"日主是{day.stem}。四柱、十神和藏干可以直接查看；"
                    "整盘主线仍按每一条证据分别核验，我不会把未通过的判断说成结论。"
                ),
                source_claim_refs=["deterministic:chart-boundary"],
                source_refs=[day.fact_ref],
                visual_anchor_ids=["baseline-uncertainty"],
                estimated_duration_seconds=14,
            ),
        ]
        stable = {
            "scope": "participant_private",
            "case_id": envelope.source.case_ref,
            "chart_version": envelope.source.chart_version,
            "life_case_version": "chart-facts-only",
            "formal_insight_id": "deterministic-chart-facts",
            "narration_script_version": "chart-facts-narration.zh.v1",
            "mode": "standard",
            "language": "zh-CN",
            "voice_id": self.tts.voice_id,
            "voice_version": self.tts.voice_version,
            "segments": [item.model_dump(mode="json") for item in segments],
            "compiled_at": envelope.source.generated_at.isoformat(),
            "autoplay": False,
            "page_available_without_audio": True,
        }
        manifest_hash = canonical_hash({
            "source_hash": envelope.source.source_hash,
            "manifest": stable,
        })
        return NarrationManifest(
            manifest_id=f"narration-{manifest_hash[:24]}",
            manifest_hash=manifest_hash,
            **stable,
        )

    def asset_id(self, *, manifest: NarrationManifest, segment: NarrationSegment) -> str:
        key = canonical_hash(
            {
                "scope": manifest.scope,
                "case_id": manifest.case_id,
                "chart_version": manifest.chart_version,
                "life_case_version": manifest.life_case_version,
                "formal_insight_id": manifest.formal_insight_id,
                "segment_id": segment.segment_id,
                "claim_refs": segment.source_claim_refs,
                "source_refs": segment.source_refs,
                "source_text_hash": _sha256(segment.text.encode("utf-8")),
                "narration_script_version": manifest.narration_script_version,
                "language": manifest.language,
                "voice_id": manifest.voice_id,
                "voice_version": manifest.voice_version,
                "tts_model_version": self.tts.voice_version,
                "pronunciation_lexicon_version": PRONUNCIATION_LEXICON_VERSION,
                "speaking_style": SPEAKING_STYLE,
                "speed": 1.0,
                "playback_codec_profile": (
                    self.opus_transcoder.profile_version if self.opus_transcoder else "wav-only"
                ),
            }
        )
        return f"speech-{key[:24]}"

    def asset_statuses(self, manifest: NarrationManifest) -> dict[str, dict[str, str]]:
        statuses: dict[str, dict[str, str]] = {}
        for segment in manifest.segments:
            asset_id = self.asset_id(manifest=manifest, segment=segment)
            asset = self.repository.get(asset_id)
            statuses[segment.segment_id] = {
                "status": "ready" if asset else "missing",
                "speech_asset_id": asset_id,
                "audio_url": _preferred_audio_url(asset) if asset else "",
                "audio_format": _preferred_audio_format(asset) if asset else "",
            }
        return statuses

    def prepare_segment(
        self,
        *,
        manifest: NarrationManifest,
        segment_id: str,
    ) -> tuple[SpeechAsset, bool]:
        segment = next((item for item in manifest.segments if item.segment_id == segment_id), None)
        if segment is None:
            raise AbuNarrationError("narration_segment_not_found")
        speech_asset_id = self.asset_id(manifest=manifest, segment=segment)
        existing = self.repository.get(speech_asset_id)
        if existing:
            return existing, True
        with self._generation_lock:
            existing = self.repository.get(speech_asset_id)
            if existing:
                return existing, True
            speech = self.tts.synthesize(segment.text)
            sample_rate, duration_ms = _wav_metadata(speech.wav_bytes)
            audio_hash = _sha256(speech.wav_bytes)
            variants: list[SpeechAssetMediaVariant] = []
            variant_bytes: dict[str, bytes] = {}
            if self.opus_transcoder is not None:
                try:
                    opus_bytes = self.opus_transcoder.transcode(speech.wav_bytes)
                except AbuNarrationError:
                    opus_bytes = b""
                if opus_bytes:
                    variant_bytes["opus"] = opus_bytes
                    variants.append(
                        SpeechAssetMediaVariant(
                            audio_url=(
                                f"/api/v50/narration/cases/{manifest.case_id}/audio/"
                                f"{speech_asset_id}/opus"
                            ),
                            audio_hash=_sha256(opus_bytes),
                            size_bytes=len(opus_bytes),
                            codec_profile_version=self.opus_transcoder.profile_version,
                        )
                    )
            asset = SpeechAsset(
                speech_asset_id=speech_asset_id,
                source=SpeechAssetSource(
                    case_id=manifest.case_id,
                    chart_version=manifest.chart_version,
                    life_case_version=manifest.life_case_version,
                    formal_insight_id=manifest.formal_insight_id,
                    segment_id=segment.segment_id,
                    claim_refs=segment.source_claim_refs,
                    source_refs=segment.source_refs,
                    narration_script_version=manifest.narration_script_version,
                    source_text_hash=_sha256(segment.text.encode("utf-8")),
                ),
                voice=SpeechAssetVoice(
                    voice_id=manifest.voice_id,
                    voice_version=manifest.voice_version,
                    tts_model_version=self.tts.voice_version,
                    language=manifest.language,
                    speaking_style=SPEAKING_STYLE,
                    speed=1.0,
                    pronunciation_lexicon_version=PRONUNCIATION_LEXICON_VERSION,
                ),
                media=SpeechAssetMedia(
                    audio_url=(
                        f"/api/v50/narration/cases/{manifest.case_id}/audio/{speech_asset_id}"
                    ),
                    audio_hash=audio_hash,
                    duration_ms=duration_ms,
                    sample_rate=sample_rate,
                    subtitle_track=[
                        SpeechSubtitleItem(start_ms=0, end_ms=duration_ms, text=segment.text)
                    ],
                    size_bytes=len(speech.wav_bytes),
                    playback_variants=variants,
                ),
                generated_at=datetime.now(timezone.utc),
                generation_seconds=speech.generation_seconds,
            )
            self.repository.save(asset, speech.wav_bytes, variant_bytes=variant_bytes)
            return asset, False


def _compile_segments(
    *,
    baseline: ApprovedClaim,
    reasoning_steps: list[ApprovedReasoningStep],
    uncertainty: EnvelopeUncertainty,
) -> list[NarrationSegment]:
    common_refs = _unique(
        [
            *baseline.evidence_refs,
            *(ref for step in reasoning_steps for ref in step.source_refs),
        ]
    )
    segments: list[NarrationSegment] = []

    def add(
        *,
        kind: str,
        title: str,
        text: str,
        anchor: str,
        source_refs: list[str],
        cues: list[MingliVisualCue],
    ) -> None:
        cleaned = " ".join(text.split()).strip()
        if not cleaned:
            return
        order = len(segments)
        segments.append(
            NarrationSegment(
                segment_id=f"baseline-{kind}",
                order=order,
                kind=kind,
                title=title,
                text=cleaned,
                source_claim_refs=[baseline.claim_ref],
                source_refs=_unique(source_refs),
                visual_anchor_ids=[anchor],
                visual_cues=cues,
                estimated_duration_seconds=_estimated_duration(cleaned),
            )
        )

    add(
        kind="thesis",
        title="整盘重心",
        text=f"先看整盘重心。{baseline.approved_meaning}",
        anchor="baseline-summary",
        source_refs=common_refs,
        cues=[
            MingliVisualCue(at_ms=0, action="focus", target="baseline-summary"),
            MingliVisualCue(at_ms=500, action="reveal", target="baseline-pillar-0"),
            MingliVisualCue(at_ms=850, action="reveal", target="baseline-pillar-1"),
            MingliVisualCue(at_ms=1200, action="reveal", target="baseline-pillar-2"),
            MingliVisualCue(at_ms=1550, action="reveal", target="baseline-pillar-3"),
        ],
    )
    baseline_reasoning = [
        item
        for item in reasoning_steps
        if item.step_ref.startswith(f"{baseline.claim_ref}.reasoning.")
    ]
    work_path = baseline_reasoning[-1] if baseline_reasoning else None
    if work_path and work_path.conclusion.strip() != baseline.approved_meaning.strip():
        add(
            kind="work_path",
            title="主路径",
            text=f"再看这张盘怎么运行。{work_path.conclusion}",
            anchor="baseline-work-path",
            source_refs=[*common_refs, *work_path.source_refs],
            cues=[MingliVisualCue(at_ms=0, action="flow", target="baseline-work-path")],
        )
    if baseline.conditions:
        add(
            kind="condition",
            title="关键条件",
            text=f"这条理解成立，要先满足一个条件：{baseline.conditions[0]}",
            anchor="baseline-condition",
            source_refs=common_refs,
            cues=[MingliVisualCue(at_ms=0, action="focus", target="baseline-condition")],
        )
    if uncertainty.reasons:
        add(
            kind="uncertainty",
            title="仍未写满",
            text=f"还有一处我不会替你写满：{uncertainty.reasons[0]}",
            anchor="baseline-uncertainty",
            source_refs=common_refs,
            cues=[MingliVisualCue(at_ms=0, action="pulse", target="baseline-uncertainty")],
        )
    return segments


def _estimated_duration(text: str) -> int:
    return min(25, max(8, round(len(text) / 4.2)))


def _wav_metadata(wav_bytes: bytes) -> tuple[int, int]:
    try:
        with wave.open(io.BytesIO(wav_bytes), "rb") as reader:
            sample_rate = reader.getframerate()
            duration_ms = max(1, round(reader.getnframes() / sample_rate * 1000))
    except (wave.Error, EOFError) as exc:
        raise AbuNarrationError("tts_response_is_not_valid_wav") from exc
    return sample_rate, duration_ms


def _safe_id(value: str) -> str:
    if not value or any(
        character not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
        for character in value
    ):
        raise AbuNarrationError("invalid_speech_asset_id")
    return value


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _unique(values: list[str]) -> list[str]:
    return list(dict.fromkeys(value for value in values if value))


def _preferred_audio_url(asset: SpeechAsset) -> str:
    opus = next((item for item in asset.media.playback_variants if item.format == "opus"), None)
    return opus.audio_url if opus else asset.media.audio_url


def _preferred_audio_format(asset: SpeechAsset) -> str:
    return "opus" if any(item.format == "opus" for item in asset.media.playback_variants) else "wav"
