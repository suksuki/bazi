from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlalchemy import text
from sqlalchemy.engine import Engine

from abu_v60.media.tts import content_hash_bytes
from abu_v60.mingli.narration_contracts import (
    LEGACY_MINGLI_NARRATION_VERSION,
    MINGLI_NARRATION_VERSION,
    MingliNarrationAsset,
    narration_generation_key,
)
from abu_v60.provenance import canonical_json


class MingliNarrationStoreError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class StoredMingliNarration:
    asset: MingliNarrationAsset
    audio_bytes: bytes


_STORED_COLUMNS = """
    narration_ref, narration_version, generation_key,
    requester_account_ref, case_ref, reading_ref, source_scope,
    stage_projection_ref, stage_projection_hash, cue_set_ref,
    script_ref, script_hash, actor_ref, voice_profile_ref,
    voice_profile_hash, provider_profile_ref, provider_profile_hash,
    provider_deployment_ref, audio_mime_type, audio_sha256,
    audio_byte_length, duration_ms, sample_rate_hz, channels,
    sample_width_bytes, narration_json, narration_hash, audio_bytes
"""

_ASSET_SCALAR_FIELDS = (
    "narration_ref",
    "narration_version",
    "requester_account_ref",
    "case_ref",
    "reading_ref",
    "source_scope",
    "stage_projection_ref",
    "stage_projection_hash",
    "cue_set_ref",
    "script_ref",
    "script_hash",
    "actor_ref",
    "voice_profile_ref",
    "voice_profile_hash",
    "audio_mime_type",
    "audio_sha256",
    "audio_byte_length",
    "duration_ms",
    "sample_rate_hz",
    "channels",
    "sample_width_bytes",
    "narration_hash",
)


