from __future__ import annotations

import io
import wave
from pathlib import Path

from fastapi.testclient import TestClient

from product.agent_case_store import MemoryAgentCaseStore
from product.app import create_product_app
from product.narrated_workspace import NarratedWorkspaceService, SpeechAssetRepository
from product.product_store import MemoryProductStore
from product.theater_performance import SynthesizedSpeech
from core.mingli_agent import MingliAgent
from tests.test_v50_mingli_agent_refoundation import FakeCognitiveModel, _birth_payload


ROOT = Path(__file__).resolve().parents[1]


class _FakeNarrationTTS:
    voice_id = "Eric"

    def __init__(self, *, version: str = "fake-qwen-eric.v1") -> None:
        self.voice_version = version
        self.calls = 0
        self.texts: list[str] = []

    def synthesize(self, text: str) -> SynthesizedSpeech:
        self.calls += 1
        self.texts.append(text)
        target = io.BytesIO()
        with wave.open(target, "wb") as writer:
            writer.setnchannels(1)
            writer.setsampwidth(2)
            writer.setframerate(24_000)
            writer.writeframes(b"\x00\x00" * 24_000)
        return SynthesizedSpeech(wav_bytes=target.getvalue(), generation_seconds=0.02)


def _narrated_case(tmp_path: Path):
    product_store = MemoryProductStore()
    case_store = MemoryAgentCaseStore()
    tts = _FakeNarrationTTS()
    service = NarratedWorkspaceService(
        repository=SpeechAssetRepository(tmp_path / "speech"),
        tts=tts,
    )
    app = create_product_app(
        product_store=product_store,
        mingli_agent=MingliAgent(FakeCognitiveModel()),
        agent_case_store=case_store,
        narrated_workspace_service=service,
    )
    client = TestClient(app)
    registered = client.post(
        "/api/v50/product/auth/register",
        json={
            "display_name": "Narrated Member",
            "email": "narrated-member@example.com",
            "password": "secure-pass-123",
            "role": "member",
        },
    )
    assert registered.status_code == 200, registered.text
    started = client.post(
        "/api/v50/agent/cases",
        json={"birth_input": _birth_payload(), "active_mode": "member"},
    )
    assert started.status_code == 200, started.text
    return app, client, case_store, service, tts, started.json()["case_id"]


def test_manifest_is_a_silent_projection_of_committed_life_case(tmp_path: Path) -> None:
    _, client, case_store, _, tts, case_id = _narrated_case(tmp_path)

    response = client.get(f"/api/v50/narration/cases/{case_id}/baseline")

    assert response.status_code == 200, response.text
    body = response.json()
    manifest = body["manifest"]
    baseline = case_store.get(case_id=case_id)["life_case"]["baseline_insight"]
    assert body["tts_called"] is False
    assert body["llm_used"] is False
    assert tts.calls == 0
    assert manifest["autoplay"] is False
    assert manifest["page_available_without_audio"] is True
    assert manifest["formal_insight_id"] == baseline["insight_id"]
    assert manifest["life_case_version"] == "v1"
    assert [item["kind"] for item in manifest["segments"]][:2] == ["thesis", "work_path"]
    assert all(item["source_claim_refs"] == [baseline["insight_id"]] for item in manifest["segments"])
    assert "baseline-summary" in manifest["segments"][0]["visual_anchor_ids"]


