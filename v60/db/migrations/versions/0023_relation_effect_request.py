"""Persist account-private relation-effect evidence preparation requests.

Revision ID: 0023_relation_effect_request
Revises: 0022_dream_return_attention
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0023_relation_effect_request"
down_revision: str | None = "0022_dream_return_attention"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "relation_effect_evidence_request_receipts",
        sa.Column("receipt_ref", sa.String(length=180), primary_key=True),
        sa.Column(
            "receipt_version",
            sa.String(length=100),
            nullable=False,
        ),
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
            nullable=False,
        ),
        sa.Column("packet_ref", sa.String(length=180), nullable=False),
        sa.Column("packet_hash", sa.String(length=64), nullable=False),
        sa.Column(
            "idempotency_key",
            sa.String(length=180),
            nullable=False,
        ),
        sa.Column(
            "receipt_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column("receipt_hash", sa.String(length=64), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint(
            "requester_account_ref",
            "idempotency_key",
            name="uq_mingli_relation_effect_request_idempotency",
        ),
        sa.UniqueConstraint(
            "requester_account_ref",
            "packet_ref",
            name="uq_mingli_relation_effect_request_packet",
        ),
        sa.UniqueConstraint(
            "receipt_hash",
            name="uq_mingli_relation_effect_request_receipt_hash",
        ),
        schema="mingli",
    )
    op.create_index(
        "ix_mingli_relation_effect_request_owner_case",
        "relation_effect_evidence_request_receipts",
        ["requester_account_ref", "case_ref", "created_at"],
        schema="mingli",
    )
    op.execute(
        sa.text(
            """
            CREATE FUNCTION
                mingli.reject_relation_effect_evidence_request_mutation()
            RETURNS trigger
            LANGUAGE plpgsql
            AS $$
            BEGIN
                RAISE EXCEPTION
                    'mingli_relation_effect_evidence_requests_are_append_only';
            END;
            $$;

            CREATE TRIGGER
                trg_mingli_relation_effect_evidence_requests_append_only
            BEFORE UPDATE OR DELETE
            ON mingli.relation_effect_evidence_request_receipts
            FOR EACH ROW
            EXECUTE FUNCTION
                mingli.reject_relation_effect_evidence_request_mutation();
            """
        )
    )
    op.execute(
        sa.text(
            """
            UPDATE platform.schema_manifest
            SET foundation_version = 'v60.foundation.015',
                manifest_json = manifest_json
                    || '{"schema_revision":
                             "0023_relation_effect_request",
                         "mingli_relation_effect_evidence_request_version":
                             "v60.mingli-relation-effect-evidence-request-receipt.001"}'
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
            DROP TRIGGER IF EXISTS
                trg_mingli_relation_effect_evidence_requests_append_only
                ON mingli.relation_effect_evidence_request_receipts;
            DROP FUNCTION IF EXISTS
                mingli.reject_relation_effect_evidence_request_mutation();
            """
        )
    )
    op.drop_index(
        "ix_mingli_relation_effect_request_owner_case",
        table_name="relation_effect_evidence_request_receipts",
        schema="mingli",
    )
    op.drop_table(
        "relation_effect_evidence_request_receipts",
        schema="mingli",
    )
    op.execute(
        sa.text(
            """
            UPDATE platform.schema_manifest
            SET foundation_version = 'v60.foundation.014',
                manifest_json = (
                    manifest_json
                    - 'mingli_relation_effect_evidence_request_version'
                ) || '{"schema_revision":
                           "0022_dream_return_attention"}'::jsonb,
                updated_at = now()
            WHERE singleton_id = 1
            """
        )
    )