class MingliNarrationStore:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def by_generation_key(
        self,
        *,
        requester_account_ref: str,
        generation_key: str,
    ) -> StoredMingliNarration | None:
        with self._engine.connect() as connection:
            row = (
                connection.execute(
                    text(
                        f"""
                        SELECT {_STORED_COLUMNS}
                        FROM media.mingli_narration_assets
                        WHERE requester_account_ref = :requester_account_ref
                          AND generation_key = :generation_key
                        """
                    ),
                    {
                        "requester_account_ref": requester_account_ref,
                        "generation_key": generation_key,
                    },
                )
                .mappings()
                .one_or_none()
            )
        return self._decode(row) if row is not None else None

    def owned_asset(
        self,
        *,
        requester_account_ref: str,
        narration_ref: str,
    ) -> StoredMingliNarration | None:
        with self._engine.connect() as connection:
            row = (
                connection.execute(
                    text(
                        f"""
                        SELECT {_STORED_COLUMNS}
                        FROM media.mingli_narration_assets
                        WHERE requester_account_ref = :requester_account_ref
                          AND narration_ref = :narration_ref
                        """
                    ),
                    {
                        "requester_account_ref": requester_account_ref,
                        "narration_ref": narration_ref,
                    },
                )
                .mappings()
                .one_or_none()
            )
        return self._decode(row) if row is not None else None

    def ensure(
        self,
        *,
        generation_key: str,
        asset: MingliNarrationAsset,
        audio_bytes: bytes,
    ) -> StoredMingliNarration:
        if asset.narration_version != MINGLI_NARRATION_VERSION:
            raise MingliNarrationStoreError("mingli_narration_insert_version_unsupported")
        if len(audio_bytes) != asset.audio_byte_length:
            raise MingliNarrationStoreError("mingli_narration_audio_length_mismatch")
        if content_hash_bytes(audio_bytes) != asset.audio_sha256:
            raise MingliNarrationStoreError("mingli_narration_audio_hash_mismatch")
        provider_profile_ref, provider_profile_hash, provider_deployment_ref = (
            self._provider_identity(asset)
        )
        expected_generation_key = narration_generation_key(
            narration_version=asset.narration_version,
            requester_account_ref=asset.requester_account_ref,
            stage_projection_ref=asset.stage_projection_ref,
            stage_projection_hash=asset.stage_projection_hash,
            cue_set_ref=asset.cue_set_ref,
            script_ref=asset.script_ref,
            script_hash=asset.script_hash,
            voice_profile_ref=asset.voice_profile_ref,
            voice_profile_hash=asset.voice_profile_hash,
            provider_profile_ref=provider_profile_ref,
            provider_profile_hash=provider_profile_hash,
            provider_deployment_ref=provider_deployment_ref,
        )
        if generation_key != expected_generation_key:
            raise MingliNarrationStoreError("mingli_narration_generation_key_mismatch")
        with self._engine.begin() as connection:
            connection.execute(
                text(
                    """
                    INSERT INTO media.mingli_narration_assets
                        (narration_ref, narration_version, generation_key,
                         requester_account_ref, case_ref, reading_ref, source_scope,
                         stage_projection_ref, stage_projection_hash, cue_set_ref,
                         script_ref, script_hash, actor_ref,
                         voice_profile_ref, voice_profile_hash,
                         provider_profile_ref, provider_profile_hash,
                         provider_deployment_ref, audio_mime_type, audio_sha256,
                         audio_byte_length, duration_ms, sample_rate_hz, channels,
                         sample_width_bytes, narration_json, narration_hash, audio_bytes)
                    VALUES
                        (:narration_ref, :narration_version, :generation_key,
                         :requester_account_ref, :case_ref, :reading_ref, :source_scope,
                         :stage_projection_ref, :stage_projection_hash, :cue_set_ref,
                         :script_ref, :script_hash, :actor_ref,
                         :voice_profile_ref, :voice_profile_hash,
                         :provider_profile_ref, :provider_profile_hash,
                         :provider_deployment_ref, :audio_mime_type, :audio_sha256,
                         :audio_byte_length, :duration_ms, :sample_rate_hz, :channels,
                         :sample_width_bytes, CAST(:narration_json AS jsonb),
                         :narration_hash, :audio_bytes)
                    ON CONFLICT (generation_key) DO NOTHING
                    """
                ),
                {
                    **asset.model_dump(mode="python", exclude={"cues"}),
                    "generation_key": generation_key,
                    "narration_json": canonical_json(asset.model_dump(mode="json")),
                    "audio_bytes": audio_bytes,
                },
            )
            row = (
                connection.execute(
                    text(
                        f"""
                        SELECT {_STORED_COLUMNS}
                        FROM media.mingli_narration_assets
                        WHERE requester_account_ref = :requester_account_ref
                          AND generation_key = :generation_key
                        """
                    ),
                    {
                        "requester_account_ref": asset.requester_account_ref,
                        "generation_key": generation_key,
                    },
                )
                .mappings()
                .one()
            )
        return self._decode(row)

    @staticmethod
    def _decode(row: Any) -> StoredMingliNarration:
        asset = MingliNarrationAsset.model_validate(row["narration_json"])
        for field in _ASSET_SCALAR_FIELDS:
            if row[field] != getattr(asset, field):
                raise MingliNarrationStoreError(
                    f"mingli_narration_persisted_scalar_mismatch:{field}"
                )
        provider_profile_ref = str(row["provider_profile_ref"])
        provider_profile_hash = str(row["provider_profile_hash"])
        provider_deployment_ref = str(row["provider_deployment_ref"])
        if asset.narration_version == MINGLI_NARRATION_VERSION:
            embedded_provider = MingliNarrationStore._provider_identity(asset)
            if embedded_provider != (
                provider_profile_ref,
                provider_profile_hash,
                provider_deployment_ref,
            ):
                raise MingliNarrationStoreError(
                    "mingli_narration_persisted_provider_mismatch"
                )
        elif asset.narration_version != LEGACY_MINGLI_NARRATION_VERSION:
            raise MingliNarrationStoreError(
                "mingli_narration_persisted_version_unsupported"
            )
        expected_generation_key = narration_generation_key(
            narration_version=asset.narration_version,
            requester_account_ref=asset.requester_account_ref,
            stage_projection_ref=asset.stage_projection_ref,
            stage_projection_hash=asset.stage_projection_hash,
            cue_set_ref=asset.cue_set_ref,
            script_ref=asset.script_ref,
            script_hash=asset.script_hash,
            voice_profile_ref=asset.voice_profile_ref,
            voice_profile_hash=asset.voice_profile_hash,
            provider_profile_ref=provider_profile_ref,
            provider_profile_hash=provider_profile_hash,
            provider_deployment_ref=provider_deployment_ref,
        )
        if row["generation_key"] != expected_generation_key:
            raise MingliNarrationStoreError(
                "mingli_narration_persisted_generation_key_mismatch"
            )
        audio_bytes = bytes(row["audio_bytes"])
        if len(audio_bytes) != asset.audio_byte_length:
            raise MingliNarrationStoreError("mingli_narration_persisted_audio_length_mismatch")
        if content_hash_bytes(audio_bytes) != asset.audio_sha256:
            raise MingliNarrationStoreError("mingli_narration_persisted_audio_hash_mismatch")
        return StoredMingliNarration(asset=asset, audio_bytes=audio_bytes)

    @staticmethod
    def _provider_identity(asset: MingliNarrationAsset) -> tuple[str, str, str]:
        if (
            asset.provider_profile_ref is None
            or asset.provider_profile_hash is None
            or asset.provider_deployment_ref is None
        ):
            raise MingliNarrationStoreError("mingli_narration_provider_identity_required")
        return (
            asset.provider_profile_ref,
            asset.provider_profile_hash,
            asset.provider_deployment_ref,
        )
