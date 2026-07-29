"""Persist append-only, profile-pinned Mingli readings.

Revision ID: 0015_mingli_readings
Revises: 0014_episode_transitions
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0015_mingli_readings"
down_revision: str | None = "0014_episode_transitions"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "readings",
        sa.Column("reading_ref", sa.String(length=180), primary_key=True),
        sa.Column("reading_version", sa.String(length=80), nullable=False),
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
        sa.Column("foundation_profile_ref", sa.String(length=240), nullable=False),
        sa.Column("foundation_profile_hash", sa.String(length=64), nullable=False),
        sa.Column(
            "candidate_rule_profile_ref",
            sa.String(length=240),
            nullable=False,
        ),
        sa.Column(
            "candidate_rule_profile_hash",
            sa.String(length=64),
            nullable=False,
        ),
        sa.Column(
            "reading_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column("reading_hash", sa.String(length=64), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint("reading_hash", name="uq_mingli_reading_hash"),
        schema="mingli",
    )
    op.create_index(
        "ix_mingli_reading_case_created",
        "readings",
        ["case_ref", "created_at"],
        schema="mingli",
    )
    op.execute(
        sa.text(
            """
            CREATE FUNCTION mingli.reject_reading_mutation()
            RETURNS trigger
            LANGUAGE plpgsql
            AS $$
            BEGIN
                RAISE EXCEPTION 'mingli_readings_are_append_only';
            END;
            $$;

            CREATE TRIGGER trg_mingli_readings_append_only
            BEFORE UPDATE OR DELETE ON mingli.readings
            FOR EACH ROW EXECUTE FUNCTION mingli.reject_reading_mutation();
            """
        )
    )
    op.execute(
        sa.text(
            """
            UPDATE platform.schema_manifest
            SET foundation_version = 'v60.foundation.007',
                manifest_json = manifest_json
                    || '{"schema_revision": "0015_mingli_readings",
                         "mingli_reading_version":
                             "v60.mingli-reading.001"}'::jsonb,
                updated_at = now()
            WHERE singleton_id = 1
            """
        )
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            """
            DROP TRIGGER IF EXISTS trg_mingli_readings_append_only
                ON mingli.readings;
            DROP FUNCTION IF EXISTS mingli.reject_reading_mutation();
            """
        )
    )
    op.drop_index(
        "ix_mingli_reading_case_created",
        table_name="readings",
        schema="mingli",
    )
    op.drop_table("readings", schema="mingli")
    op.execute(
        sa.text(
            """
            UPDATE platform.schema_manifest
            SET foundation_version = 'v60.foundation.006',
                manifest_json = (manifest_json - 'mingli_reading_version')
                    || '{"schema_revision":
                             "0014_episode_transitions"}'::jsonb,
                updated_at = now()
            WHERE singleton_id = 1
            """
        )
    )
