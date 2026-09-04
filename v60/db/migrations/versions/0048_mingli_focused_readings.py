"""Add append-only multi-pass prose readings for the product Runtime.

Revision ID: 0048_mingli_focused_readings
Revises: 0047_mingli_resolution_guard
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0048_mingli_focused_readings"
down_revision: str | None = "0047_mingli_resolution_guard"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "focused_readings",
        sa.Column("focused_reading_ref", sa.String(length=180), nullable=False),
        sa.Column("focused_reading_version", sa.String(length=100), nullable=False),
        sa.Column("generation_key", sa.String(length=64), nullable=False),
        sa.Column("requester_account_ref", sa.String(length=160), nullable=False),
        sa.Column("case_ref", sa.String(length=160), nullable=False),
        sa.Column("chart_version_ref", sa.String(length=160), nullable=False),
        sa.Column("life_case_revision_ref", sa.String(length=180), nullable=False),
        sa.Column("reading_ref", sa.String(length=180), nullable=False),
        sa.Column("reading_hash", sa.String(length=64), nullable=False),
        sa.Column("packet_ref", sa.String(length=180), nullable=False),
        sa.Column("packet_hash", sa.String(length=64), nullable=False),
        sa.Column("runtime_ref", sa.String(length=100), nullable=False),
        sa.Column("provider_id", sa.String(length=80), nullable=False),
        sa.Column("model_ref", sa.String(length=180), nullable=False),
        sa.Column("model_digest", sa.String(length=64), nullable=False),
        sa.Column("provider_profile_ref", sa.String(length=180), nullable=False),
        sa.Column("provider_profile_hash", sa.String(length=64), nullable=False),
        sa.Column("prompt_version", sa.String(length=100), nullable=False),
        sa.Column("prompt_hash", sa.String(length=64), nullable=False),
        sa.Column("focused_reading_json", postgresql.JSONB(), nullable=False),
        sa.Column("focused_reading_hash", sa.String(length=64), nullable=False),
        sa.Column("input_tokens", sa.Integer(), nullable=False),
        sa.Column("output_tokens", sa.Integer(), nullable=False),
        sa.Column("total_tokens", sa.Integer(), nullable=False),
        sa.Column("duration_ms", sa.BigInteger(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("focused_reading_ref"),
        sa.UniqueConstraint("focused_reading_hash"),
        sa.UniqueConstraint("generation_key"),
        schema="mingli",
    )
    op.create_index(
        "ix_mingli_focused_readings_current",
        "focused_readings",
        [
            "requester_account_ref",
            "case_ref",
            "reading_ref",
            "created_at",
        ],
        unique=False,
        schema="mingli",
    )
    op.execute(
        sa.text(
            """
            CREATE FUNCTION mingli.reject_focused_reading_mutation()
            RETURNS trigger
            LANGUAGE plpgsql
            AS $$
            BEGIN
                RAISE EXCEPTION 'mingli_focused_readings_are_append_only';
            END;
            $$;

            CREATE TRIGGER trg_mingli_focused_readings_append_only
            BEFORE UPDATE OR DELETE ON mingli.focused_readings
            FOR EACH ROW
            EXECUTE FUNCTION mingli.reject_focused_reading_mutation();
            """
        )
    )
    op.execute(
        sa.text(
            """
            UPDATE platform.schema_manifest
            SET foundation_version = 'v60.foundation.040',
                manifest_json = manifest_json
                    || '{"schema_revision":
                             "0048_mingli_focused_readings",
                         "mingli_focused_runtime_version":
                             "v60.mingli-focused-runtime.001",
                         "mingli_focused_reading_version":
                             "v60.mingli-focused-reading.001",
                         "mingli_focused_pass_version":
                             "v60.mingli-focused-pass.001",
                         "mingli_focused_request_version":
                             "v60.mingli-focused-request.001",
                         "mingli_focused_prompt_version":
                             "v60.prompt.mingli-focused-reading.001",
                         "mingli_reading_summary_version":
                             "v60.mingli-reading-summary.007"}'::jsonb,
                updated_at = now()
            WHERE singleton_id = 1
            """
        )
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            """
            DROP TRIGGER IF EXISTS trg_mingli_focused_readings_append_only
                ON mingli.focused_readings;
            DROP FUNCTION IF EXISTS mingli.reject_focused_reading_mutation();
            """
        )
    )
    op.drop_index(
        "ix_mingli_focused_readings_current",
        table_name="focused_readings",
        schema="mingli",
    )
    op.drop_table("focused_readings", schema="mingli")
    op.execute(
        sa.text(
            """
            UPDATE platform.schema_manifest
            SET foundation_version = 'v60.foundation.039',
                manifest_json = (manifest_json
                    - 'mingli_focused_runtime_version'
                    - 'mingli_focused_reading_version'
                    - 'mingli_focused_pass_version'
                    - 'mingli_focused_request_version'
                    - 'mingli_focused_prompt_version')
                    || '{"schema_revision":
                             "0047_mingli_resolution_guard",
                         "mingli_reading_summary_version":
                             "v60.mingli-reading-summary.006"}'::jsonb,
                updated_at = now()
            WHERE singleton_id = 1
            """
        )
    )
