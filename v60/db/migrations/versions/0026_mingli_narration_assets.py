"""Persist private, projection-bound Mingli narration assets.

Revision ID: 0026_mingli_narration_assets
Revises: 0025_dream_personal_journey
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0026_mingli_narration_assets"
down_revision: str | None = "0025_dream_personal_journey"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "mingli_narration_assets",
        sa.Column("narration_ref", sa.String(length=180), primary_key=True),
        sa.Column("narration_version", sa.String(length=100), nullable=False),
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
            "reading_ref",
            sa.String(length=180),
            sa.ForeignKey("mingli.readings.reading_ref"),
            nullable=True,
        ),
        sa.Column("source_scope", sa.String(length=60), nullable=False),
        sa.Column("stage_projection_ref", sa.String(length=180), nullable=False),
        sa.Column("stage_projection_hash", sa.String(length=64), nullable=False),
        sa.Column("cue_set_ref", sa.String(length=180), nullable=False),
        sa.Column("script_ref", sa.String(length=180), nullable=False),
        sa.Column("script_hash", sa.String(length=64), nullable=False),
        sa.Column("actor_ref", sa.String(length=160), nullable=False),
        sa.Column("voice_profile_ref", sa.String(length=180), nullable=False),
        sa.Column("voice_profile_hash", sa.String(length=64), nullable=False),
        sa.Column("provider_profile_ref", sa.String(length=180), nullable=False),
        sa.Column("provider_profile_hash", sa.String(length=64), nullable=False),
        sa.Column("provider_deployment_ref", sa.String(length=180), nullable=False),
        sa.Column("audio_mime_type", sa.String(length=80), nullable=False),
        sa.Column("audio_sha256", sa.String(length=64), nullable=False),
        sa.Column("audio_byte_length", sa.BigInteger(), nullable=False),
        sa.Column("duration_ms", sa.BigInteger(), nullable=False),
        sa.Column("sample_rate_hz", sa.Integer(), nullable=False),
        sa.Column("channels", sa.Integer(), nullable=False),
        sa.Column("sample_width_bytes", sa.Integer(), nullable=False),
        sa.Column(
            "narration_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column("narration_hash", sa.String(length=64), nullable=False),
        sa.Column("audio_bytes", sa.LargeBinary(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint("generation_key", name="uq_media_mingli_narration_generation"),
        sa.UniqueConstraint("narration_hash", name="uq_media_mingli_narration_hash"),
        sa.CheckConstraint(
            "source_scope <> 'FORMAL_READING' OR reading_ref IS NOT NULL",
            name="ck_media_mingli_narration_reading_binding",
        ),
        sa.CheckConstraint(
            "audio_byte_length > 0 AND audio_byte_length <= 8388608",
            name="ck_media_mingli_narration_audio_size",
        ),
        sa.CheckConstraint("duration_ms > 0", name="ck_media_mingli_narration_duration"),
        sa.CheckConstraint("sample_rate_hz > 0", name="ck_media_mingli_narration_rate"),
        sa.CheckConstraint("channels = 1", name="ck_media_mingli_narration_mono"),
        sa.CheckConstraint(
            "sample_width_bytes = 2",
            name="ck_media_mingli_narration_sample_width",
        ),
        schema="media",
    )
    op.create_index(
        "ix_media_mingli_narration_owner_case",
        "mingli_narration_assets",
        ["requester_account_ref", "case_ref", "created_at"],
        schema="media",
    )
    op.execute(
        sa.text(
            """
            CREATE FUNCTION media.reject_mingli_narration_mutation()
            RETURNS trigger
            LANGUAGE plpgsql
            AS $$
            BEGIN
                RAISE EXCEPTION 'mingli_narration_assets_are_append_only';
            END;
            $$;

            CREATE TRIGGER trg_media_mingli_narration_append_only
            BEFORE UPDATE OR DELETE
            ON media.mingli_narration_assets
            FOR EACH ROW
            EXECUTE FUNCTION media.reject_mingli_narration_mutation();
            """
        )
    )
    op.execute(
        sa.text(
            """
            UPDATE platform.schema_manifest
            SET foundation_version = 'v60.foundation.018',
                manifest_json = manifest_json
                    || '{"schema_revision": "0026_mingli_narration_assets",
                         "mingli_stage_projection_version":
                             "v60.mingli-stage-projection.001",
                         "mingli_narration_version":
                             "v60.mingli-narration.001"}'::jsonb,
                updated_at = now()
            WHERE singleton_id = 1
            """
        )
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            """
            DROP TRIGGER IF EXISTS trg_media_mingli_narration_append_only
                ON media.mingli_narration_assets;
            DROP FUNCTION IF EXISTS media.reject_mingli_narration_mutation();
            """
        )
    )
    op.drop_index(
        "ix_media_mingli_narration_owner_case",
        table_name="mingli_narration_assets",
        schema="media",
    )
    op.drop_table("mingli_narration_assets", schema="media")
    op.execute(
        sa.text(
            """
            UPDATE platform.schema_manifest
            SET foundation_version = 'v60.foundation.017',
                manifest_json = (
                    manifest_json
                    - 'mingli_stage_projection_version'
                    - 'mingli_narration_version'
                ) || '{"schema_revision":
                           "0025_dream_personal_journey"}'::jsonb,
                updated_at = now()
            WHERE singleton_id = 1
            """
        )
    )
