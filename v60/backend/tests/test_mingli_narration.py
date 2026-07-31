from __future__ import annotations

import wave
from dataclasses import replace
from datetime import date
from io import BytesIO

import pytest
from abu_v60.db import engine
from abu_v60.media.mingli_narration import MingliNarrationService
from abu_v60.media.mingli_narration_store import (
    MingliNarrationStore,
    MingliNarrationStoreError,
    StoredMingliNarration,
)
from abu_v60.media.tts import Qwen3TTSProvider, TTSProviderError, validate_wav
from abu_v60.mingli.narration_catalog import voice_profile
from abu_v60.mingli.narration_contracts import (
    LEGACY_MINGLI_NARRATION_VERSION,
    MINGLI_NARRATION_VERSION,
    MingliNarrationAsset,
    MingliNarrationPrepareRequest,
    narration_generation_key,
)
from abu_v60.mingli.showcases import seed_mingli_showcases
from abu_v60.mingli.stage import MingliStageService
from abu_v60.mingli.stage_contracts import MingliStageMode
from abu_v60.provenance import content_hash, stable_ref
from abu_v60.settings import TTS_MODEL, settings
from pydantic import ValidationError
from sqlalchemy import text


def _wav(*, frames: int = 2400) -> bytes:
    output = BytesIO()
    with wave.open(output, "wb") as writer:
        writer.setnchannels(1)
        writer.setsampwidth(2)
        writer.setframerate(24000)
        writer.writeframes(b"\x00\x00" * frames)
    return output.getvalue()


def _owner_account_ref() -> str:
    with engine.connect() as connection:
        return str(
            connection.execute(
                text(
                    """
                    SELECT owner_account_ref FROM mingli.cases
                    WHERE subject_kind = 'HUMAN_OWNER' AND status = 'ACTIVE'
                    ORDER BY created_at LIMIT 1
                    """
                )
            ).scalar_one()
        )


class _FakeProvider:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []

    def synthesize(self, *, text: str, speaker: str):
        self.calls.append((text, speaker))
        return validate_wav(_wav(), max_audio_bytes=1024 * 1024)


class _MemoryStore:
    def __init__(self) -> None:
        self.values: dict[str, StoredMingliNarration] = {}

    def by_generation_key(self, *, requester_account_ref: str, generation_key: str):
        return self.values.get(generation_key)

    def ensure(self, *, generation_key: str, asset, audio_bytes: bytes, **_: object):
        stored = StoredMingliNarration(asset=asset, audio_bytes=audio_bytes)
        return self.values.setdefault(generation_key, stored)

    def owned_asset(self, *, requester_account_ref: str, narration_ref: str):
        return next(
            (
                stored
                for stored in self.values.values()
                if stored.asset.requester_account_ref == requester_account_ref
                and stored.asset.narration_ref == narration_ref
            ),
            None,
        )


def _generation_key(asset: MingliNarrationAsset) -> str:
    assert asset.provider_profile_ref is not None
    assert asset.provider_profile_hash is not None
    assert asset.provider_deployment_ref is not None
    return narration_generation_key(
        narration_version=asset.narration_version,
        requester_account_ref=asset.requester_account_ref,
        stage_projection_ref=asset.stage_projection_ref,
        stage_projection_hash=asset.stage_projection_hash,
        cue_set_ref=asset.cue_set_ref,
        script_ref=asset.script_ref,
        script_hash=asset.script_hash,
        voice_profile_ref=asset.voice_profile_ref,
        voice_profile_hash=asset.voice_profile_hash,
        provider_profile_ref=asset.provider_profile_ref,
        provider_profile_hash=asset.provider_profile_hash,
        provider_deployment_ref=asset.provider_deployment_ref,
    )


def _asset_row(
    *,
    asset: MingliNarrationAsset,
    generation_key: str,
    audio_bytes: bytes,
) -> dict[str, object]:
    return {
        **asset.model_dump(mode="python", exclude={"cues"}),
        "generation_key": generation_key,
        "narration_json": asset.model_dump(mode="json"),
        "audio_bytes": audio_bytes,
    }


