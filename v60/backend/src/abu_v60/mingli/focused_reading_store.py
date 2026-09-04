from __future__ import annotations

from typing import Any

from sqlalchemy import text
from sqlalchemy.engine import Connection, Engine

from abu_v60.mingli.focused_reading_contracts import MingliFocusedReadingEnvelope
from abu_v60.provenance import canonical_json


class MingliFocusedReadingStoreError(ValueError):
    pass


class MingliFocusedReadingStore:
    """Append-only raw and normalized focused prose for one exact Reading."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def ensure(
        self,
        reading: MingliFocusedReadingEnvelope,
    ) -> MingliFocusedReadingEnvelope:
        payload = reading.model_dump(mode="json")
        with self._engine.begin() as connection:
            connection.execute(
                text(
                    """
                    INSERT INTO mingli.focused_readings
                        (focused_reading_ref, focused_reading_version,
                         generation_key, requester_account_ref, case_ref,
                         chart_version_ref, life_case_revision_ref,
                         reading_ref, reading_hash, packet_ref, packet_hash,
                         runtime_ref, provider_id, model_ref, model_digest,
                         provider_profile_ref, provider_profile_hash,
                         prompt_version, prompt_hash, focused_reading_json,
                         focused_reading_hash, input_tokens, output_tokens,
                         total_tokens, duration_ms)
                    VALUES
                        (:focused_reading_ref, :focused_reading_version,
                         :generation_key, :requester_account_ref, :case_ref,
                         :chart_version_ref, :life_case_revision_ref,
                         :reading_ref, :reading_hash, :packet_ref, :packet_hash,
                         :runtime_ref, :provider_id, :model_ref, :model_digest,
                         :provider_profile_ref, :provider_profile_hash,
                         :prompt_version, :prompt_hash,
                         CAST(:focused_reading_json AS jsonb),
                         :focused_reading_hash, :input_tokens, :output_tokens,
                         :total_tokens, :duration_ms)
                    ON CONFLICT DO NOTHING
                    """
                ),
                {
                    **self._columns(reading),
                    "focused_reading_json": canonical_json(payload),
                },
            )
            stored = self._load_by_generation(
                connection,
                requester_account_ref=reading.requester_account_ref,
                generation_key=reading.generation_key,
            )
        if stored is None:
            raise MingliFocusedReadingStoreError("mingli_focused_reading_identity_conflict")
        restored = self._validated(stored)
        if (
            restored.focused_reading_ref != reading.focused_reading_ref
            or restored.focused_reading_hash != reading.focused_reading_hash
        ):
            raise MingliFocusedReadingStoreError("mingli_focused_reading_generation_conflict")
        return restored

    def find_generation(
        self,
        *,
        requester_account_ref: str,
        generation_key: str,
    ) -> MingliFocusedReadingEnvelope | None:
        with self._engine.connect() as connection:
            row = self._load_by_generation(
                connection,
                requester_account_ref=requester_account_ref,
                generation_key=generation_key,
            )
        return None if row is None else self._validated(row)

    def latest(
        self,
        *,
        requester_account_ref: str,
        case_ref: str,
        reading_ref: str,
        reading_hash: str,
        provider_profile_hash: str,
        prompt_hash: str,
    ) -> MingliFocusedReadingEnvelope | None:
        with self._engine.connect() as connection:
            row = (
                connection.execute(
                    text(
                        """
                    SELECT *
                    FROM mingli.focused_readings
                    WHERE requester_account_ref = :requester_account_ref
                      AND case_ref = :case_ref
                      AND reading_ref = :reading_ref
                      AND reading_hash = :reading_hash
                      AND provider_profile_hash = :provider_profile_hash
                      AND prompt_hash = :prompt_hash
                    ORDER BY created_at DESC, focused_reading_ref DESC
                    LIMIT 1
                    """
                    ),
                    {
                        "requester_account_ref": requester_account_ref,
                        "case_ref": case_ref,
                        "reading_ref": reading_ref,
                        "reading_hash": reading_hash,
                        "provider_profile_hash": provider_profile_hash,
                        "prompt_hash": prompt_hash,
                    },
                )
                .mappings()
                .first()
            )
        return None if row is None else self._validated(dict(row))

    @staticmethod
    def _load_by_generation(
        connection: Connection,
        *,
        requester_account_ref: str,
        generation_key: str,
    ) -> dict[str, Any] | None:
        row = (
            connection.execute(
                text(
                    """
                SELECT *
                FROM mingli.focused_readings
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
            .first()
        )
        return None if row is None else dict(row)

    @staticmethod
    def _validated(row: dict[str, Any]) -> MingliFocusedReadingEnvelope:
        reading = MingliFocusedReadingEnvelope.model_validate(row["focused_reading_json"])
        if (
            row["focused_reading_ref"] != reading.focused_reading_ref
            or row["focused_reading_hash"] != reading.focused_reading_hash
            or row["generation_key"] != reading.generation_key
        ):
            raise MingliFocusedReadingStoreError("mingli_focused_reading_row_mismatch")
        return reading

    @staticmethod
    def _columns(reading: MingliFocusedReadingEnvelope) -> dict[str, Any]:
        return {
            "focused_reading_ref": reading.focused_reading_ref,
            "focused_reading_version": reading.focused_reading_version,
            "generation_key": reading.generation_key,
            "requester_account_ref": reading.requester_account_ref,
            "case_ref": reading.case_ref,
            "chart_version_ref": reading.chart_version_ref,
            "life_case_revision_ref": reading.life_case_revision_ref,
            "reading_ref": reading.reading_ref,
            "reading_hash": reading.reading_hash,
            "packet_ref": reading.packet_ref,
            "packet_hash": reading.packet_hash,
            "runtime_ref": reading.runtime_ref,
            "provider_id": reading.provider_id,
            "model_ref": reading.model_ref,
            "model_digest": reading.model_digest,
            "provider_profile_ref": reading.provider_profile_ref,
            "provider_profile_hash": reading.provider_profile_hash,
            "prompt_version": reading.prompt_version,
            "prompt_hash": reading.prompt_hash,
            "focused_reading_hash": reading.focused_reading_hash,
            "input_tokens": reading.input_tokens,
            "output_tokens": reading.output_tokens,
            "total_tokens": reading.total_tokens,
            "duration_ms": reading.duration_ms,
        }
