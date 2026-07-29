from __future__ import annotations

from typing import Any

from sqlalchemy import text
from sqlalchemy.engine import Engine

from abu_v60.mingli.mechanism_contracts import MingliMechanismEvidenceVector
from abu_v60.provenance import canonical_json


class MingliMechanismVectorStoreError(ValueError):
    pass


class MingliMechanismVectorNotFoundError(MingliMechanismVectorStoreError):
    pass


class MingliMechanismVectorStore:
    """Append-only store for chart-bound mechanism evidence vectors."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def ensure(
        self,
        vector: MingliMechanismEvidenceVector,
    ) -> MingliMechanismEvidenceVector:
        with self._engine.begin() as connection:
            self.ensure_in_connection(connection, vector=vector)
        return vector

    def ensure_in_connection(
        self,
        connection: Any,
        *,
        vector: MingliMechanismEvidenceVector,
    ) -> MingliMechanismEvidenceVector:
        connection.execute(
            text(
                """
                INSERT INTO mingli.mechanism_evidence_vectors
                    (vector_ref, vector_version, case_ref,
                     chart_version_ref, quant_vector_ref,
                     mechanism_profile_ref, mechanism_profile_hash,
                     vector_json, vector_hash)
                VALUES
                    (:vector_ref, :vector_version, :case_ref,
                     :chart_version_ref, :quant_vector_ref,
                     :mechanism_profile_ref, :mechanism_profile_hash,
                     CAST(:vector_json AS jsonb), :vector_hash)
                ON CONFLICT DO NOTHING
                """
            ),
            {
                "vector_ref": vector.vector_ref,
                "vector_version": vector.vector_version,
                "case_ref": vector.case_ref,
                "chart_version_ref": vector.chart_version_ref,
                "quant_vector_ref": vector.quant_vector_ref,
                "mechanism_profile_ref": vector.mechanism_profile_ref,
                "mechanism_profile_hash": vector.mechanism_profile_hash,
                "vector_json": canonical_json(vector.model_dump(mode="json")),
                "vector_hash": vector.vector_hash,
            },
        )
        row = self._load_row(connection, vector_ref=vector.vector_ref)
        if row is None:
            raise MingliMechanismVectorStoreError("mechanism_vector_identity_conflict")
        self._verify_row(row, expected=vector)
        return vector

    def get(self, *, vector_ref: str) -> MingliMechanismEvidenceVector:
        with self._engine.connect() as connection:
            row = self._load_row(connection, vector_ref=vector_ref)
        if row is None:
            raise MingliMechanismVectorNotFoundError("mechanism_vector_not_found")
        vector = MingliMechanismEvidenceVector.model_validate(row["vector_json"])
        self._verify_row(row, expected=vector)
        return vector

    @staticmethod
    def _load_row(connection: Any, *, vector_ref: str) -> Any | None:
        return (
            connection.execute(
                text(
                    """
                    SELECT vector_ref, vector_version, case_ref,
                           chart_version_ref, quant_vector_ref,
                           mechanism_profile_ref, mechanism_profile_hash,
                           vector_json, vector_hash
                    FROM mingli.mechanism_evidence_vectors
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
        expected: MingliMechanismEvidenceVector,
    ) -> None:
        exact = {
            "vector_ref": expected.vector_ref,
            "vector_version": expected.vector_version,
            "case_ref": expected.case_ref,
            "chart_version_ref": expected.chart_version_ref,
            "quant_vector_ref": expected.quant_vector_ref,
            "mechanism_profile_ref": expected.mechanism_profile_ref,
            "mechanism_profile_hash": expected.mechanism_profile_hash,
            "vector_json": expected.model_dump(mode="json"),
            "vector_hash": expected.vector_hash,
        }
        if dict(row) != exact:
            raise MingliMechanismVectorStoreError("mechanism_vector_persistence_conflict")
