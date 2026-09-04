"""Add typed regime decisions and sealed synthetic Mingli Lab runs.

Revision ID: 0032_mingli_synthetic_lab
Revises: 0031_mingli_method_distillation
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0032_mingli_synthetic_lab"
down_revision: str | None = "0031_mingli_method_distillation"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "synthetic_experiment_runs",
        sa.Column("run_ref", sa.String(length=180), primary_key=True),
        sa.Column("run_version", sa.String(length=100), nullable=False),
        sa.Column("experiment_ref", sa.String(length=180), nullable=False),
        sa.Column("definition_hash", sa.String(length=64), nullable=False),
        sa.Column("evaluator_version", sa.String(length=100), nullable=False),
        sa.Column("analysis_date", sa.Date(), nullable=False),
        sa.Column(
            "member_a_agent_reading_ref",
            sa.String(length=180),
            sa.ForeignKey("mingli.agent_readings.agent_reading_ref"),
            nullable=False,
        ),
        sa.Column(
            "member_b_agent_reading_ref",
            sa.String(length=180),
            sa.ForeignKey("mingli.agent_readings.agent_reading_ref"),
            nullable=False,
        ),
        sa.Column(
            "member_a_stage_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column(
            "member_b_stage_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column("outcome", sa.String(length=60), nullable=False),
        sa.Column(
            "evaluation_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column("run_hash", sa.String(length=64), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint("run_hash", name="uq_mingli_synthetic_experiment_run_hash"),
        sa.CheckConstraint(
            "outcome IN ('PASS', 'PRODUCT_SAFE_MODEL_FAIL', 'MODEL_FAIL', 'INVALID_EXPERIMENT')",
            name="ck_mingli_synthetic_experiment_outcome",
        ),
        schema="mingli",
    )
    op.create_index(
        "ix_mingli_synthetic_experiment_created",
        "synthetic_experiment_runs",
        ["experiment_ref", "created_at"],
        schema="mingli",
    )
    op.execute(
        sa.text(
            """
            CREATE FUNCTION mingli.reject_synthetic_experiment_run_mutation()
            RETURNS trigger
            LANGUAGE plpgsql
            AS $$
            BEGIN
                RAISE EXCEPTION 'mingli_synthetic_experiment_runs_are_append_only';
            END;
            $$;

            CREATE TRIGGER trg_mingli_synthetic_experiment_runs_append_only
            BEFORE UPDATE OR DELETE ON mingli.synthetic_experiment_runs
            FOR EACH ROW EXECUTE FUNCTION
                mingli.reject_synthetic_experiment_run_mutation();
            """
        )
    )
    op.execute(
        sa.text(
            """
            UPDATE platform.schema_manifest
            SET foundation_version = 'v60.foundation.024',
                manifest_json = manifest_json
                    || '{"schema_revision": "0032_mingli_synthetic_lab",
                         "mingli_agent_prompt_view_version":
                             "v60.mingli-agent-prompt-view.010",
                         "mingli_agent_runtime_version":
                             "v60.mingli-agent-runtime.018",
                         "mingli_agent_packet_version":
                             "v60.mingli-agent-case-packet.003",
                         "mingli_agent_packet_compiler_version":
                             "v60.mingli-agent-packet-compiler.003",
                         "mingli_agent_reading_version":
                             "v60.mingli-agent-reading.004",
                         "mingli_agent_adjudication_version":
                             "v60.mingli-agent-adjudication.006",
                         "mingli_agent_method_distillation_version":
                             "v60.mingli-agent-method-distillation.002",
                         "mingli_agent_output_repair_version":
                             "v60.mingli-agent-output-repair.003",
                         "mingli_agent_regime_contract_version":
                             "v60.mingli-agent-regime-decision.001",
                         "mingli_stage_projection_version":
                             "v60.mingli-stage-projection.004",
                         "mingli_corpus_qualification_version":
                             "v60.mingli-corpus-qualification.002",
                         "mingli_case_materialization_version":
                             "v60.mingli-case-materialization.001",
                         "mingli_synthetic_experiment_catalog_version":
                             "v60.mingli-synthetic-experiment-catalog.001",
                         "mingli_synthetic_experiment_evaluator_version":
                             "v60.mingli-synthetic-experiment-evaluator.001",
                         "mingli_synthetic_experiment_dev_gold_version":
                             "v60.mingli-synthetic-experiment-dev-gold.001",
                         "mingli_synthetic_experiment_run_version":
                             "v60.mingli-synthetic-experiment-run.001",
                         "mingli_synthetic_experiment_snapshot_version":
                             "v60.mingli-synthetic-experiment-snapshot.001"}'::jsonb,
                updated_at = now()
            WHERE singleton_id = 1
            """
        )
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            """
            DROP TRIGGER IF EXISTS trg_mingli_synthetic_experiment_runs_append_only
                ON mingli.synthetic_experiment_runs;
            DROP FUNCTION IF EXISTS
                mingli.reject_synthetic_experiment_run_mutation();
            """
        )
    )
    op.drop_index(
        "ix_mingli_synthetic_experiment_created",
        table_name="synthetic_experiment_runs",
        schema="mingli",
    )
    op.drop_table("synthetic_experiment_runs", schema="mingli")
    op.execute(
        sa.text(
            """
            UPDATE platform.schema_manifest
            SET foundation_version = 'v60.foundation.023',
                manifest_json = ((manifest_json
                    || '{"schema_revision": "0031_mingli_method_distillation",
                         "mingli_agent_prompt_view_version":
                             "v60.mingli-agent-prompt-view.009",
                         "mingli_agent_packet_version":
                             "v60.mingli-agent-case-packet.002",
                         "mingli_agent_packet_compiler_version":
                             "v60.mingli-agent-packet-compiler.002",
                         "mingli_agent_reading_version":
                             "v60.mingli-agent-reading.003",
                         "mingli_agent_adjudication_version":
                             "v60.mingli-agent-adjudication.005",
                         "mingli_agent_method_distillation_version":
                             "v60.mingli-agent-method-distillation.001",
                         "mingli_agent_output_repair_version":
                             "v60.mingli-agent-output-repair.002"}'::jsonb)
                    - 'mingli_agent_regime_contract_version'
                    - 'mingli_agent_runtime_version'
                    - 'mingli_synthetic_experiment_catalog_version'
                    - 'mingli_synthetic_experiment_evaluator_version'
                    - 'mingli_synthetic_experiment_dev_gold_version'
                    - 'mingli_case_materialization_version'
                    - 'mingli_synthetic_experiment_run_version'
                    - 'mingli_synthetic_experiment_snapshot_version')
                    || '{"mingli_stage_projection_version":
                             "v60.mingli-stage-projection.002",
                         "mingli_corpus_qualification_version":
                             "v60.mingli-corpus-qualification.001"}'::jsonb,
                updated_at = now()
            WHERE singleton_id = 1
            """
        )
    )
