from __future__ import annotations

from typing import Any

from sqlalchemy import text
from sqlalchemy.engine import Connection, Engine

from abu_v60.mingli.focused_reading_contracts import (
    MINGLI_FOCUS_ORDER,
    MingliFocus,
    MingliFocusedPassRecord,
)
from abu_v60.provenance import canonical_json


class MingliFocusedPassStoreError(ValueError):
    pass


class MingliFocusedPassStore:
    """Append-only independently replayable focused passes."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def ensure(self, record: MingliFocusedPassRecord) -> MingliFocusedPassRecord:
        with self._engine.begin() as connection:
            connection.execute(
                text(
                    """
                    INSERT INTO mingli.focused_pass_records
                        (record_ref, record_version, generation_key,
                         requester_account_ref, case_ref, chart_version_ref,
                         life_case_revision_ref, reading_ref, reading_hash,
                         packet_ref, packet_hash, runtime_ref, provider_id,
                         model_ref, model_digest, provider_profile_ref,
                         provider_profile_hash, prompt_version, prompt_hash,
                         focus, structure_pass_hash, pass_json, record_hash,
                         pass_hash,
                         input_tokens, output_tokens, total_tokens, duration_ms)
                    VALUES
                        (:record_ref, :record_version, :generation_key,
                         :requester_account_ref, :case_ref, :chart_version_ref,
                         :life_case_revision_ref, :reading_ref, :reading_hash,
                         :packet_ref, :packet_hash, :runtime_ref, :provider_id,
                         :model_ref, :model_digest, :provider_profile_ref,
                         :provider_profile_hash, :prompt_version, :prompt_hash,
                         :focus, :structure_pass_hash,
                         CAST(:pass_json AS jsonb), :record_hash, :pass_hash,
                         :input_tokens, :output_tokens, :total_tokens,
                         :duration_ms)
                    ON CONFLICT DO NOTHING
                    """
                ),
                {
                    **self._columns(record),
                    "pass_json": canonical_json(record.model_dump(mode="json")),
                },
            )
            stored = self._load_by_generation(
                connection,
                requester_account_ref=record.requester_account_ref,
                generation_key=record.generation_key,
            )
        if stored is None:
            raise MingliFocusedPassStoreError("mingli_focused_pass_identity_conflict")
        restored = self._validated(stored)
        if restored.record_ref != record.record_ref or restored.record_hash != record.record_hash:
            raise MingliFocusedPassStoreError("mingli_focused_pass_generation_conflict")
        return restored

    def find_generation(
        self,
        *,
        requester_account_ref: str,
        generation_key: str,
    ) -> MingliFocusedPassRecord | None:
        with self._engine.connect() as connection:
            row = self._load_by_generation(
                connection,
                requester_account_ref=requester_account_ref,
                generation_key=generation_key,
            )
        return None if row is None else self._validated(row)

    def owned_record(
        self,
        *,
        requester_account_ref: str,
        record_ref: str,
    ) -> MingliFocusedPassRecord | None:
        with self._engine.connect() as connection:
            row = (
                connection.execute(
                    text(
                        """
                    SELECT *
                    FROM mingli.focused_pass_records
                    WHERE requester_account_ref = :requester_account_ref
                      AND record_ref = :record_ref
                    """
                    ),
                    {
                        "requester_account_ref": requester_account_ref,
                        "record_ref": record_ref,
                    },
                )
                .mappings()
                .first()
            )
        return None if row is None else self._validated(dict(row))

    def latest(
        self,
        *,
        requester_account_ref: str,
        case_ref: str,
        reading_ref: str,
        reading_hash: str,
        provider_profile_hash: str,
        prompt_hash: str,
        focus: MingliFocus,
    ) -> MingliFocusedPassRecord | None:
        with self._engine.connect() as connection:
            row = (
                connection.execute(
                    text(
                        """
                    SELECT *
                    FROM mingli.focused_pass_records
                    WHERE requester_account_ref = :requester_account_ref
                      AND case_ref = :case_ref
                      AND reading_ref = :reading_ref
                      AND reading_hash = :reading_hash
                      AND provider_profile_hash = :provider_profile_hash
                      AND prompt_hash = :prompt_hash
                      AND focus = :focus
                    ORDER BY created_at DESC, record_ref DESC
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
                        "focus": focus,
                    },
                )
                .mappings()
                .first()
            )
        return None if row is None else self._validated(dict(row))

    def latest_all(
        self,
        *,
        requester_account_ref: str,
        case_ref: str,
        reading_ref: str,
        reading_hash: str,
        provider_profile_hash: str,
        prompt_hash: str,
    ) -> tuple[MingliFocusedPassRecord, ...]:
        with self._engine.connect() as connection:
            rows = (
                connection.execute(
                    text(
                        """
                    SELECT DISTINCT ON (focus) *
                    FROM mingli.focused_pass_records
                    WHERE requester_account_ref = :requester_account_ref
                      AND case_ref = :case_ref
                      AND reading_ref = :reading_ref
                      AND reading_hash = :reading_hash
                      AND provider_profile_hash = :provider_profile_hash
                      AND prompt_hash = :prompt_hash
                    ORDER BY focus, created_at DESC, record_ref DESC
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
                .all()
            )
        by_focus = {record.focus: record for record in (self._validated(dict(row)) for row in rows)}
        return tuple(by_focus[focus] for focus in MINGLI_FOCUS_ORDER if focus in by_focus)

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
                FROM mingli.focused_pass_records
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
    def _validated(row: dict[str, Any]) -> MingliFocusedPassRecord:
        record = MingliFocusedPassRecord.model_validate(row["pass_json"])
        if (
            row["record_ref"] != record.record_ref
            or row["record_hash"] != record.record_hash
            or row["generation_key"] != record.generation_key
            or row["focus"] != record.focus
            or row["pass_hash"] != record.pass_result.pass_hash
        ):
            raise MingliFocusedPassStoreError("mingli_focused_pass_row_mismatch")
        return record

    @staticmethod
    def _columns(record: MingliFocusedPassRecord) -> dict[str, Any]:
        result = record.pass_result
        return {
            "record_ref": record.record_ref,
            "record_version": record.record_version,
            "generation_key": record.generation_key,
            "requester_account_ref": record.requester_account_ref,
            "case_ref": record.case_ref,
            "chart_version_ref": record.chart_version_ref,
            "life_case_revision_ref": record.life_case_revision_ref,
            "reading_ref": record.reading_ref,
            "reading_hash": record.reading_hash,
            "packet_ref": record.packet_ref,
            "packet_hash": record.packet_hash,
            "runtime_ref": record.runtime_ref,
            "provider_id": record.provider_id,
            "model_ref": record.model_ref,
            "model_digest": record.model_digest,
            "provider_profile_ref": record.provider_profile_ref,
            "provider_profile_hash": record.provider_profile_hash,
            "prompt_version": record.prompt_version,
            "prompt_hash": record.prompt_hash,
            "focus": record.focus,
            "structure_pass_hash": record.structure_pass_hash,
            "record_hash": record.record_hash,
            "pass_hash": result.pass_hash,
            "input_tokens": result.input_tokens,
            "output_tokens": result.output_tokens,
            "total_tokens": result.total_tokens,
            "duration_ms": result.duration_ms,
        }
