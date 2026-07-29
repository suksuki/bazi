from __future__ import annotations

from typing import Any

from sqlalchemy import text
from sqlalchemy.engine import Engine

from abu_v60.mingli.domain_contracts import MingliLifeDomainEvidenceVector
from abu_v60.provenance import canonical_json


class MingliLifeDomainVectorStoreError(ValueError):
    pass


class MingliLifeDomainVectorNotFoundError(MingliLifeDomainVectorStoreError):
    pass


class MingliLifeDomainVectorStore:
    """Mingli-owned append-only history for domain evidence projections."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def ensure(
        self,
        vector: MingliLifeDomainEvidenceVector,
    ) -> MingliLifeDomainEvidenceVector:
        with self._engine.begin() as connection:
            self.ensure_in_connection(connection, vector=vector)
        return vector

    def ensure_in_connection(
        self,
        connection: Any,
        *,
        vector: MingliLifeDomainEvidenceVector,
    ) -> MingliLifeDomainEvidenceVector:
        connection.execute(
            text(
                """
                INSERT INTO mingli.life_domain_evidence_vectors
                    (vector_ref, vector_version, case_ref, chart_version_ref,
                     life_case_revision_ref, mechanism_vector_ref,
                     timing_vector_ref, policy_ref, policy_hash,
                     vector_json, vector_hash)
                VALUES
                    (:vector_ref, :vector_version, :case_ref, :chart_version_ref,
                     :life_case_revision_ref, :mechanism_vector_ref,
                     :timing_vector_ref, :policy_ref, :policy_hash,
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
                "mechanism_vector_ref": vector.mechanism_vector_ref,
                "timing_vector_ref": vector.timing_vector_ref,
                "policy_ref": vector.policy_ref,
                "policy_hash": vector.policy_hash,
                "vector_json": canonical_json(vector.model_dump(mode="json")),
                "vector_hash": vector.vector_hash,
            },
        )
        row = self._load_row(connection, vector_ref=vector.vector_ref)
        if row is None:
            raise MingliLifeDomainVectorStoreError(
                "life_domain_vector_identity_conflict"
            )
        self._verify_row(row, expected=vector)
        return vector

    def get(self, *, vector_ref: str) -> MingliLifeDomainEvidenceVector:
        with self._engine.connect() as connection:
            row = self._load_row(connection, vector_ref=vector_ref)
        if row is None:
            raise MingliLifeDomainVectorNotFoundError(
                "life_domain_vector_not_found"
            )
        vector = MingliLifeDomainEvidenceVector.model_validate(row["vector_json"])
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
                           mechanism_vector_ref, timing_vector_ref,
                           policy_ref, policy_hash, vector_json, vector_hash
                    FROM mingli.life_domain_evidence_vectors
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
        expected: MingliLifeDomainEvidenceVector,
    ) -> None:
        exact = {
            "vector_ref": expected.vector_ref,
            "vector_version": expected.vector_version,
            "case_ref": expected.case_ref,
            "chart_version_ref": expected.chart_version_ref,
            "life_case_revision_ref": expected.life_case_revision_ref,
            "mechanism_vector_ref": expected.mechanism_vector_ref,
            "timing_vector_ref": expected.timing_vector_ref,
            "policy_ref": expected.policy_ref,
            "policy_hash": expected.policy_hash,
            "vector_json": expected.model_dump(mode="json"),
            "vector_hash": expected.vector_hash,
        }
        if dict(row) != exact:
            raise MingliLifeDomainVectorStoreError(
                "life_domain_vector_persistence_conflict"
            )
