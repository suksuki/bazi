from __future__ import annotations

import io
import wave
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from product.agent_case_store import MemoryAgentCaseStore
from product.app import create_product_app
from product.canonical_scene import CanonicalSceneOwner
from product.abu_narration import AbuNarrationService, SpeechAssetRepository
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
    service = AbuNarrationService(
        repository=SpeechAssetRepository(tmp_path / "speech"),
        tts=tts,
    )
    app = create_product_app(
        product_store=product_store,
        mingli_agent=MingliAgent(FakeCognitiveModel()),
        agent_case_store=case_store,
        abu_narration_service=service,
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


def _manifest(
    *,
    service: AbuNarrationService,
    case_store: MemoryAgentCaseStore,
    case_id: str,
):
    row = case_store.get(case_id=case_id)
    assert row is not None
    projection = CanonicalSceneOwner(case_store=case_store).issue_projection(
        case_id=case_id,
        participant_id=str(row["user_id"]),
        account_role="member",
        projection_kind="abu",
    )
    return service.compile_manifest(projection)


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


def test_manifest_reads_the_case_once_through_canonical_scene_owner(tmp_path: Path) -> None:
    _, client, case_store, _, _, case_id = _narrated_case(tmp_path)

    with patch.object(case_store, "get", wraps=case_store.get) as get_case:
        response = client.get(f"/api/v50/narration/cases/{case_id}/baseline")

    assert response.status_code == 200, response.text
    assert get_case.call_count == 1


def test_manifest_ignores_legacy_record_and_uses_canonical_abu_projection(
    tmp_path: Path,
) -> None:
    _, client, case_store, _, _, case_id = _narrated_case(tmp_path)
    before = client.get(f"/api/v50/narration/cases/{case_id}/baseline")
    row = case_store.get(case_id=case_id)
    assert row is not None
    row["record"] = {"legacy_claim": "THIS MUST NOT BECOME ABU NARRATION"}
    case_store.save(
        case_id=case_id,
        user_id=str(row["user_id"]),
        profile_id=row.get("profile_id"),
        payload=row,
    )
    after = client.get(f"/api/v50/narration/cases/{case_id}/baseline")

    assert before.status_code == after.status_code == 200
    assert before.json()["manifest"] == after.json()["manifest"]
    assert "THIS MUST NOT" not in str(after.json())


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
    first_manifest = _manifest(service=service, case_store=case_store, case_id=case_id)
    first_asset, _ = service.prepare_segment(
        manifest=first_manifest,
        segment_id=first_manifest.segments[0].segment_id,
    )
    replacement_tts = _FakeNarrationTTS(version="fake-qwen-eric.v2")
    replacement = AbuNarrationService(
        repository=service.repository,
        tts=replacement_tts,
    )
    second_manifest = _manifest(service=replacement, case_store=case_store, case_id=case_id)
    second_asset, cache_hit = replacement.prepare_segment(
        manifest=second_manifest,
        segment_id=second_manifest.segments[0].segment_id,
    )

    assert first_manifest.manifest_id != second_manifest.manifest_id
    assert first_asset.speech_asset_id != second_asset.speech_asset_id
    assert cache_hit is False
    assert replacement_tts.calls == 1


def test_public_workspace_is_opt_in_and_has_bidirectional_page_anchors() -> None:
    components = (ROOT / "apps/product/experience_shell/src/components.ts").read_text(encoding="utf-8")
    audio = (ROOT / "apps/product/experience_shell/src/audio.ts").read_text(encoding="utf-8")
    styles = (ROOT / "apps/product/static/experience/styles.css").read_text(encoding="utf-8")

    assert "阿布同步论命" in components
    assert 'data-command="listen"' in components
    assert "data-play-segment" in components
    assert "data-select-anchor" in components
    assert "new Audio(audioUrl)" in audio
    assert ".play()" in audio
    assert "autoplay" not in audio
    assert "prefers-reduced-motion" in styles
    assert ".narration-workspace" in styles


class _FakeOpusTranscoder:
    profile_version = "fake-opus.v1"

    def transcode(self, wav_bytes: bytes) -> bytes:
        assert wav_bytes.startswith(b"RIFF")
        return b"OggS" + b"\x00" * 128


def test_new_speech_asset_exposes_private_opus_playback_variant(tmp_path: Path) -> None:
    _, _, case_store, service, tts, case_id = _narrated_case(tmp_path)
    opus_service = AbuNarrationService(
        repository=service.repository,
        tts=tts,
        opus_transcoder=_FakeOpusTranscoder(),
    )
    manifest = _manifest(service=opus_service, case_store=case_store, case_id=case_id)
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
