from __future__ import annotations

from typing import Any

from sqlalchemy import text
from sqlalchemy.engine import Engine

from abu_v60.mingli.timing_contracts import MingliTimingEvidenceVector
from abu_v60.provenance import canonical_json


class MingliTimingVectorStoreError(ValueError):
    pass


class MingliTimingVectorNotFoundError(MingliTimingVectorStoreError):
    pass


class MingliTimingVectorStore:
    """Mingli-owned append-only history for frozen timing vectors."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def ensure(
        self,
        vector: MingliTimingEvidenceVector,
    ) -> MingliTimingEvidenceVector:
        with self._engine.begin() as connection:
            self.ensure_in_connection(connection, vector=vector)
        return vector

    def ensure_in_connection(
        self,
        connection: Any,
        *,
        vector: MingliTimingEvidenceVector,
    ) -> MingliTimingEvidenceVector:
        payload = vector.model_dump(mode="json")
        connection.execute(
            text(
                """
                INSERT INTO mingli.timing_evidence_vectors
                    (vector_ref, vector_version, case_ref, chart_version_ref,
                     life_case_revision_ref, analysis_date, timezone,
                     timing_profile_ref, timing_profile_hash,
                     vector_json, vector_hash)
                VALUES
                    (:vector_ref, :vector_version, :case_ref, :chart_version_ref,
                     :life_case_revision_ref, :analysis_date, :timezone,
                     :timing_profile_ref, :timing_profile_hash,
                     CAST(:vector_json AS jsonb), :vector_hash)
                ON CONFLICT DO NOTHING
                """
            ),
            {
                "vector_ref": vector.vector_ref,
                "vector_version": vector.vector_version,
                "case_ref": vector.case_ref,
                "chart_version_ref": vector.chart_version_ref,
                "life_case_revision_ref": vector.life_case_revision_ref,
                "analysis_date": vector.analysis_date,
                "timezone": vector.timezone,
                "timing_profile_ref": vector.timing_profile_ref,
                "timing_profile_hash": vector.timing_profile_hash,
                "vector_json": canonical_json(payload),
                "vector_hash": vector.vector_hash,
            },
        )
        row = self._load_row(connection, vector_ref=vector.vector_ref)
        if row is None:
            raise MingliTimingVectorStoreError("timing_vector_identity_conflict")
        self._verify_row(row, expected=vector)
        return vector

    def get(self, *, vector_ref: str) -> MingliTimingEvidenceVector:
        with self._engine.connect() as connection:
            row = self._load_row(connection, vector_ref=vector_ref)
        if row is None:
            raise MingliTimingVectorNotFoundError("timing_vector_not_found")
        vector = MingliTimingEvidenceVector.model_validate(row["vector_json"])
        self._verify_row(row, expected=vector)
        return vector

    @staticmethod
    def _load_row(connection: Any, *, vector_ref: str) -> Any | None:
        return (
            connection.execute(
                text(
                    """
                    SELECT vector_ref, vector_version, case_ref,
                           chart_version_ref, life_case_revision_ref,
                           analysis_date, timezone, timing_profile_ref,
                           timing_profile_hash, vector_json, vector_hash
                    FROM mingli.timing_evidence_vectors
                    WHERE vector_ref = :vector_ref
                    """
                ),
                {"vector_ref": vector_ref},
            )
            .mappings()
            .one_or_none()
        )

    @staticmethod
    def _verify_row(
        row: Any,
        *,
        expected: MingliTimingEvidenceVector,
    ) -> None:
        exact = {
            "vector_ref": expected.vector_ref,
            "vector_version": expected.vector_version,
            "case_ref": expected.case_ref,
            "chart_version_ref": expected.chart_version_ref,
            "life_case_revision_ref": expected.life_case_revision_ref,
            "analysis_date": expected.analysis_date,
            "timezone": expected.timezone,
            "timing_profile_ref": expected.timing_profile_ref,
            "timing_profile_hash": expected.timing_profile_hash,
            "vector_json": expected.model_dump(mode="json"),
            "vector_hash": expected.vector_hash,
        }
        if dict(row) != exact:
            raise MingliTimingVectorStoreError("timing_vector_persistence_conflict")