def test_segment_generation_is_immutable_cached_and_private(tmp_path: Path) -> None:
    app, client, _, service, tts, case_id = _narrated_case(tmp_path)
    manifest = client.get(f"/api/v50/narration/cases/{case_id}/baseline").json()["manifest"]
    segment_id = manifest["segments"][0]["segment_id"]

    first = client.post(f"/api/v50/narration/cases/{case_id}/baseline/segments/{segment_id}")
    second = client.post(f"/api/v50/narration/cases/{case_id}/baseline/segments/{segment_id}")

    assert first.status_code == second.status_code == 200
    assert first.json()["cache_hit"] is False
    assert first.json()["tts_called"] is True
    assert second.json()["cache_hit"] is True
    assert second.json()["tts_called"] is False
    assert tts.calls == 1
    asset = first.json()["speech_asset"]
    assert asset["scope"] == "participant_private"
    assert asset["source"]["case_id"] == case_id
    assert asset["source"]["claim_refs"] == [manifest["formal_insight_id"]]
    assert service.repository.get(asset["speech_asset_id"]) is not None
    audio = client.get(asset["media"]["audio_url"])
    assert audio.status_code == 200
    assert audio.content.startswith(b"RIFF")

    anonymous = TestClient(app)
    assert anonymous.get(f"/api/v50/narration/cases/{case_id}/baseline").status_code == 404
    assert anonymous.get(asset["media"]["audio_url"]).status_code == 404


def test_voice_version_changes_the_manifest_and_speech_asset_key(tmp_path: Path) -> None:
    _, client, case_store, service, _, case_id = _narrated_case(tmp_path)
    first_manifest = service.compile_manifest(case_store.get(case_id=case_id))
    first_asset, _ = service.prepare_segment(
        manifest=first_manifest,
        segment_id=first_manifest.segments[0].segment_id,
    )
    replacement_tts = _FakeNarrationTTS(version="fake-qwen-eric.v2")
    replacement = NarratedWorkspaceService(
        repository=service.repository,
        tts=replacement_tts,
    )
    second_manifest = replacement.compile_manifest(case_store.get(case_id=case_id))
    second_asset, cache_hit = replacement.prepare_segment(
        manifest=second_manifest,
        segment_id=second_manifest.segments[0].segment_id,
    )

    assert first_manifest.manifest_id != second_manifest.manifest_id
    assert first_asset.speech_asset_id != second_asset.speech_asset_id
    assert cache_hit is False
    assert replacement_tts.calls == 1


def test_public_workspace_is_opt_in_and_has_bidirectional_page_anchors() -> None:
    html = (ROOT / "apps" / "product" / "static" / "l5" / "index.html").read_text(encoding="utf-8")
    script = (ROOT / "apps" / "product" / "static" / "l5" / "app.js").read_text(encoding="utf-8")
    styles = (ROOT / "apps" / "product" / "static" / "l5" / "styles.css").read_text(encoding="utf-8")

    assert "20260718-voice-validation-v1" in html
    assert "阿布同步论命" in script
    assert "页面先到，声音由你决定" in script
    assert "data-narration-start" in script
    assert "data-narration-jump" in script
    assert "data-narration-anchor" in script
    assert "baseline?.reasoning_path" in script
    assert "baselineWorkPath.conclusion" in script
    assert "new Audio(audioUrl)" in script
    assert ".play()" in script
    assert "autoplay" not in script
    assert "prefers-reduced-motion" in styles
    assert ".narrated-workspace" in styles


class _FakeOpusTranscoder:
    profile_version = "fake-opus.v1"

    def transcode(self, wav_bytes: bytes) -> bytes:
        assert wav_bytes.startswith(b"RIFF")
        return b"OggS" + b"\x00" * 128


def test_new_speech_asset_exposes_private_opus_playback_variant(tmp_path: Path) -> None:
    _, _, case_store, service, tts, case_id = _narrated_case(tmp_path)
    opus_service = NarratedWorkspaceService(
        repository=service.repository,
        tts=tts,
        opus_transcoder=_FakeOpusTranscoder(),
    )
    manifest = opus_service.compile_manifest(case_store.get(case_id=case_id))
    asset, cache_hit = opus_service.prepare_segment(
        manifest=manifest,
        segment_id=manifest.segments[0].segment_id,
    )

    assert cache_hit is False
    assert asset.media.format == "wav"
    assert len(asset.media.playback_variants) == 1
    variant = asset.media.playback_variants[0]
    assert variant.format == "opus"
    assert variant.audio_url.endswith("/opus")
    assert opus_service.repository.variant_path(asset.speech_asset_id, "opus").read_bytes().startswith(b"OggS")
