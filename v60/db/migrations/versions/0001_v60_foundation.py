"""Create the V60 authority, world and media foundation.

Revision ID: 0001_v60_foundation
Revises:
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001_v60_foundation"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    for schema in ("platform", "media", "cognition", "world"):
        op.execute(sa.text(f'CREATE SCHEMA IF NOT EXISTS "{schema}"'))

    op.create_table(
        "schema_manifest",
        sa.Column("singleton_id", sa.Integer(), primary_key=True),
        sa.Column("foundation_version", sa.String(length=80), nullable=False),
        sa.Column("manifest_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        schema="platform",
    )

    op.create_table(
        "asset_versions",
        sa.Column("asset_ref", sa.String(length=160), primary_key=True),
        sa.Column("asset_version", sa.String(length=80), primary_key=True),
        sa.Column("sha256", sa.String(length=64), nullable=False),
        sa.Column("media_type", sa.String(length=80), nullable=False),
        sa.Column("runtime_path", sa.Text(), nullable=False),
        sa.Column("source_manifest_ref", sa.Text(), nullable=False),
        sa.Column("source_status", sa.String(length=80), nullable=False),
        sa.Column("v60_role", sa.String(length=120), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        schema="media",
    )

    op.create_table(
        "decision_records",
        sa.Column("decision_id", sa.String(length=160), primary_key=True),
        sa.Column("decision_type", sa.String(length=80), nullable=False),
        sa.Column("subject_ref", sa.String(length=200), nullable=False),
        sa.Column("authority", sa.String(length=80), nullable=False),
        sa.Column("method", sa.String(length=120), nullable=False),
        sa.Column("status", sa.String(length=80), nullable=False),
        sa.Column("correlation_id", sa.String(length=160), nullable=False),
        sa.Column("causation_id", sa.String(length=160), nullable=False),
        sa.Column("record_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("record_hash", sa.String(length=64), nullable=False, unique=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        schema="cognition",
    )

    op.create_table(
        "worlds",
        sa.Column("world_ref", sa.String(length=160), primary_key=True),
        sa.Column("world_version", sa.String(length=80), nullable=False),
        sa.Column("branch", sa.String(length=80), nullable=False),
        sa.Column("current_epoch", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("current_tick", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("state_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        schema="world",
    )

    op.create_table(
        "clock_epochs",
        sa.Column("world_ref", sa.String(length=160), primary_key=True),
        sa.Column("epoch", sa.BigInteger(), primary_key=True),
        sa.Column("start_tick", sa.BigInteger(), nullable=False),
        sa.Column("rate_numerator", sa.BigInteger(), nullable=False),
        sa.Column("rate_denominator", sa.BigInteger(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint("start_tick >= 0", name="ck_world_epoch_start_tick"),
        sa.CheckConstraint("rate_numerator >= 0", name="ck_world_epoch_rate_numerator"),
        sa.CheckConstraint("rate_denominator > 0", name="ck_world_epoch_rate_denominator"),
        schema="world",
    )

    op.execute(
        sa.text(
            """
            INSERT INTO platform.schema_manifest
                (singleton_id, foundation_version, manifest_json)
            VALUES
                (1, 'v60.foundation.001',
                 '{"v50_runtime_dependency": false,
                   "entry_experience": "DREAM_WORLD",
                   "decision_kernel": "v60.cognitive-decision-kernel.001"}'::jsonb)
            """
        )
    )
    op.execute(
        sa.text(
            """
            INSERT INTO world.worlds
                (world_ref, world_version, branch, current_epoch, current_tick, state_json)
            VALUES
                ('abu-dream-world-v1', 'v1', 'canonical_world', 0, 0,
                 '{"status": "FOUNDATION_READY", "actor_population": 0}'::jsonb)
            """
        )
    )
    op.execute(
        sa.text(
            """
            INSERT INTO world.clock_epochs
                (world_ref, epoch, start_tick, rate_numerator, rate_denominator)
            VALUES
                ('abu-dream-world-v1', 0, 0, 0, 1)
            """
        )
    )


def downgrade() -> None:
    op.drop_table("clock_epochs", schema="world")
    op.drop_table("worlds", schema="world")
    op.drop_table("decision_records", schema="cognition")
    op.drop_table("asset_versions", schema="media")
    op.drop_table("schema_manifest", schema="platform")
    for schema in ("world", "cognition", "media", "platform"):
        op.execute(sa.text(f'DROP SCHEMA IF EXISTS "{schema}"'))
