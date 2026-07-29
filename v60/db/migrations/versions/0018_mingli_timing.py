"""Persist deterministic Mingli timing evidence vectors.

Revision ID: 0018_mingli_timing
Revises: 0017_mechanism_evidence
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0018_mingli_timing"
down_revision: str | None = "0017_mechanism_evidence"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "timing_evidence_vectors",
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
            "life_case_revision_ref",
            sa.String(length=180),
            sa.ForeignKey("mingli.life_case_revisions.life_case_revision_ref"),
            nullable=False,
        ),
        sa.Column("analysis_date", sa.Date(), nullable=False),
        sa.Column("timezone", sa.String(length=80), nullable=False),
        sa.Column("timing_profile_ref", sa.String(length=240), nullable=False),
        sa.Column("timing_profile_hash", sa.String(length=64), nullable=False),
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
        sa.UniqueConstraint("vector_hash", name="uq_mingli_timing_vector_hash"),
        schema="mingli",
    )
    op.create_index(
        "ix_mingli_timing_vector_case_date",
        "timing_evidence_vectors",
        ["case_ref", "analysis_date"],
        schema="mingli",
    )
    for name, length in (
        ("timing_evidence_profile_ref", 240),
        ("timing_evidence_profile_hash", 64),
        ("timing_vector_ref", 180),
        ("timing_vector_hash", 64),
    ):
        op.add_column(
            "readings",
            sa.Column(name, sa.String(length=length), nullable=True),
            schema="mingli",
        )
    op.create_foreign_key(
        "fk_mingli_reading_timing_vector",
        "readings",
        "timing_evidence_vectors",
        ["timing_vector_ref"],
        ["vector_ref"],
        source_schema="mingli",
        referent_schema="mingli",
    )
    op.execute(
        sa.text(
            """
            CREATE FUNCTION mingli.reject_timing_vector_mutation()
            RETURNS trigger
            LANGUAGE plpgsql
            AS $$
            BEGIN
                RAISE EXCEPTION 'mingli_timing_vectors_are_append_only';
            END;
            $$;

            CREATE TRIGGER trg_mingli_timing_vectors_append_only
            BEFORE UPDATE OR DELETE ON mingli.timing_evidence_vectors
            FOR EACH ROW
            EXECUTE FUNCTION mingli.reject_timing_vector_mutation();
            """
        )
    )
    op.execute(
        sa.text(
            """
            UPDATE platform.schema_manifest
            SET foundation_version = 'v60.foundation.010',
                manifest_json = manifest_json
                    || '{"schema_revision": "0018_mingli_timing",
                         "mingli_reading_version":
                             "v60.mingli-reading.004",
                         "mingli_timing_vector_version":
                             "v60.mingli-timing-evidence-vector.001"}'::jsonb,
                updated_at = now()
            WHERE singleton_id = 1
            """
        )
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            """
            DROP TRIGGER IF EXISTS trg_mingli_timing_vectors_append_only
                ON mingli.timing_evidence_vectors;
            DROP FUNCTION IF EXISTS mingli.reject_timing_vector_mutation();
            """
        )
    )
    op.drop_constraint(
        "fk_mingli_reading_timing_vector",
        "readings",
        schema="mingli",
        type_="foreignkey",
    )
    for column in (
        "timing_vector_hash",
        "timing_vector_ref",
        "timing_evidence_profile_hash",
        "timing_evidence_profile_ref",
    ):
        op.drop_column("readings", column, schema="mingli")
    op.drop_index(
        "ix_mingli_timing_vector_case_date",
        table_name="timing_evidence_vectors",
        schema="mingli",
    )
    op.drop_table("timing_evidence_vectors", schema="mingli")
    op.execute(
        sa.text(
            """
            UPDATE platform.schema_manifest
            SET foundation_version = 'v60.foundation.009',
                manifest_json = (manifest_json - 'mingli_timing_vector_version')
                    || '{"schema_revision": "0017_mechanism_evidence",
                         "mingli_reading_version":
                             "v60.mingli-reading.003"}'::jsonb,
                updated_at = now()
            WHERE singleton_id = 1
            """
        )
    )
