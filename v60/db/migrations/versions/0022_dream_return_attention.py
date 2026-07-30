"""Persist account-private Dream return attention and same-tree application.

Revision ID: 0022_dream_return_attention
Revises: 0021_source_coordinate_review
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0022_dream_return_attention"
down_revision: str | None = "0021_source_coordinate_review"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "return_attention_selections",
        sa.Column("attention_ref", sa.String(length=180), primary_key=True),
        sa.Column(
            "viewer_account_ref",
            sa.String(length=160),
            sa.ForeignKey("identity.accounts.account_ref"),
            nullable=False,
        ),
        sa.Column(
            "source_encounter_ref",
            sa.String(length=180),
            sa.ForeignKey("dream.encounters.encounter_ref"),
            nullable=False,
        ),
        sa.Column("source_encounter_version", sa.BigInteger(), nullable=False),
        sa.Column("source_echo_ref", sa.String(length=180), nullable=False),
        sa.Column("source_echo_hash", sa.String(length=64), nullable=False),
        sa.Column(
            "source_candidate_ref",
            sa.String(length=180),
            sa.ForeignKey("dream.grove_candidates.candidate_ref"),
            nullable=False,
        ),
        sa.Column("source_candidate_hash", sa.String(length=64), nullable=False),
        sa.Column(
            "tree_ref",
            sa.String(length=180),
            sa.ForeignKey("dream.life_trees.tree_ref"),
            nullable=False,
        ),
        sa.Column("observation_ref", sa.String(length=180), nullable=False),
        sa.Column("idempotency_key", sa.String(length=180), nullable=False),
        sa.Column(
            "record_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column("record_hash", sa.String(length=64), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint(
            "viewer_account_ref",
            "source_encounter_ref",
            name="uq_dream_return_attention_source",
        ),
        sa.UniqueConstraint(
            "viewer_account_ref",
            "idempotency_key",
            name="uq_dream_return_attention_idempotency",
        ),
        sa.UniqueConstraint(
            "record_hash",
            name="uq_dream_return_attention_record_hash",
        ),
        schema="dream",
    )
    op.create_index(
        "ix_dream_return_attention_pending_tree",
        "return_attention_selections",
        ["viewer_account_ref", "tree_ref", "created_at"],
        schema="dream",
    )
    op.create_table(
        "return_attention_applications",
        sa.Column("application_ref", sa.String(length=180), primary_key=True),
        sa.Column(
            "viewer_account_ref",
            sa.String(length=160),
            sa.ForeignKey("identity.accounts.account_ref"),
            nullable=False,
        ),
        sa.Column(
            "attention_ref",
            sa.String(length=180),
            sa.ForeignKey("dream.return_attention_selections.attention_ref"),
            nullable=False,
            unique=True,
        ),
        sa.Column(
            "encounter_ref",
            sa.String(length=180),
            sa.ForeignKey("dream.encounters.encounter_ref"),
            nullable=False,
            unique=True,
        ),
        sa.Column(
            "tree_ref",
            sa.String(length=180),
            sa.ForeignKey("dream.life_trees.tree_ref"),
            nullable=False,
        ),
        sa.Column(
            "application_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column("application_hash", sa.String(length=64), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint(
            "application_hash",
            name="uq_dream_return_attention_application_hash",
        ),
        schema="dream",
    )
    op.create_index(
        "ix_dream_return_attention_application_owner",
        "return_attention_applications",
        ["viewer_account_ref", "encounter_ref"],
        schema="dream",
    )
    op.execute(
        sa.text(
            """
            CREATE FUNCTION dream.reject_return_attention_mutation()
            RETURNS trigger
            LANGUAGE plpgsql
            AS $$
            BEGIN
                RAISE EXCEPTION 'dream_return_attention_is_append_only';
            END;
            $$;

            CREATE TRIGGER trg_dream_return_attention_selection_append_only
            BEFORE UPDATE OR DELETE
            ON dream.return_attention_selections
            FOR EACH ROW
            EXECUTE FUNCTION dream.reject_return_attention_mutation();

            CREATE TRIGGER trg_dream_return_attention_application_append_only
            BEFORE UPDATE OR DELETE
            ON dream.return_attention_applications
            FOR EACH ROW
            EXECUTE FUNCTION dream.reject_return_attention_mutation();
            """
        )
    )
    op.execute(
        sa.text(
            """
            UPDATE platform.schema_manifest
            SET foundation_version = 'v60.foundation.014',
                manifest_json = manifest_json
                    || '{"schema_revision": "0022_dream_return_attention",
                         "dream_game_engine_version":
                             "v60.dream-game-engine.015",
                         "dream_grove_version": "v60.dream-grove.003",
                         "dream_return_attention_version":
                             "v60.dream-return-attention.001",
                         "dream_opening_attention_version":
                             "v60.dream-opening-attention.001"}'::jsonb,
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
                trg_dream_return_attention_application_append_only
                ON dream.return_attention_applications;
            DROP TRIGGER IF EXISTS
                trg_dream_return_attention_selection_append_only
                ON dream.return_attention_selections;
            DROP FUNCTION IF EXISTS dream.reject_return_attention_mutation();
            """
        )
    )
    op.drop_index(
        "ix_dream_return_attention_application_owner",
        table_name="return_attention_applications",
        schema="dream",
    )
    op.drop_table("return_attention_applications", schema="dream")
    op.drop_index(
        "ix_dream_return_attention_pending_tree",
        table_name="return_attention_selections",
        schema="dream",
    )
    op.drop_table("return_attention_selections", schema="dream")
    op.execute(
        sa.text(
            """
            UPDATE platform.schema_manifest
            SET foundation_version = 'v60.foundation.013',
                manifest_json = (
                    manifest_json
                    - 'dream_return_attention_version'
                    - 'dream_opening_attention_version'
                ) || '{"schema_revision": "0021_source_coordinate_review",
                       "dream_game_engine_version":
                           "v60.dream-game-engine.014",
                       "dream_grove_version": "v60.dream-grove.002"}'::jsonb,
                updated_at = now()
            WHERE singleton_id = 1
            """
        )
    )
