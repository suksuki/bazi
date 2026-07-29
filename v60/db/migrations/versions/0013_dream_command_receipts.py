"""Persist exact Dream command receipts.

Revision ID: 0013_dream_command_receipts
Revises: 0012_owner_admission
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0013_dream_command_receipts"
down_revision: str | None = "0012_owner_admission"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "command_receipts",
        sa.Column("command_receipt_ref", sa.String(length=180), primary_key=True),
        sa.Column(
            "viewer_account_ref",
            sa.String(length=160),
            sa.ForeignKey("identity.accounts.account_ref"),
            nullable=False,
        ),
        sa.Column(
            "encounter_ref",
            sa.String(length=180),
            sa.ForeignKey("dream.encounters.encounter_ref"),
            nullable=False,
        ),
        sa.Column("idempotency_key", sa.String(length=180), nullable=False),
        sa.Column("command", sa.String(length=80), nullable=False),
        sa.Column("expected_version", sa.BigInteger(), nullable=False),
        sa.Column(
            "envelope_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column("envelope_hash", sa.String(length=64), nullable=False),
        sa.Column(
            "result_encounter_ref",
            sa.String(length=180),
            sa.ForeignKey("dream.encounters.encounter_ref"),
            nullable=False,
        ),
        sa.Column("result_version", sa.BigInteger(), nullable=False),
        sa.Column("result_status", sa.String(length=80), nullable=False),
        sa.Column("result_state_hash", sa.String(length=64), nullable=False),
        sa.Column("receipt_hash", sa.String(length=64), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint(
            "viewer_account_ref",
            "idempotency_key",
            name="uq_dream_command_idempotency",
        ),
        sa.UniqueConstraint(
            "receipt_hash",
            name="uq_dream_command_receipt_hash",
        ),
        schema="dream",
    )
    op.create_index(
        "ix_dream_command_receipt_encounter",
        "command_receipts",
        ["encounter_ref", "created_at"],
        schema="dream",
    )
    op.execute(
        sa.text(
            """
            UPDATE platform.schema_manifest
            SET foundation_version = 'v60.foundation.005',
                manifest_json = manifest_json
                    || '{"decision_kernel": "v60.cognitive-decision-kernel.003",
                         "schema_revision": "0013_dream_command_receipts",
                         "dream_command_receipt_version":
                             "v60.dream-command-receipt.001"}'::jsonb,
                updated_at = now()
            WHERE singleton_id = 1
            """
        )
    )


def downgrade() -> None:
    op.drop_index(
        "ix_dream_command_receipt_encounter",
        table_name="command_receipts",
        schema="dream",
    )
    op.drop_table("command_receipts", schema="dream")
    op.execute(
        sa.text(
            """
            UPDATE platform.schema_manifest
            SET foundation_version = 'v60.foundation.001',
                manifest_json = (manifest_json
                    - 'schema_revision'
                    - 'dream_command_receipt_version')
                    || '{"decision_kernel":
                             "v60.cognitive-decision-kernel.001"}'::jsonb,
                updated_at = now()
            WHERE singleton_id = 1
            """
        )
    )
