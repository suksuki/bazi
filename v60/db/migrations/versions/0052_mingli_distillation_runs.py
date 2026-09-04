"""Add append-only three-pass synthetic distillation runs.

Revision ID: 0052_mingli_distillation_runs
Revises: 0051_mingli_raw_judgment
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0052_mingli_distillation_runs"
down_revision: str | None = "0051_mingli_raw_judgment"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "synthetic_distillation_runs",
        sa.Column("run_ref", sa.String(length=180), nullable=False),
        sa.Column("run_version", sa.String(length=100), nullable=False),
        sa.Column("generation_key", sa.String(length=64), nullable=False),
        sa.Column("experiment_ref", sa.String(length=180), nullable=False),
        sa.Column("definition_hash", sa.String(length=64), nullable=False),
        sa.Column("variant", sa.String(length=1), nullable=False),
        sa.Column("case_ref", sa.String(length=160), nullable=False),
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
        sa.Column("outcome", sa.String(length=60), nullable=False),
        sa.Column("model_independence", sa.String(length=40), nullable=False),
        sa.Column("run_json", postgresql.JSONB(), nullable=False),
        sa.Column("run_hash", sa.String(length=64), nullable=False),
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
        sa.CheckConstraint("variant IN ('A', 'B')"),
        sa.PrimaryKeyConstraint("run_ref"),
        sa.UniqueConstraint("generation_key"),
        sa.UniqueConstraint("run_hash"),
        schema="mingli",
    )
    op.create_index(
        "ix_mingli_synthetic_distillation_runs_history",
        "synthetic_distillation_runs",
        ["experiment_ref", "variant", "created_at"],
        unique=False,
        schema="mingli",
    )
    op.execute(
        sa.text(
            """
            CREATE FUNCTION mingli.reject_synthetic_distillation_run_mutation()
            RETURNS trigger
            LANGUAGE plpgsql
            AS $$
            BEGIN
                RAISE EXCEPTION 'mingli_synthetic_distillation_runs_are_append_only';
            END;
            $$;

            CREATE TRIGGER trg_mingli_synthetic_distillation_runs_append_only
            BEFORE UPDATE OR DELETE ON mingli.synthetic_distillation_runs
            FOR EACH ROW
            EXECUTE FUNCTION mingli.reject_synthetic_distillation_run_mutation();
            """
        )
    )
    op.execute(
        sa.text(
            """
            UPDATE platform.schema_manifest
            SET foundation_version = 'v60.foundation.044',
                manifest_json = manifest_json
                    || '{"schema_revision":
                             "0052_mingli_distillation_runs",
                         "mingli_synthetic_distillation_runtime_version":
                             "v60.mingli-synthetic-distillation-runtime.001",
                         "mingli_synthetic_distillation_prompt_version":
                             "v60.prompt.mingli-synthetic-distillation.001",
                         "mingli_synthetic_distillation_pass_version":
                             "v60.mingli-synthetic-distillation-pass.001",
                         "mingli_synthetic_distillation_evaluator_version":
                             "v60.mingli-synthetic-distillation-evaluator.001",
                         "mingli_synthetic_distillation_run_version":
                             "v60.mingli-synthetic-distillation-run.001",
                         "mingli_synthetic_distillation_provider_profile_ref":
                             "v60.model-serving.qwen38-27b-mingli-distillation.001"}'::jsonb,
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
                trg_mingli_synthetic_distillation_runs_append_only
                ON mingli.synthetic_distillation_runs;
            DROP FUNCTION IF EXISTS
                mingli.reject_synthetic_distillation_run_mutation();
            """
        )
    )
    op.drop_index(
        "ix_mingli_synthetic_distillation_runs_history",
        table_name="synthetic_distillation_runs",
        schema="mingli",
    )
    op.drop_table("synthetic_distillation_runs", schema="mingli")
    op.execute(
        sa.text(
            """
            UPDATE platform.schema_manifest
            SET foundation_version = 'v60.foundation.043',
                manifest_json = (manifest_json
                    - 'mingli_synthetic_distillation_runtime_version'
                    - 'mingli_synthetic_distillation_prompt_version'
                    - 'mingli_synthetic_distillation_pass_version'
                    - 'mingli_synthetic_distillation_evaluator_version'
                    - 'mingli_synthetic_distillation_run_version'
                    - 'mingli_synthetic_distillation_provider_profile_ref')
                    || '{"schema_revision":
                             "0051_mingli_raw_judgment"}'::jsonb,
                updated_at = now()
            WHERE singleton_id = 1
            """
        )
    )
