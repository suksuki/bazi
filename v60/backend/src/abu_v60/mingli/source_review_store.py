from __future__ import annotations

from typing import Any

from sqlalchemy import text
from sqlalchemy.engine import Connection, Engine

from abu_v60.mingli.source_review_contracts import (
    MingliSourceCoordinateReviewVector,
)
from abu_v60.provenance import canonical_json


class MingliSourceReviewVectorStoreError(ValueError):
    pass


class MingliSourceReviewVectorNotFoundError(MingliSourceReviewVectorStoreError):
    pass


class MingliSourceReviewVectorStore:
    """Mingli-owned append-only source-coordinate review history."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def ensure(
        self,
        vector: MingliSourceCoordinateReviewVector,
    ) -> MingliSourceCoordinateReviewVector:
        with self._engine.begin() as connection:
            self.ensure_in_connection(connection, vector=vector)
        return vector

    def ensure_in_connection(
        self,
        connection: Connection,
        *,
        vector: MingliSourceCoordinateReviewVector,
    ) -> MingliSourceCoordinateReviewVector:
        connection.execute(
            text(
                """
                INSERT INTO mingli.source_coordinate_review_vectors
                    (vector_ref, vector_version, case_ref, chart_version_ref,
                     quant_vector_ref, source_review_profile_ref,
                     source_review_profile_hash, vector_json, vector_hash)
                VALUES
                    (:vector_ref, :vector_version, :case_ref, :chart_version_ref,
                     :quant_vector_ref, :source_review_profile_ref,
                     :source_review_profile_hash, CAST(:vector_json AS jsonb),
                     :vector_hash)
                ON CONFLICT DO NOTHING
                """
            ),
            {
                "vector_ref": vector.vector_ref,
                "vector_version": vector.vector_version,
                "case_ref": vector.case_ref,
                "chart_version_ref": vector.chart_version_ref,
                "quant_vector_ref": vector.quant_vector_ref,
                "source_review_profile_ref": vector.source_review_profile_ref,
                "source_review_profile_hash": vector.source_review_profile_hash,
                "vector_json": canonical_json(vector.model_dump(mode="json")),
                "vector_hash": vector.vector_hash,
            },
        )
        row = self._load_row(connection, vector_ref=vector.vector_ref)
        if row is None:
            raise MingliSourceReviewVectorStoreError("source_review_vector_identity_conflict")
        self._verify_row(row, expected=vector)
        return vector

    def get(
        self,
        *,
        vector_ref: str,
    ) -> MingliSourceCoordinateReviewVector:
        with self._engine.connect() as connection:
            row = self._load_row(connection, vector_ref=vector_ref)
        if row is None:
            raise MingliSourceReviewVectorNotFoundError("source_review_vector_not_found")
        vector = MingliSourceCoordinateReviewVector.model_validate(row["vector_json"])
        self._verify_row(row, expected=vector)
        return vector

    @staticmethod
    def _load_row(
        connection: Any,
        *,
        vector_ref: str,
    ) -> Any | None:
        return (
            connection.execute(
                text(
                    """
                    SELECT vector_ref, vector_version, case_ref,
                           chart_version_ref, quant_vector_ref,
                           source_review_profile_ref,
                           source_review_profile_hash,
                           vector_json, vector_hash
                    FROM mingli.source_coordinate_review_vectors
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
        expected: MingliSourceCoordinateReviewVector,
    ) -> None:
        exact = {
            "vector_ref": expected.vector_ref,
            "vector_version": expected.vector_version,
            "case_ref": expected.case_ref,
            "chart_version_ref": expected.chart_version_ref,
            "quant_vector_ref": expected.quant_vector_ref,
            "source_review_profile_ref": expected.source_review_profile_ref,
            "source_review_profile_hash": expected.source_review_profile_hash,
            "vector_json": expected.model_dump(mode="json"),
            "vector_hash": expected.vector_hash,
        }
        if dict(row) != exact:
            raise MingliSourceReviewVectorStoreError("source_review_vector_persistence_conflict")
