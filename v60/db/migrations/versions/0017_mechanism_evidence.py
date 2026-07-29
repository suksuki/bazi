"""Persist bounded Mingli mechanism evidence vectors.

Revision ID: 0017_mechanism_evidence
Revises: 0016_quant_foundation
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0017_mechanism_evidence"
down_revision: str | None = "0016_quant_foundation"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "mechanism_evidence_vectors",
        sa.Column("vector_ref", sa.String(length=180), primary_key=True),
        sa.Column("vector_version", sa.String(length=100), nullable=False),
        sa.Column(
            "case_ref",
            sa.String(length=160),
            sa.ForeignKey("mingli.cases.case_ref"),
            nullable=False,
        ),
        sa.Column(
            "chart_version_ref",
            sa.String(length=160),
            sa.ForeignKey("mingli.chart_versions.chart_version_ref"),
            nullable=False,
        ),
        sa.Column(
            "quant_vector_ref",
            sa.String(length=180),
            sa.ForeignKey("mingli.quant_foundation_vectors.vector_ref"),
            nullable=False,
        ),
        sa.Column("mechanism_profile_ref", sa.String(length=240), nullable=False),
        sa.Column("mechanism_profile_hash", sa.String(length=64), nullable=False),
        sa.Column(
            "vector_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column("vector_hash", sa.String(length=64), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint(
            "vector_hash",
            name="uq_mingli_mechanism_vector_hash",
        ),
        schema="mingli",
    )
    op.create_index(
        "ix_mingli_mechanism_vector_case_created",
        "mechanism_evidence_vectors",
        ["case_ref", "created_at"],
        schema="mingli",
    )
    for name, length in (
        ("mechanism_evidence_profile_ref", 240),
        ("mechanism_evidence_profile_hash", 64),
        ("mechanism_vector_ref", 180),
        ("mechanism_vector_hash", 64),
    ):
        op.add_column(
            "readings",
            sa.Column(
                name,
                sa.String(length=length),
                nullable=True,
            ),
            schema="mingli",
        )
    op.create_foreign_key(
        "fk_mingli_reading_mechanism_vector",
        "readings",
        "mechanism_evidence_vectors",
        ["mechanism_vector_ref"],
        ["vector_ref"],
        source_schema="mingli",
        referent_schema="mingli",
    )
    op.execute(
        sa.text(
            """
            CREATE FUNCTION mingli.reject_mechanism_vector_mutation()
            RETURNS trigger
            LANGUAGE plpgsql
            AS $$
            BEGIN
                RAISE EXCEPTION 'mingli_mechanism_vectors_are_append_only';
            END;
            $$;

            CREATE TRIGGER trg_mingli_mechanism_vectors_append_only
            BEFORE UPDATE OR DELETE ON mingli.mechanism_evidence_vectors
            FOR EACH ROW
            EXECUTE FUNCTION mingli.reject_mechanism_vector_mutation();
            """
        )
    )
    op.execute(
        sa.text(
            """
            UPDATE platform.schema_manifest
            SET foundation_version = 'v60.foundation.009',
                manifest_json = manifest_json
                    || '{"schema_revision": "0017_mechanism_evidence",
                         "mingli_reading_version":
                             "v60.mingli-reading.003",
                         "mingli_mechanism_vector_version":
                             "v60.mingli-mechanism-evidence-vector.001"}'::jsonb,
                updated_at = now()
            WHERE singleton_id = 1
            """
        )
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            """
            DROP TRIGGER IF EXISTS trg_mingli_mechanism_vectors_append_only
                ON mingli.mechanism_evidence_vectors;
            DROP FUNCTION IF EXISTS mingli.reject_mechanism_vector_mutation();
            """
        )
    )
    op.drop_constraint(
        "fk_mingli_reading_mechanism_vector",
        "readings",
        schema="mingli",
        type_="foreignkey",
    )
    for column in (
        "mechanism_vector_hash",
        "mechanism_vector_ref",
        "mechanism_evidence_profile_hash",
        "mechanism_evidence_profile_ref",
    ):
        op.drop_column("readings", column, schema="mingli")
    op.drop_index(
        "ix_mingli_mechanism_vector_case_created",
        table_name="mechanism_evidence_vectors",
        schema="mingli",
    )
    op.drop_table("mechanism_evidence_vectors", schema="mingli")
    op.execute(
        sa.text(
            """
            UPDATE platform.schema_manifest
            SET foundation_version = 'v60.foundation.008',
                manifest_json = (manifest_json - 'mingli_mechanism_vector_version')
                    || '{"schema_revision": "0016_quant_foundation",
                         "mingli_reading_version":
                             "v60.mingli-reading.002"}'::jsonb,
                updated_at = now()
            WHERE singleton_id = 1
            """
        )
    )