def test_tts_adapter_sends_only_server_owned_proxy_fields_and_validates_pcm() -> None:
    calls: list[tuple[str, dict[str, str]]] = []

    def transport(url: str, payload: dict[str, str], _: float, __: int) -> bytes:
        calls.append((url, payload))
        return _wav()

    provider = Qwen3TTSProvider(
        enabled=True,
        url="http://192.168.0.7:7860/tts",
        timeout_seconds=2,
        max_audio_bytes=1024 * 1024,
        transport=transport,
    )
    audio = provider.synthesize(text="你好，我是阿布。", speaker="Dylan")

    assert calls == [
        (
            "http://192.168.0.7:7860/tts",
            {"text": "你好，我是阿布。", "speaker": "Dylan", "language": "Chinese"},
        )
    ]
    assert audio.sample_rate_hz == 24000
    assert audio.channels == 1
    assert audio.sample_width_bytes == 2
    with pytest.raises(TTSProviderError, match="audio_not_wav"):
        validate_wav(b"not-wav", max_audio_bytes=1024)


def test_browser_request_cannot_submit_text_speaker_provider_or_url() -> None:
    with pytest.raises(ValidationError):
        MingliNarrationPrepareRequest.model_validate(
            {
                "subject_id": "abu",
                "stage_mode": "NATAL_4",
                "expected_stage_projection_ref": "stage:1",
                "expected_stage_projection_hash": "a" * 64,
                "text": "任意正文",
                "speaker": "Eric",
                "provider": "other",
                "url": "https://example.invalid/tts",
            }
        )


def test_only_owner_selected_dylan_profile_is_labeled_owner_selected() -> None:
    selected = voice_profile("ABU_NARRATOR_V1")
    override = voice_profile("ABU_NARRATOR_V1", speaker="Eric")

    assert selected.speaker == "Dylan"
    assert selected.status == "OWNER_SELECTED"
    assert override.status == "AUDITION_CANDIDATE"
    assert override.voice_profile_ref != selected.voice_profile_ref


def test_tts_endpoint_deployment_and_fixed_model_are_one_admitted_profile() -> None:
    private = replace(
        settings,
        tts_url="http://192.168.0.7:7860/tts",
        tts_provider_deployment_ref="dblife-server13-private-upstream",
    )
    assert private.tts_model == TTS_MODEL

    with pytest.raises(ValueError, match="tts_url_deployment_mismatch"):
        replace(settings, tts_url="http://192.168.0.7:7860/tts")
    with pytest.raises(ValueError, match="tts_model_not_controlled"):
        replace(settings, tts_model="unverified-model-label")


def test_narration_prepares_four_exact_audio_cues_and_replays_without_provider() -> None:
    seed_mingli_showcases(engine)
    account_ref = _owner_account_ref()
    stages = MingliStageService(
        engine,
        current_date_provider=lambda _: date(2026, 8, 1),
    )
    projection = stages.project(
        account_ref=account_ref,
        subject_id="abu",
        stage_mode=MingliStageMode.NATAL_DAYUN_YEAR_6,
        selected_year=2026,
    )
    request = MingliNarrationPrepareRequest(
        subject_id="abu",
        stage_mode=MingliStageMode.NATAL_DAYUN_YEAR_6,
        selected_year=2026,
        expected_stage_projection_ref=projection.projection_ref,
        expected_stage_projection_hash=projection.projection_hash,
    )
    provider = _FakeProvider()
    store = _MemoryStore()
    service = MingliNarrationService(
        engine,
        runtime_settings=replace(
            settings,
            tts_enabled=True,
            tts_max_audio_bytes=1024 * 1024,
        ),
        stages=stages,
        store=store,
        provider=provider,
    )

    first = service.prepare(account_ref=account_ref, request=request)
    replay = service.prepare(account_ref=account_ref, request=request)

    assert first.asset == replay.asset
    assert len(provider.calls) == 4
    assert [cue.cue_id for cue in first.asset.cues] == [
        "STRUCTURE",
        "RELATION_BOUNDARY",
        "EVIDENCE_GAP",
        "TIME_LAYER",
    ]
    assert first.asset.cues[0].start_ms == 0
    assert first.asset.cues[-1].end_ms == first.asset.duration_ms
    assert all(
        left.end_ms == right.start_ms
        for left, right in zip(first.asset.cues, first.asset.cues[1:], strict=False)
    )
    assert first.asset.clock_source == "HTML_AUDIO_CURRENT_TIME"
    assert first.asset.upstream_exposed_to_client is False
    assert first.asset.voice_profile_status == "OWNER_SELECTED"
    assert first.asset.narration_version == MINGLI_NARRATION_VERSION
    assert first.asset.provider_profile_ref == settings.tts_provider_profile_ref
    assert first.asset.provider_deployment_ref == settings.tts_provider_deployment_ref

    generation_key = next(iter(store.values))
    assert generation_key == _generation_key(first.asset)


