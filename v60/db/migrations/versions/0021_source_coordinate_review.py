"""Persist bounded source-coordinate relation review vectors.

Revision ID: 0021_source_coordinate_review
Revises: 0020_three_life_qualification
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0021_source_coordinate_review"
down_revision: str | None = "0020_three_life_qualification"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "source_coordinate_review_vectors",
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
        sa.Column(
            "source_review_profile_ref",
            sa.String(length=240),
            nullable=False,
        ),
        sa.Column(
            "source_review_profile_hash",
            sa.String(length=64),
            nullable=False,
        ),
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
            name="uq_mingli_source_review_vector_hash",
        ),
        schema="mingli",
    )
    op.create_index(
        "ix_mingli_source_review_vector_case",
        "source_coordinate_review_vectors",
        ["case_ref", "created_at"],
        schema="mingli",
    )
    for name, length in (
        ("source_review_profile_ref", 240),
        ("source_review_profile_hash", 64),
        ("source_review_vector_ref", 180),
        ("source_review_vector_hash", 64),
    ):
        op.add_column(
            "readings",
            sa.Column(name, sa.String(length=length), nullable=True),
            schema="mingli",
        )
    op.create_foreign_key(
        "fk_mingli_reading_source_review_vector",
        "readings",
        "source_coordinate_review_vectors",
        ["source_review_vector_ref"],
        ["vector_ref"],
        source_schema="mingli",
        referent_schema="mingli",
    )
    op.execute(
        sa.text(
            """
            CREATE FUNCTION mingli.reject_source_review_vector_mutation()
            RETURNS trigger
            LANGUAGE plpgsql
            AS $$
            BEGIN
                RAISE EXCEPTION 'mingli_source_review_vectors_are_append_only';
            END;
            $$;

            CREATE TRIGGER trg_mingli_source_review_vectors_append_only
            BEFORE UPDATE OR DELETE
            ON mingli.source_coordinate_review_vectors
            FOR EACH ROW
            EXECUTE FUNCTION mingli.reject_source_review_vector_mutation();
            """
        )
    )
    op.execute(
        sa.text(
            """
            UPDATE platform.schema_manifest
            SET foundation_version = 'v60.foundation.013',
                manifest_json = manifest_json
                    || '{"schema_revision": "0021_source_coordinate_review",
                         "mingli_reading_version":
                             "v60.mingli-reading.006",
                         "mingli_source_review_vector_version":
                             "v60.mingli-source-coordinate-review-vector.001"}'
                       ::jsonb,
                updated_at = now()
            WHERE singleton_id = 1
            """
        )
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            """
            DROP TRIGGER IF EXISTS trg_mingli_source_review_vectors_append_only
                ON mingli.source_coordinate_review_vectors;
            DROP FUNCTION IF EXISTS
                mingli.reject_source_review_vector_mutation();
            """
        )
    )
    op.drop_constraint(
        "fk_mingli_reading_source_review_vector",
        "readings",
        schema="mingli",
        type_="foreignkey",
    )
    for column in (
        "source_review_vector_hash",
        "source_review_vector_ref",
        "source_review_profile_hash",
        "source_review_profile_ref",
    ):
        op.drop_column("readings", column, schema="mingli")
    op.drop_index(
        "ix_mingli_source_review_vector_case",
        table_name="source_coordinate_review_vectors",
        schema="mingli",
    )
    op.drop_table("source_coordinate_review_vectors", schema="mingli")
    op.execute(
        sa.text(
            """
            UPDATE platform.schema_manifest
            SET foundation_version = 'v60.foundation.012',
                manifest_json = (
                    manifest_json
                    - 'mingli_source_review_vector_version'
                ) || '{"schema_revision": "0020_three_life_qualification",
                       "mingli_reading_version":
                           "v60.mingli-reading.005"}'::jsonb,
                updated_at = now()
            WHERE singleton_id = 1
            """
        )
    )
