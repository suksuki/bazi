"""Add independently generated focused passes for progressive product reading.

Revision ID: 0049_mingli_focused_passes
Revises: 0048_mingli_focused_readings
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0049_mingli_focused_passes"
down_revision: str | None = "0048_mingli_focused_readings"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "focused_pass_records",
        sa.Column("record_ref", sa.String(length=180), nullable=False),
        sa.Column("record_version", sa.String(length=100), nullable=False),
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
        sa.Column("focus", sa.String(length=80), nullable=False),
        sa.Column("structure_pass_hash", sa.String(length=64), nullable=True),
        sa.Column("pass_json", postgresql.JSONB(), nullable=False),
        sa.Column("record_hash", sa.String(length=64), nullable=False),
        sa.Column("pass_hash", sa.String(length=64), nullable=False),
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
        sa.PrimaryKeyConstraint("record_ref"),
        sa.UniqueConstraint("generation_key"),
        sa.UniqueConstraint("record_hash"),
        schema="mingli",
    )
    op.create_index(
        "ix_mingli_focused_pass_records_current",
        "focused_pass_records",
        [
            "requester_account_ref",
            "case_ref",
            "reading_ref",
            "focus",
            "created_at",
        ],
        unique=False,
        schema="mingli",
    )
    op.execute(
        sa.text(
            """
            CREATE FUNCTION mingli.reject_focused_pass_record_mutation()
            RETURNS trigger
            LANGUAGE plpgsql
            AS $$
            BEGIN
                RAISE EXCEPTION 'mingli_focused_pass_records_are_append_only';
            END;
            $$;

            CREATE TRIGGER trg_mingli_focused_pass_records_append_only
            BEFORE UPDATE OR DELETE ON mingli.focused_pass_records
            FOR EACH ROW
            EXECUTE FUNCTION mingli.reject_focused_pass_record_mutation();
            """
        )
    )
    op.execute(
        sa.text(
            """
            UPDATE platform.schema_manifest
            SET foundation_version = 'v60.foundation.041',
                manifest_json = manifest_json
                    || '{"schema_revision":
                             "0049_mingli_focused_passes",
                         "mingli_focused_pass_record_version":
                             "v60.mingli-focused-pass-record.001",
                         "mingli_focused_pass_request_version":
                             "v60.mingli-focused-pass-request.001",
                         "mingli_reading_summary_version":
                             "v60.mingli-reading-summary.008"}'::jsonb,
                updated_at = now()
            WHERE singleton_id = 1
            """
        )
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            """
            DROP TRIGGER IF EXISTS trg_mingli_focused_pass_records_append_only
                ON mingli.focused_pass_records;
            DROP FUNCTION IF EXISTS mingli.reject_focused_pass_record_mutation();
            """
        )
    )
    op.drop_index(
        "ix_mingli_focused_pass_records_current",
        table_name="focused_pass_records",
        schema="mingli",
    )
    op.drop_table("focused_pass_records", schema="mingli")
    op.execute(
        sa.text(
            """
            UPDATE platform.schema_manifest
            SET foundation_version = 'v60.foundation.040',
                manifest_json = (manifest_json
                    - 'mingli_focused_pass_record_version'
                    - 'mingli_focused_pass_request_version')
                    || '{"schema_revision":
                             "0048_mingli_focused_readings",
                         "mingli_reading_summary_version":
                             "v60.mingli-reading-summary.007"}'::jsonb,
                updated_at = now()
            WHERE singleton_id = 1
            """
        )
    )
