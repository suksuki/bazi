from __future__ import annotations

from typing import Any

from sqlalchemy import text
from sqlalchemy.engine import Connection, Engine

from abu_v60.mingli.agent_contracts import (
    MINGLI_AGENT_READING_VERSION,
    MingliAgentReadingEnvelope,
)
from abu_v60.provenance import canonical_json


class MingliAgentReadingStoreError(ValueError):
    pass


class MingliAgentReadingNotFoundError(MingliAgentReadingStoreError):
    pass


class MingliAgentReadingStore:
    """Append-only private interpretations, pinned to one exact base Reading."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def ensure(
        self,
        reading: MingliAgentReadingEnvelope,
    ) -> MingliAgentReadingEnvelope:
        payload = reading.model_dump(mode="json")
        with self._engine.begin() as connection:
            result = connection.execute(
                text(
                    """
                    INSERT INTO mingli.agent_readings
                        (agent_reading_ref, agent_reading_version,
                         generation_key, requester_account_ref, case_ref,
                         chart_version_ref, life_case_revision_ref,
                         reading_ref, reading_hash, packet_ref, packet_hash,
                         agent_profile_ref, agent_profile_hash, provider_id,
                         model_ref, model_digest, provider_profile_ref,
                         provider_profile_hash, prompt_ref, prompt_hash,
                         provider_response_ref, interpretation_status,
                         owner_review_status, canonical_fact_write_allowed,
                         read_only, agent_reading_json,
                         agent_reading_hash, input_tokens, output_tokens,
                         total_tokens, duration_ms)
                    VALUES
                        (:agent_reading_ref, :agent_reading_version,
                         :generation_key, :requester_account_ref, :case_ref,
                         :chart_version_ref, :life_case_revision_ref,
                         :reading_ref, :reading_hash, :packet_ref, :packet_hash,
                         :agent_profile_ref, :agent_profile_hash, :provider_id,
                         :model_ref, :model_digest, :provider_profile_ref,
                         :provider_profile_hash, :prompt_ref, :prompt_hash,
                         :provider_response_ref, :interpretation_status,
                         :owner_review_status, :canonical_fact_write_allowed,
                         :read_only, CAST(:agent_reading_json AS jsonb),
                         :agent_reading_hash, :input_tokens, :output_tokens,
                         :total_tokens, :duration_ms)
                    ON CONFLICT DO NOTHING
                    """
                ),
                {
                    **self._exact(reading),
                    "agent_reading_json": canonical_json(payload),
                },
            )
            row = self._load_by_generation_key(
                connection,
                requester_account_ref=reading.requester_account_ref,
                generation_key=reading.generation_key,
            )
            if row is None:
                raise MingliAgentReadingStoreError("mingli_agent_reading_identity_conflict")
            stored = self._validated(row)
            if result.rowcount == 1:
                self._verify_row(row, expected=reading)
            else:
                self._verify_generation_identity(stored, requested=reading)
        return stored

    def get(
        self,
        *,
        requester_account_ref: str,
        agent_reading_ref: str,
    ) -> MingliAgentReadingEnvelope:
        with self._engine.connect() as connection:
            row = self._load_by_ref(
                connection,
                requester_account_ref=requester_account_ref,
                agent_reading_ref=agent_reading_ref,
            )
        if row is None:
            raise MingliAgentReadingNotFoundError("mingli_agent_reading_not_found")
        return self._validated(row)

    def find_generation(
        self,
        *,
        requester_account_ref: str,
        generation_key: str,
    ) -> MingliAgentReadingEnvelope | None:
        with self._engine.connect() as connection:
            row = self._load_by_generation_key(
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
        agent_profile_ref: str,
        agent_profile_hash: str,
        provider_profile_ref: str,
        provider_profile_hash: str,
        prompt_ref: str,
        prompt_hash: str,
    ) -> MingliAgentReadingEnvelope | None:
        with self._engine.connect() as connection:
            row = (
                connection.execute(
                    text(
                        f"""
                        {self._select_sql()}
                        WHERE requester_account_ref = :requester_account_ref
                          AND case_ref = :case_ref
                          AND reading_ref = :reading_ref
                          AND reading_hash = :reading_hash
                          AND agent_reading_version = :agent_reading_version
                          AND agent_profile_ref = :agent_profile_ref
                          AND agent_profile_hash = :agent_profile_hash
                          AND provider_profile_ref = :provider_profile_ref
                          AND provider_profile_hash = :provider_profile_hash
                          AND prompt_ref = :prompt_ref
                          AND prompt_hash = :prompt_hash
                        ORDER BY created_at DESC, agent_reading_ref DESC
                        LIMIT 1
                        """
                    ),
                    {
                        "requester_account_ref": requester_account_ref,
                        "case_ref": case_ref,
                        "reading_ref": reading_ref,
                        "reading_hash": reading_hash,
                        "agent_reading_version": MINGLI_AGENT_READING_VERSION,
                        "agent_profile_ref": agent_profile_ref,
                        "agent_profile_hash": agent_profile_hash,
                        "provider_profile_ref": provider_profile_ref,
                        "provider_profile_hash": provider_profile_hash,
                        "prompt_ref": prompt_ref,
                        "prompt_hash": prompt_hash,
                    },
                )
                .mappings()
                .one_or_none()
            )
        return None if row is None else self._validated(row)

    @classmethod
    def _validated(cls, row: Any) -> MingliAgentReadingEnvelope:
        reading = MingliAgentReadingEnvelope.model_validate(row["agent_reading_json"])
        cls._verify_row(row, expected=reading)
        return reading

    @classmethod
    def _load_by_ref(
        cls,
        connection: Connection,
        *,
        requester_account_ref: str,
        agent_reading_ref: str,
    ) -> Any | None:
        return (
            connection.execute(
                text(
                    f"""
                    {cls._select_sql()}
                    WHERE requester_account_ref = :requester_account_ref
                      AND agent_reading_ref = :agent_reading_ref
                    """
                ),
                {
                    "requester_account_ref": requester_account_ref,
                    "agent_reading_ref": agent_reading_ref,
                },
            )
            .mappings()
            .one_or_none()
        )

    @classmethod
    def _load_by_generation_key(
        cls,
        connection: Connection,
        *,
        requester_account_ref: str,
        generation_key: str,
    ) -> Any | None:
        return (
            connection.execute(
                text(
                    f"""
                    {cls._select_sql()}
                    WHERE generation_key = :generation_key
                      AND requester_account_ref = :requester_account_ref
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

    @staticmethod
    def _select_sql() -> str:
        return """
            SELECT agent_reading_ref, agent_reading_version,
                   generation_key, requester_account_ref, case_ref,
                   chart_version_ref, life_case_revision_ref,
                   reading_ref, reading_hash, packet_ref, packet_hash,
                   agent_profile_ref, agent_profile_hash, provider_id,
                   model_ref, model_digest, provider_profile_ref,
                   provider_profile_hash, prompt_ref, prompt_hash,
                   provider_response_ref, interpretation_status,
                   owner_review_status, canonical_fact_write_allowed,
                   read_only, agent_reading_json,
                   agent_reading_hash, input_tokens, output_tokens,
                   total_tokens, duration_ms
            FROM mingli.agent_readings
        """

    @staticmethod
    def _exact(reading: MingliAgentReadingEnvelope) -> dict[str, Any]:
        return {
            "agent_reading_ref": reading.agent_reading_ref,
            "agent_reading_version": reading.agent_reading_version,
            "generation_key": reading.generation_key,
            "requester_account_ref": reading.requester_account_ref,
            "case_ref": reading.case_ref,
            "chart_version_ref": reading.chart_version_ref,
            "life_case_revision_ref": reading.life_case_revision_ref,
            "reading_ref": reading.reading_ref,
            "reading_hash": reading.reading_hash,
            "packet_ref": reading.packet_ref,
            "packet_hash": reading.packet_hash,
            "agent_profile_ref": reading.agent_profile_ref,
            "agent_profile_hash": reading.agent_profile_hash,
            "provider_id": reading.provider_id,
            "model_ref": reading.model_ref,
            "model_digest": reading.model_digest,
            "provider_profile_ref": reading.provider_profile_ref,
            "provider_profile_hash": reading.provider_profile_hash,
            "prompt_ref": reading.prompt_ref,
            "prompt_hash": reading.prompt_hash,
            "provider_response_ref": reading.provider_response_ref,
            "interpretation_status": reading.interpretation_status,
            "owner_review_status": reading.owner_review_status,
            "canonical_fact_write_allowed": reading.canonical_fact_write_allowed,
            "read_only": reading.read_only,
            "agent_reading_hash": reading.agent_reading_hash,
            "input_tokens": reading.input_tokens,
            "output_tokens": reading.output_tokens,
            "total_tokens": reading.total_tokens,
            "duration_ms": reading.duration_ms,
        }

    @classmethod
    def _verify_row(
        cls,
        row: Any,
        *,
        expected: MingliAgentReadingEnvelope,
    ) -> None:
        exact = cls._exact(expected)
        if any(row[key] != value for key, value in exact.items()):
            raise MingliAgentReadingStoreError("mingli_agent_reading_row_mismatch")
        stored = MingliAgentReadingEnvelope.model_validate(row["agent_reading_json"])
        if stored != expected:
            raise MingliAgentReadingStoreError("mingli_agent_reading_json_mismatch")

    @staticmethod
    def _verify_generation_identity(
        stored: MingliAgentReadingEnvelope,
        *,
        requested: MingliAgentReadingEnvelope,
    ) -> None:
        shared = (
            "generation_key",
            "requester_account_ref",
            "case_ref",
            "chart_version_ref",
            "life_case_revision_ref",
            "reading_ref",
            "reading_hash",
            "packet_ref",
            "packet_hash",
            "agent_profile_ref",
            "agent_profile_hash",
            "provider_profile_ref",
            "provider_profile_hash",
            "prompt_ref",
            "prompt_hash",
        )
        if any(getattr(stored, key) != getattr(requested, key) for key in shared):
            raise MingliAgentReadingStoreError("mingli_agent_reading_generation_identity_mismatch")
