"""Persist account-private relation-effect bibliography candidates.

Revision ID: 0024_relation_effect_material
Revises: 0023_relation_effect_request
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0024_relation_effect_material"
down_revision: str | None = "0023_relation_effect_request"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "relation_effect_evidence_material_records",
        sa.Column("material_ref", sa.String(length=180), primary_key=True),
        sa.Column(
            "material_version",
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
        sa.Column(
            "request_receipt_ref",
            sa.String(length=180),
            sa.ForeignKey("mingli.relation_effect_evidence_request_receipts.receipt_ref"),
            nullable=False,
        ),
        sa.Column(
            "request_receipt_hash",
            sa.String(length=64),
            nullable=False,
        ),
        sa.Column("packet_ref", sa.String(length=180), nullable=False),
        sa.Column("packet_hash", sa.String(length=64), nullable=False),
        sa.Column(
            "request_item_ref",
            sa.String(length=180),
            nullable=False,
        ),
        sa.Column(
            "demand_packet_ref",
            sa.String(length=180),
            nullable=False,
        ),
        sa.Column(
            "demand_packet_hash",
            sa.String(length=64),
            nullable=False,
        ),
        sa.Column("slot_ref", sa.String(length=180), nullable=False),
        sa.Column("dimension_id", sa.String(length=80), nullable=False),
        sa.Column("candidate_kind", sa.String(length=100), nullable=False),
        sa.Column(
            "target_artifact_kind",
            sa.String(length=100),
            nullable=False,
        ),
        sa.Column(
            "bibliography_hash",
            sa.String(length=64),
            nullable=False,
        ),
        sa.Column(
            "idempotency_key",
            sa.String(length=180),
            nullable=False,
        ),
        sa.Column(
            "material_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column("material_hash", sa.String(length=64), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint(
            "requester_account_ref",
            "idempotency_key",
            name="uq_mingli_relation_effect_material_idempotency",
        ),
        sa.UniqueConstraint(
            "material_hash",
            name="uq_mingli_relation_effect_material_hash",
        ),
        sa.UniqueConstraint(
            "requester_account_ref",
            "request_receipt_ref",
            "request_item_ref",
            "slot_ref",
            "bibliography_hash",
            name="uq_mingli_relation_effect_material_bibliography",
        ),
        schema="mingli",
    )
    op.create_index(
        "ix_mingli_relation_effect_material_owner_receipt",
        "relation_effect_evidence_material_records",
        ["requester_account_ref", "request_receipt_ref", "created_at"],
        schema="mingli",
    )
    op.execute(
        sa.text(
            """
            CREATE FUNCTION
                mingli.reject_relation_effect_evidence_material_mutation()
            RETURNS trigger
            LANGUAGE plpgsql
            AS $$
            BEGIN
                RAISE EXCEPTION
                    'mingli_relation_effect_evidence_materials_are_append_only';
            END;
            $$;

            CREATE TRIGGER
                trg_mingli_relation_effect_evidence_materials_append_only
            BEFORE UPDATE OR DELETE
            ON mingli.relation_effect_evidence_material_records
            FOR EACH ROW
            EXECUTE FUNCTION
                mingli.reject_relation_effect_evidence_material_mutation();
            """
        )
    )
    op.execute(
        sa.text(
            """
            UPDATE platform.schema_manifest
            SET foundation_version = 'v60.foundation.016',
                manifest_json = manifest_json
                    || '{"schema_revision":
                             "0024_relation_effect_material",
                         "mingli_relation_effect_evidence_material_version":
                             "v60.mingli-relation-effect-evidence-material.001"}'
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
                trg_mingli_relation_effect_evidence_materials_append_only
                ON mingli.relation_effect_evidence_material_records;
            DROP FUNCTION IF EXISTS
                mingli.reject_relation_effect_evidence_material_mutation();
            """
        )
    )
    op.drop_index(
        "ix_mingli_relation_effect_material_owner_receipt",
        table_name="relation_effect_evidence_material_records",
        schema="mingli",
    )
    op.drop_table(
        "relation_effect_evidence_material_records",
        schema="mingli",
    )
    op.execute(
        sa.text(
            """
            UPDATE platform.schema_manifest
            SET foundation_version = 'v60.foundation.015',
                manifest_json = (
                    manifest_json
                    - 'mingli_relation_effect_evidence_material_version'
                ) || '{"schema_revision":
                           "0023_relation_effect_request"}'::jsonb,
                updated_at = now()
            WHERE singleton_id = 1
            """
        )
    )
