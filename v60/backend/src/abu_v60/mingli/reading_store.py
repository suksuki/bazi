from __future__ import annotations

from typing import Any

from sqlalchemy import text
from sqlalchemy.engine import Engine

from abu_v60.mingli.reading import MingliReadingEnvelope
from abu_v60.provenance import canonical_json


class MingliReadingStoreError(ValueError):
    pass


class MingliReadingNotFoundError(MingliReadingStoreError):
    pass


class MingliReadingStore:
    """Mingli-owned append-only history for reproducible readings."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def ensure(self, reading: MingliReadingEnvelope) -> MingliReadingEnvelope:
        payload = reading.model_dump(mode="json")
        with self._engine.begin() as connection:
            connection.execute(
                text(
                    """
                    INSERT INTO mingli.readings
                        (reading_ref, reading_version, case_ref,
                         chart_version_ref, life_case_revision_ref,
                         foundation_profile_ref, foundation_profile_hash,
                         candidate_rule_profile_ref,
                         candidate_rule_profile_hash,
                         quant_foundation_profile_ref,
                         quant_foundation_profile_hash,
                         quant_vector_ref, quant_vector_hash,
                         source_review_profile_ref,
                         source_review_profile_hash,
                         source_review_vector_ref,
                         source_review_vector_hash,
                         mechanism_evidence_profile_ref,
                         mechanism_evidence_profile_hash,
                         mechanism_vector_ref, mechanism_vector_hash,
                         timing_evidence_profile_ref,
                         timing_evidence_profile_hash,
                         timing_vector_ref, timing_vector_hash,
                         life_domain_vector_ref, life_domain_vector_hash,
                         reading_json, reading_hash)
                    VALUES
                        (:reading_ref, :reading_version, :case_ref,
                         :chart_version_ref, :life_case_revision_ref,
                         :foundation_profile_ref, :foundation_profile_hash,
                         :candidate_rule_profile_ref,
                         :candidate_rule_profile_hash,
                         :quant_foundation_profile_ref,
                         :quant_foundation_profile_hash,
                         :quant_vector_ref, :quant_vector_hash,
                         :source_review_profile_ref,
                         :source_review_profile_hash,
                         :source_review_vector_ref,
                         :source_review_vector_hash,
                         :mechanism_evidence_profile_ref,
                         :mechanism_evidence_profile_hash,
                         :mechanism_vector_ref, :mechanism_vector_hash,
                         :timing_evidence_profile_ref,
                         :timing_evidence_profile_hash,
                         :timing_vector_ref, :timing_vector_hash,
                         :life_domain_vector_ref, :life_domain_vector_hash,
                         CAST(:reading_json AS jsonb), :reading_hash)
                    ON CONFLICT DO NOTHING
                    """
                ),
                {
                    "reading_ref": reading.reading_ref,
                    "reading_version": reading.reading_version,
                    "case_ref": reading.case_ref,
                    "chart_version_ref": reading.chart_version_ref,
                    "life_case_revision_ref": reading.life_case_revision_ref,
                    "foundation_profile_ref": (reading.foundation_profile.profile_ref),
                    "foundation_profile_hash": (reading.foundation_profile.profile_hash),
                    "candidate_rule_profile_ref": (reading.candidate_rule_profile.profile_ref),
                    "candidate_rule_profile_hash": (reading.candidate_rule_profile.profile_hash),
                    "quant_foundation_profile_ref": (
                        reading.quant_foundation_profile.profile_ref
                        if reading.quant_foundation_profile is not None
                        else None
                    ),
                    "quant_foundation_profile_hash": (
                        reading.quant_foundation_profile.profile_hash
                        if reading.quant_foundation_profile is not None
                        else None
                    ),
                    "quant_vector_ref": reading.quant_vector_ref,
                    "quant_vector_hash": reading.quant_vector_hash,
                    "source_review_profile_ref": (
                        reading.source_review_profile.profile_ref
                        if reading.source_review_profile is not None
                        else None
                    ),
                    "source_review_profile_hash": (
                        reading.source_review_profile.profile_hash
                        if reading.source_review_profile is not None
                        else None
                    ),
                    "source_review_vector_ref": (reading.source_review_vector_ref),
                    "source_review_vector_hash": (reading.source_review_vector_hash),
                    "mechanism_evidence_profile_ref": (
                        reading.mechanism_evidence_profile.profile_ref
                        if reading.mechanism_evidence_profile is not None
                        else None
                    ),
                    "mechanism_evidence_profile_hash": (
                        reading.mechanism_evidence_profile.profile_hash
                        if reading.mechanism_evidence_profile is not None
                        else None
                    ),
                    "mechanism_vector_ref": reading.mechanism_vector_ref,
                    "mechanism_vector_hash": reading.mechanism_vector_hash,
                    "timing_evidence_profile_ref": (
                        reading.timing_evidence_profile.profile_ref
                        if reading.timing_evidence_profile is not None
                        else None
                    ),
                    "timing_evidence_profile_hash": (
                        reading.timing_evidence_profile.profile_hash
                        if reading.timing_evidence_profile is not None
                        else None
                    ),
                    "timing_vector_ref": reading.timing_vector_ref,
                    "timing_vector_hash": reading.timing_vector_hash,
                    "life_domain_vector_ref": reading.life_domain_vector_ref,
                    "life_domain_vector_hash": reading.life_domain_vector_hash,
                    "reading_json": canonical_json(payload),
                    "reading_hash": reading.reading_hash,
                },
            )
            row = self._load_row(connection, reading_ref=reading.reading_ref)
            if row is None:
                raise MingliReadingStoreError("mingli_reading_identity_conflict")
            self._verify_row(row, expected=reading)
        return reading

    def get(self, *, reading_ref: str) -> MingliReadingEnvelope:
        with self._engine.connect() as connection:
            row = self._load_row(connection, reading_ref=reading_ref)
        if row is None:
            raise MingliReadingNotFoundError("mingli_reading_not_found")
        reading = MingliReadingEnvelope.model_validate(row["reading_json"])
        self._verify_row(row, expected=reading)
        return reading

    @staticmethod
    def _load_row(connection: Any, *, reading_ref: str) -> Any | None:
        return (
            connection.execute(
                text(
                    """
                    SELECT reading_ref, reading_version, case_ref,
                           chart_version_ref, life_case_revision_ref,
                           foundation_profile_ref, foundation_profile_hash,
                           candidate_rule_profile_ref,
                           candidate_rule_profile_hash,
                           quant_foundation_profile_ref,
                           quant_foundation_profile_hash,
                           quant_vector_ref, quant_vector_hash,
                           source_review_profile_ref,
                           source_review_profile_hash,
                           source_review_vector_ref,
                           source_review_vector_hash,
                           mechanism_evidence_profile_ref,
                           mechanism_evidence_profile_hash,
                           mechanism_vector_ref, mechanism_vector_hash,
                           timing_evidence_profile_ref,
                           timing_evidence_profile_hash,
                           timing_vector_ref, timing_vector_hash,
                           life_domain_vector_ref, life_domain_vector_hash,
                           reading_json, reading_hash
                    FROM mingli.readings
                    WHERE reading_ref = :reading_ref
                    """
                ),
                {"reading_ref": reading_ref},
            )
            .mappings()
            .one_or_none()
        )

    @staticmethod
    def _verify_row(
        row: Any,
        *,
        expected: MingliReadingEnvelope,
    ) -> None:
        exact = {
            "reading_ref": expected.reading_ref,
            "reading_version": expected.reading_version,
            "case_ref": expected.case_ref,
            "chart_version_ref": expected.chart_version_ref,
            "life_case_revision_ref": expected.life_case_revision_ref,
            "foundation_profile_ref": expected.foundation_profile.profile_ref,
            "foundation_profile_hash": expected.foundation_profile.profile_hash,
            "candidate_rule_profile_ref": (expected.candidate_rule_profile.profile_ref),
            "candidate_rule_profile_hash": (expected.candidate_rule_profile.profile_hash),
            "quant_foundation_profile_ref": (
                expected.quant_foundation_profile.profile_ref
                if expected.quant_foundation_profile is not None
                else None
            ),
            "quant_foundation_profile_hash": (
                expected.quant_foundation_profile.profile_hash
                if expected.quant_foundation_profile is not None
                else None
            ),
            "quant_vector_ref": expected.quant_vector_ref,
            "quant_vector_hash": expected.quant_vector_hash,
            "source_review_profile_ref": (
                expected.source_review_profile.profile_ref
                if expected.source_review_profile is not None
                else None
            ),
            "source_review_profile_hash": (
                expected.source_review_profile.profile_hash
                if expected.source_review_profile is not None
                else None
            ),
            "source_review_vector_ref": expected.source_review_vector_ref,
            "source_review_vector_hash": expected.source_review_vector_hash,
            "mechanism_evidence_profile_ref": (
                expected.mechanism_evidence_profile.profile_ref
                if expected.mechanism_evidence_profile is not None
                else None
            ),
            "mechanism_evidence_profile_hash": (
                expected.mechanism_evidence_profile.profile_hash
                if expected.mechanism_evidence_profile is not None
                else None
            ),
            "mechanism_vector_ref": expected.mechanism_vector_ref,
            "mechanism_vector_hash": expected.mechanism_vector_hash,
            "timing_evidence_profile_ref": (
                expected.timing_evidence_profile.profile_ref
                if expected.timing_evidence_profile is not None
                else None
            ),
            "timing_evidence_profile_hash": (
                expected.timing_evidence_profile.profile_hash
                if expected.timing_evidence_profile is not None
                else None
            ),
            "timing_vector_ref": expected.timing_vector_ref,
            "timing_vector_hash": expected.timing_vector_hash,
            "life_domain_vector_ref": expected.life_domain_vector_ref,
            "life_domain_vector_hash": expected.life_domain_vector_hash,
            "reading_json": expected.model_dump(mode="json"),
            "reading_hash": expected.reading_hash,
        }
        if dict(row) != exact:
            raise MingliReadingStoreError("mingli_reading_persistence_conflict")
