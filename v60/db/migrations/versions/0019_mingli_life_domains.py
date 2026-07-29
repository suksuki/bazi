"""Persist bounded Mingli life-domain evidence vectors.

Revision ID: 0019_mingli_life_domains
Revises: 0018_mingli_timing
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0019_mingli_life_domains"
down_revision: str | None = "0018_mingli_timing"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "life_domain_evidence_vectors",
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
        sa.Column(
            "mechanism_vector_ref",
            sa.String(length=180),
            sa.ForeignKey("mingli.mechanism_evidence_vectors.vector_ref"),
            nullable=False,
        ),
        sa.Column(
            "timing_vector_ref",
            sa.String(length=180),
            sa.ForeignKey("mingli.timing_evidence_vectors.vector_ref"),
            nullable=False,
        ),
        sa.Column("policy_ref", sa.String(length=180), nullable=False),
        sa.Column("policy_hash", sa.String(length=64), nullable=False),
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
            name="uq_mingli_life_domain_vector_hash",
        ),
        schema="mingli",
    )
    op.create_index(
        "ix_mingli_life_domain_vector_case",
        "life_domain_evidence_vectors",
        ["case_ref", "created_at"],
        schema="mingli",
    )
    for name in ("life_domain_vector_ref", "life_domain_vector_hash"):
        op.add_column(
            "readings",
            sa.Column(name, sa.String(length=180 if name.endswith("_ref") else 64)),
            schema="mingli",
        )
    op.create_foreign_key(
        "fk_mingli_reading_life_domain_vector",
        "readings",
        "life_domain_evidence_vectors",
        ["life_domain_vector_ref"],
        ["vector_ref"],
        source_schema="mingli",
        referent_schema="mingli",
    )
    op.execute(
        sa.text(
            """
            CREATE FUNCTION mingli.reject_life_domain_vector_mutation()
            RETURNS trigger
            LANGUAGE plpgsql
            AS $$
            BEGIN
                RAISE EXCEPTION 'mingli_life_domain_vectors_are_append_only';
            END;
            $$;

            CREATE TRIGGER trg_mingli_life_domain_vectors_append_only
            BEFORE UPDATE OR DELETE ON mingli.life_domain_evidence_vectors
            FOR EACH ROW
            EXECUTE FUNCTION mingli.reject_life_domain_vector_mutation();
            """
        )
    )
    op.execute(
        sa.text(
            """
            UPDATE platform.schema_manifest
            SET foundation_version = 'v60.foundation.011',
                manifest_json = manifest_json
                    || '{"schema_revision": "0019_mingli_life_domains",
                         "mingli_reading_version":
                             "v60.mingli-reading.005",
                         "mingli_life_domain_vector_version":
                             "v60.mingli-life-domain-evidence-vector.001"}'::jsonb,
                updated_at = now()
            WHERE singleton_id = 1
            """
        )
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            """
            DROP TRIGGER IF EXISTS trg_mingli_life_domain_vectors_append_only
                ON mingli.life_domain_evidence_vectors;
            DROP FUNCTION IF EXISTS mingli.reject_life_domain_vector_mutation();
            """
        )
    )
    op.drop_constraint(
        "fk_mingli_reading_life_domain_vector",
        "readings",
        schema="mingli",
        type_="foreignkey",
    )
    for column in ("life_domain_vector_hash", "life_domain_vector_ref"):
        op.drop_column("readings", column, schema="mingli")
    op.drop_index(
        "ix_mingli_life_domain_vector_case",
        table_name="life_domain_evidence_vectors",
        schema="mingli",
    )
    op.drop_table("life_domain_evidence_vectors", schema="mingli")
    op.execute(
        sa.text(
            """
            UPDATE platform.schema_manifest
            SET foundation_version = 'v60.foundation.010',
                manifest_json = (manifest_json - 'mingli_life_domain_vector_version')
                    || '{"schema_revision": "0018_mingli_timing",
                         "mingli_reading_version":
                             "v60.mingli-reading.004"}'::jsonb,
                updated_at = now()
            WHERE singleton_id = 1
            """
        )
    )
