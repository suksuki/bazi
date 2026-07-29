from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import text

from abu_v60.provenance import canonical_json, content_hash


class MigrationBatchAdmissionError(ValueError):
    pass


class MigrationBatchDefinition(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    batch_ref: str = Field(min_length=1)
    source_system: str = Field(min_length=1)
    source_database: str = Field(min_length=1)
    status: str = Field(min_length=1)
    manifest: dict[str, Any]

    @property
    def manifest_hash(self) -> str:
        return content_hash(self.manifest)


class MigrationBatchAdmissionService:
    """Single platform-schema write port for immutable import/seed receipts."""

    def admit(
        self,
        connection: Any,
        *,
        definition: MigrationBatchDefinition,
    ) -> str:
        connection.execute(
            text(
                """
                INSERT INTO platform.migration_batches
                    (batch_ref, source_system, source_database, status,
                     manifest_json, manifest_hash)
                VALUES
                    (:batch_ref, :source_system, :source_database, :status,
                     CAST(:manifest AS jsonb), :manifest_hash)
                ON CONFLICT (batch_ref) DO NOTHING
                """
            ),
            {
                "batch_ref": definition.batch_ref,
                "source_system": definition.source_system,
                "source_database": definition.source_database,
                "status": definition.status,
                "manifest": canonical_json(definition.manifest),
                "manifest_hash": definition.manifest_hash,
            },
        )
        row = (
            connection.execute(
                text(
                    """
                    SELECT source_system, source_database, status,
                           manifest_json, manifest_hash
                    FROM platform.migration_batches
                    WHERE batch_ref = :batch_ref
                    """
                ),
                {"batch_ref": definition.batch_ref},
            )
            .mappings()
            .one()
        )
        expected = {
            "source_system": definition.source_system,
            "source_database": definition.source_database,
            "status": definition.status,
            "manifest_json": definition.manifest,
            "manifest_hash": definition.manifest_hash,
        }
        if dict(row) != expected:
            raise MigrationBatchAdmissionError("migration_batch_admission_conflict")
        return definition.manifest_hash