def test_narration_and_default_stage_share_the_same_voice_settings() -> None:
    seed_mingli_showcases(engine)
    account_ref = _owner_account_ref()
    audition_settings = replace(settings, tts_abu_voice="Eric")
    projection = MingliStageService(
        engine,
        runtime_settings=audition_settings,
    ).project(
        account_ref=account_ref,
        subject_id="abu",
        stage_mode=MingliStageMode.NATAL_4,
    )
    provider = _FakeProvider()
    service = MingliNarrationService(
        engine,
        runtime_settings=audition_settings,
        store=_MemoryStore(),
        provider=provider,
    )

    stored = service.prepare(
        account_ref=account_ref,
        request=MingliNarrationPrepareRequest(
            subject_id="abu",
            stage_mode=MingliStageMode.NATAL_4,
            expected_stage_projection_ref=projection.projection_ref,
            expected_stage_projection_hash=projection.projection_hash,
        ),
    )

    assert projection.narration_voice_status == "AUDITION_CANDIDATE"
    assert stored.asset.voice_profile_status == "AUDITION_CANDIDATE"
    assert {speaker for _, speaker in provider.calls} == {"Eric"}


def test_store_rejects_audio_hash_before_append_only_insert() -> None:
    audio_bytes = _wav()
    cues = tuple(
        {
            "cue_id": cue_id,
            "text": cue_id,
            "start_ms": index * 25,
            "end_ms": (index + 1) * 25,
            "semantic_action": action,
        }
        for index, (cue_id, action) in enumerate(
            (
                ("STRUCTURE", "PILLARS_PRESENT"),
                ("RELATION_BOUNDARY", "RELATIONS_PRESENT"),
                ("EVIDENCE_GAP", "BOUNDARY_HOLD"),
                ("TIME_LAYER", "TIME_COORDINATES_PRESENT"),
            )
        )
    )
    asset = MingliNarrationAsset.issue(
        requester_account_ref=_owner_account_ref(),
        case_ref="v60-case-narration-preinsert-hash-guard",
        reading_ref=None,
        source_scope="CANONICAL_SYNTHETIC_DEMO",
        stage_projection_ref="v60-stage-narration-preinsert-hash-guard",
        stage_projection_hash="1" * 64,
        cue_set_ref="v60.mingli-stage-guide-cues.001",
        script_ref="v60-script-narration-preinsert-hash-guard",
        script_hash="2" * 64,
        actor_ref="ABU_NARRATOR_V1",
        voice_profile_ref="v60.voice-profile.abu-dylan-owner-selected.001",
        voice_profile_hash="3" * 64,
        voice_profile_status="OWNER_SELECTED",
        provider_profile_ref=settings.tts_provider_profile_ref,
        provider_profile_hash="4" * 64,
        provider_deployment_ref=settings.tts_provider_deployment_ref,
        preparation_status="READY",
        audio_mime_type="audio/wav",
        audio_sha256="0" * 64,
        audio_byte_length=len(audio_bytes),
        duration_ms=100,
        sample_rate_hz=24000,
        channels=1,
        sample_width_bytes=2,
        cues=cues,
        clock_source="HTML_AUDIO_CURRENT_TIME",
        refresh_policy="READY_AT_ZERO",
        upstream_exposed_to_client=False,
    )
    store = MingliNarrationStore(engine)
    with pytest.raises(MingliNarrationStoreError, match="audio_hash_mismatch"):
        store.ensure(
            generation_key=_generation_key(asset),
            asset=asset,
            audio_bytes=audio_bytes,
        )
    with engine.connect() as connection:
        count = connection.execute(
            text(
                """
                SELECT count(*) FROM media.mingli_narration_assets
                WHERE narration_ref = :narration_ref
                """
            ),
            {"narration_ref": asset.narration_ref},
        ).scalar_one()
    assert count == 0


