"""Persist append-only, Case-bound Mingli Agent interpretations.

Revision ID: 0028_mingli_agent_readings
Revises: 0027_mingli_narration_v2
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0028_mingli_agent_readings"
down_revision: str | None = "0027_mingli_narration_v2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "agent_readings",
        sa.Column("agent_reading_ref", sa.String(length=180), primary_key=True),
        sa.Column("agent_reading_version", sa.String(length=100), nullable=False),
        sa.Column("generation_key", sa.String(length=64), nullable=False),
        sa.Column(
            "requester_account_ref",
            sa.String(length=160),
            sa.ForeignKey("identity.accounts.account_ref"),
            nullable=False,
        ),
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
            "reading_ref",
            sa.String(length=180),
            sa.ForeignKey("mingli.readings.reading_ref"),
            nullable=False,
        ),
        sa.Column("reading_hash", sa.String(length=64), nullable=False),
        sa.Column("packet_ref", sa.String(length=180), nullable=False),
        sa.Column("packet_hash", sa.String(length=64), nullable=False),
        sa.Column("agent_profile_ref", sa.String(length=180), nullable=False),
        sa.Column("agent_profile_hash", sa.String(length=64), nullable=False),
        sa.Column("provider_id", sa.String(length=80), nullable=False),
        sa.Column("model_ref", sa.String(length=180), nullable=False),
        sa.Column("model_digest", sa.String(length=64), nullable=False),
        sa.Column("provider_profile_ref", sa.String(length=180), nullable=False),
        sa.Column("provider_profile_hash", sa.String(length=64), nullable=False),
        sa.Column("prompt_ref", sa.String(length=180), nullable=False),
        sa.Column("prompt_hash", sa.String(length=64), nullable=False),
        sa.Column("provider_response_ref", sa.String(length=180), nullable=False),
        sa.Column("interpretation_status", sa.String(length=60), nullable=False),
        sa.Column("owner_review_status", sa.String(length=60), nullable=False),
        sa.Column("canonical_fact_write_allowed", sa.Boolean(), nullable=False),
        sa.Column("read_only", sa.Boolean(), nullable=False),
        sa.Column(
            "agent_reading_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column("agent_reading_hash", sa.String(length=64), nullable=False),
        sa.Column("input_tokens", sa.Integer(), nullable=False),
        sa.Column("output_tokens", sa.Integer(), nullable=False),
        sa.Column("total_tokens", sa.Integer(), nullable=False),
        sa.Column("duration_ms", sa.BigInteger(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint(
            "generation_key",
            name="uq_mingli_agent_reading_generation",
        ),
        sa.UniqueConstraint(
            "agent_reading_hash",
            name="uq_mingli_agent_reading_hash",
        ),
        sa.CheckConstraint(
            "input_tokens >= 0 AND output_tokens >= 0 AND total_tokens >= 0",
            name="ck_mingli_agent_reading_token_counts",
        ),
        sa.CheckConstraint(
            "total_tokens = input_tokens + output_tokens",
            name="ck_mingli_agent_reading_token_total",
        ),
        sa.CheckConstraint(
            "duration_ms >= 0",
            name="ck_mingli_agent_reading_duration",
        ),
        sa.CheckConstraint(
            "interpretation_status = 'AGENT_INTERPRETATION'",
            name="ck_mingli_agent_reading_interpretation_status",
        ),
        sa.CheckConstraint(
            "owner_review_status = 'NOT_REVIEWED'",
            name="ck_mingli_agent_reading_owner_review_status",
        ),
        sa.CheckConstraint(
            "canonical_fact_write_allowed = false AND read_only = true",
            name="ck_mingli_agent_reading_governance",
        ),
        schema="mingli",
    )
    op.create_index(
        "ix_mingli_agent_reading_owner_case_created",
        "agent_readings",
        ["requester_account_ref", "case_ref", "created_at"],
        schema="mingli",
    )
    op.create_index(
        "ix_mingli_agent_reading_reading_created",
        "agent_readings",
        ["reading_ref", "created_at"],
        schema="mingli",
    )
    op.execute(
        sa.text(
            """
            CREATE FUNCTION mingli.reject_agent_reading_mutation()
            RETURNS trigger
            LANGUAGE plpgsql
            AS $$
            BEGIN
                RAISE EXCEPTION 'mingli_agent_readings_are_append_only';
            END;
            $$;

            CREATE TRIGGER trg_mingli_agent_readings_append_only
            BEFORE UPDATE OR DELETE ON mingli.agent_readings
            FOR EACH ROW EXECUTE FUNCTION mingli.reject_agent_reading_mutation();
            """
        )
    )
    op.execute(
        sa.text(
            """
            UPDATE platform.schema_manifest
            SET foundation_version = 'v60.foundation.020',
                manifest_json = manifest_json
                    || '{"schema_revision": "0028_mingli_agent_readings",
                         "mingli_agent_packet_version":
                             "v60.mingli-agent-case-packet.001",
                         "mingli_agent_reading_version":
                             "v60.mingli-agent-reading.001"}'::jsonb,
                updated_at = now()
            WHERE singleton_id = 1
            """
        )
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            """
            DROP TRIGGER IF EXISTS trg_mingli_agent_readings_append_only
                ON mingli.agent_readings;
            DROP FUNCTION IF EXISTS mingli.reject_agent_reading_mutation();
            """
        )
    )
    op.drop_index(
        "ix_mingli_agent_reading_reading_created",
        table_name="agent_readings",
        schema="mingli",
    )
    op.drop_index(
        "ix_mingli_agent_reading_owner_case_created",
        table_name="agent_readings",
        schema="mingli",
    )
    op.drop_table("agent_readings", schema="mingli")
    op.execute(
        sa.text(
            """
            UPDATE platform.schema_manifest
            SET foundation_version = 'v60.foundation.019',
                manifest_json = (
                    manifest_json
                    - 'mingli_agent_packet_version'
                    - 'mingli_agent_reading_version'
                ) || '{"schema_revision":
                           "0027_mingli_narration_v2"}'::jsonb,
                updated_at = now()
            WHERE singleton_id = 1
            """
        )
    )
