"""Add V60 identity, Case and lineage-owned Mingli records.

Revision ID: 0002_identity_case_foundation
Revises: 0001_v60_foundation
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002_identity_case_foundation"
down_revision: str | None = "0001_v60_foundation"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    for schema in ("identity", "mingli"):
        op.execute(sa.text(f'CREATE SCHEMA IF NOT EXISTS "{schema}"'))

    op.create_table(
        "migration_batches",
        sa.Column("batch_ref", sa.String(length=160), primary_key=True),
        sa.Column("source_system", sa.String(length=80), nullable=False),
        sa.Column("source_database", sa.String(length=160), nullable=False),
        sa.Column("status", sa.String(length=80), nullable=False),
        sa.Column("manifest_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("manifest_hash", sa.String(length=64), nullable=False, unique=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        schema="platform",
    )

    op.create_table(
        "accounts",
        sa.Column("account_ref", sa.String(length=160), primary_key=True),
        sa.Column("email", sa.String(length=320), nullable=False, unique=True),
        sa.Column("display_name", sa.String(length=160), nullable=False),
        sa.Column("account_role", sa.String(length=80), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("password_scheme", sa.String(length=120), nullable=False),
        sa.Column("password_hash", sa.String(length=128), nullable=False),
        sa.Column("password_salt", sa.String(length=128), nullable=False),
        sa.Column("source_ref", sa.String(length=240), nullable=False),
        sa.Column("source_hash", sa.String(length=64), nullable=False),
        sa.Column(
            "source_batch_ref",
            sa.String(length=160),
            sa.ForeignKey("platform.migration_batches.batch_ref"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        schema="identity",
    )

    op.create_table(
        "sessions",
        sa.Column("session_ref", sa.String(length=160), primary_key=True),
        sa.Column(
            "account_ref",
            sa.String(length=160),
            sa.ForeignKey("identity.accounts.account_ref"),
            nullable=False,
        ),
        sa.Column("token_hash", sa.String(length=64), nullable=False, unique=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        schema="identity",
    )

    op.create_table(
        "profiles",
        sa.Column("profile_ref", sa.String(length=160), primary_key=True),
        sa.Column(
            "account_ref",
            sa.String(length=160),
            sa.ForeignKey("identity.accounts.account_ref"),
            nullable=False,
        ),
        sa.Column("display_name", sa.String(length=160), nullable=False),
        sa.Column("gender", sa.String(length=40), nullable=False),
        sa.Column("calendar_type", sa.String(length=40), nullable=False),
        sa.Column("birth_date", sa.Date(), nullable=False),
        sa.Column("birth_time", sa.Time(), nullable=False),
        sa.Column("birth_location", sa.String(length=240), nullable=False),
        sa.Column("timezone", sa.String(length=80), nullable=False),
        sa.Column("source_ref", sa.String(length=240), nullable=False),
        sa.Column("source_hash", sa.String(length=64), nullable=False),
        sa.Column("input_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        schema="identity",
    )

    op.create_table(
        "cases",
        sa.Column("case_ref", sa.String(length=160), primary_key=True),
        sa.Column(
            "owner_account_ref",
            sa.String(length=160),
            sa.ForeignKey("identity.accounts.account_ref"),
            nullable=False,
        ),
        sa.Column(
            "profile_ref",
            sa.String(length=160),
            sa.ForeignKey("identity.profiles.profile_ref"),
            nullable=False,
        ),
        sa.Column("subject_kind", sa.String(length=80), nullable=False),
        sa.Column("status", sa.String(length=80), nullable=False),
        sa.Column("case_version", sa.BigInteger(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        schema="mingli",
    )

    op.create_table(
        "chart_versions",
        sa.Column("chart_version_ref", sa.String(length=160), primary_key=True),
        sa.Column(
            "case_ref",
            sa.String(length=160),
            sa.ForeignKey("mingli.cases.case_ref"),
            nullable=False,
        ),
        sa.Column("version", sa.BigInteger(), nullable=False),
        sa.Column("birth_input_hash", sa.String(length=64), nullable=False),
        sa.Column("pillars_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("algorithm_version", sa.String(length=120), nullable=False),
        sa.Column("source_manifest_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("chart_hash", sa.String(length=64), nullable=False, unique=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint("case_ref", "version", name="uq_mingli_chart_case_version"),
        schema="mingli",
    )

    op.create_table(
        "facts",
        sa.Column("fact_ref", sa.String(length=200), primary_key=True),
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
        sa.Column("fact_type", sa.String(length=120), nullable=False),
        sa.Column("subject_ref", sa.String(length=200), nullable=False),
        sa.Column("object_ref", sa.String(length=200), nullable=True),
        sa.Column("authority", sa.String(length=80), nullable=False),
        sa.Column("fact_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("source_ref", sa.String(length=240), nullable=False),
        sa.Column("fact_hash", sa.String(length=64), nullable=False, unique=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        schema="mingli",
    )

    op.create_table(
        "life_case_revisions",
        sa.Column("life_case_revision_ref", sa.String(length=180), primary_key=True),
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
        sa.Column("revision", sa.BigInteger(), nullable=False),
        sa.Column("status", sa.String(length=80), nullable=False),
        sa.Column("payload_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("evidence_manifest_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("revision_hash", sa.String(length=64), nullable=False, unique=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint("case_ref", "revision", name="uq_life_case_revision"),
        schema="mingli",
    )

    op.create_table(
        "canonical_scenes",
        sa.Column("scene_ref", sa.String(length=180), primary_key=True),
        sa.Column(
            "case_ref",
            sa.String(length=160),
            sa.ForeignKey("mingli.cases.case_ref"),
            nullable=False,
        ),
        sa.Column(
            "life_case_revision_ref",
            sa.String(length=180),
            sa.ForeignKey("mingli.life_case_revisions.life_case_revision_ref"),
            nullable=False,
        ),
        sa.Column("scene_version", sa.BigInteger(), nullable=False),
        sa.Column("scene_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("scene_hash", sa.String(length=64), nullable=False, unique=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint("case_ref", "scene_version", name="uq_canonical_scene_version"),
        schema="mingli",
    )


def downgrade() -> None:
    op.drop_table("canonical_scenes", schema="mingli")
    op.drop_table("life_case_revisions", schema="mingli")
    op.drop_table("facts", schema="mingli")
    op.drop_table("chart_versions", schema="mingli")
    op.drop_table("cases", schema="mingli")
    op.drop_table("profiles", schema="identity")
    op.drop_table("sessions", schema="identity")
    op.drop_table("accounts", schema="identity")
    op.drop_table("migration_batches", schema="platform")
    for schema in ("mingli", "identity"):
        op.execute(sa.text(f'DROP SCHEMA IF EXISTS "{schema}"'))