def test_store_decode_rejects_scalar_drift_and_accepts_legacy_v1_identity() -> None:
    seed_mingli_showcases(engine)
    provider = _FakeProvider()
    memory = _MemoryStore()
    stages = MingliStageService(
        engine,
        current_date_provider=lambda _: date(2026, 8, 1),
    )
    projection = stages.project(
        account_ref=_owner_account_ref(),
        subject_id="abu",
        stage_mode=MingliStageMode.NATAL_4,
    )
    service = MingliNarrationService(
        engine,
        stages=stages,
        store=memory,
        provider=provider,
    )
    stored = service.prepare(
        account_ref=_owner_account_ref(),
        request=MingliNarrationPrepareRequest(
            subject_id="abu",
            stage_mode=MingliStageMode.NATAL_4,
            expected_stage_projection_ref=projection.projection_ref,
            expected_stage_projection_hash=projection.projection_hash,
        ),
    )
    generation_key = _generation_key(stored.asset)
    drifted = _asset_row(
        asset=stored.asset,
        generation_key=generation_key,
        audio_bytes=stored.audio_bytes,
    )
    drifted["case_ref"] = "wrong-case"
    with pytest.raises(MingliNarrationStoreError, match="scalar_mismatch:case_ref"):
        MingliNarrationStore._decode(drifted)

    legacy_identity = stored.asset.model_dump(
        mode="json",
        exclude={
            "narration_ref",
            "narration_hash",
            "narration_version",
            "provider_profile_ref",
            "provider_profile_hash",
            "provider_deployment_ref",
        },
    )
    legacy_identity["narration_version"] = LEGACY_MINGLI_NARRATION_VERSION
    legacy = MingliNarrationAsset.model_validate(
        {
            "narration_ref": stable_ref("v60-mingli-narration", legacy_identity),
            "narration_hash": content_hash(legacy_identity),
            **legacy_identity,
        }
    )
    legacy_key = narration_generation_key(
        narration_version=LEGACY_MINGLI_NARRATION_VERSION,
        requester_account_ref=legacy.requester_account_ref,
        stage_projection_ref=legacy.stage_projection_ref,
        stage_projection_hash=legacy.stage_projection_hash,
        cue_set_ref=legacy.cue_set_ref,
        script_ref=legacy.script_ref,
        script_hash=legacy.script_hash,
        voice_profile_ref=legacy.voice_profile_ref,
        voice_profile_hash=legacy.voice_profile_hash,
        provider_profile_ref=settings.tts_provider_profile_ref,
        provider_profile_hash=stored.asset.provider_profile_hash or "",
        provider_deployment_ref=settings.tts_provider_deployment_ref,
    )
    legacy_row = _asset_row(
        asset=legacy,
        generation_key=legacy_key,
        audio_bytes=stored.audio_bytes,
    )
    legacy_row.update(
        provider_profile_ref=settings.tts_provider_profile_ref,
        provider_profile_hash=stored.asset.provider_profile_hash,
        provider_deployment_ref=settings.tts_provider_deployment_ref,
    )
    decoded = MingliNarrationStore._decode(legacy_row)
    assert decoded.asset.narration_version == LEGACY_MINGLI_NARRATION_VERSION
