"""Add private Mingli corpus qualification and Dream grove candidates.

Revision ID: 0020_three_life_qualification
Revises: 0019_mingli_life_domains
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0020_three_life_qualification"
down_revision: str | None = "0019_mingli_life_domains"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "corpus_qualification_runs",
        sa.Column("run_ref", sa.String(length=180), primary_key=True),
        sa.Column("run_version", sa.String(length=100), nullable=False),
        sa.Column(
            "account_ref",
            sa.String(length=160),
            sa.ForeignKey("identity.accounts.account_ref"),
            nullable=False,
        ),
        sa.Column("analysis_date", sa.Date(), nullable=False),
        sa.Column("case_count", sa.Integer(), nullable=False),
        sa.Column("owner_case_count", sa.Integer(), nullable=False),
        sa.Column("reference_case_count", sa.Integer(), nullable=False),
        sa.Column(
            "case_results_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column(
            "coverage_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column("run_hash", sa.String(length=64), nullable=False, unique=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint("case_count > 0", name="ck_mingli_corpus_case_count"),
        sa.CheckConstraint(
            "case_count = owner_case_count + reference_case_count",
            name="ck_mingli_corpus_subject_counts",
        ),
        schema="mingli",
    )
    op.create_index(
        "ix_mingli_corpus_qualification_account",
        "corpus_qualification_runs",
        ["account_ref", "analysis_date"],
        schema="mingli",
    )
    op.create_table(
        "grove_candidates",
        sa.Column("candidate_ref", sa.String(length=180), primary_key=True),
        sa.Column("pool_ref", sa.String(length=180), nullable=False),
        sa.Column(
            "question_ref",
            sa.String(length=180),
            sa.ForeignKey("story.question_instances.question_ref"),
            nullable=False,
        ),
        sa.Column(
            "actor_ref",
            sa.String(length=160),
            sa.ForeignKey("world.actors.actor_ref"),
            nullable=False,
        ),
        sa.Column(
            "tree_ref",
            sa.String(length=180),
            sa.ForeignKey("dream.life_trees.tree_ref"),
            nullable=False,
        ),
        sa.Column("domain", sa.String(length=40), nullable=False),
        sa.Column("public_alias", sa.String(length=120), nullable=False),
        sa.Column("premise", sa.Text(), nullable=False),
        sa.Column("display_order", sa.Integer(), nullable=False),
        sa.Column("runtime_status", sa.String(length=40), nullable=False),
        sa.Column(
            "candidate_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column("candidate_hash", sa.String(length=64), nullable=False, unique=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint(
            "pool_ref",
            "question_ref",
            name="uq_dream_grove_pool_question",
        ),
        sa.UniqueConstraint(
            "pool_ref",
            "display_order",
            name="uq_dream_grove_pool_order",
        ),
        sa.CheckConstraint(
            "domain IN ('career', 'wealth', 'relationship')",
            name="ck_dream_grove_domain",
        ),
        sa.CheckConstraint(
            "runtime_status IN ('ACTIVE', 'RETIRED')",
            name="ck_dream_grove_runtime_status",
        ),
        schema="dream",
    )
    op.create_index(
        "ix_dream_grove_candidate_pool",
        "grove_candidates",
        ["pool_ref", "runtime_status", "display_order"],
        schema="dream",
    )
    op.execute(
        sa.text(
            """
            CREATE FUNCTION mingli.reject_corpus_qualification_mutation()
            RETURNS trigger
            LANGUAGE plpgsql
            AS $$
            BEGIN
                RAISE EXCEPTION 'mingli_corpus_qualification_runs_are_append_only';
            END;
            $$;

            CREATE TRIGGER trg_mingli_corpus_qualification_append_only
            BEFORE UPDATE OR DELETE ON mingli.corpus_qualification_runs
            FOR EACH ROW
            EXECUTE FUNCTION mingli.reject_corpus_qualification_mutation();
            """
        )
    )
    op.execute(
        sa.text(
            """
            UPDATE platform.schema_manifest
            SET foundation_version = 'v60.foundation.012',
                manifest_json = manifest_json
                    || '{"schema_revision": "0020_three_life_qualification",
                         "mingli_corpus_qualification_version":
                             "v60.mingli-corpus-qualification.001",
                         "dream_grove_version":
                             "v60.dream-grove.001"}'::jsonb,
                updated_at = now()
            WHERE singleton_id = 1
            """
        )
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            """
            DROP TRIGGER IF EXISTS trg_mingli_corpus_qualification_append_only
                ON mingli.corpus_qualification_runs;
            DROP FUNCTION IF EXISTS mingli.reject_corpus_qualification_mutation();
            """
        )
    )
    op.drop_index(
        "ix_dream_grove_candidate_pool",
        table_name="grove_candidates",
        schema="dream",
    )
    op.drop_table("grove_candidates", schema="dream")
    op.drop_index(
        "ix_mingli_corpus_qualification_account",
        table_name="corpus_qualification_runs",
        schema="mingli",
    )
    op.drop_table("corpus_qualification_runs", schema="mingli")
    op.execute(
        sa.text(
            """
            UPDATE platform.schema_manifest
            SET foundation_version = 'v60.foundation.011',
                manifest_json = (
                    manifest_json
                    - 'mingli_corpus_qualification_version'
                    - 'dream_grove_version'
                ) || '{"schema_revision": "0019_mingli_life_domains"}'::jsonb,
                updated_at = now()
            WHERE singleton_id = 1
            """
        )
    )
