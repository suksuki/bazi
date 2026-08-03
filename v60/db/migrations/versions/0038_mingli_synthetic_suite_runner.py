"""Add the append-only synthetic Mingli DEV Suite runner ledger.

Revision ID: 0038_mingli_suite_runner
Revises: 0037_mingli_root_matrix
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0038_mingli_suite_runner"
down_revision: str | None = "0037_mingli_root_matrix"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "synthetic_suite_runs",
        sa.Column("suite_run_ref", sa.String(length=180), primary_key=True),
        sa.Column("suite_run_version", sa.String(length=100), nullable=False),
        sa.Column("suite_ref", sa.String(length=180), nullable=False),
        sa.Column("suite_definition_hash", sa.String(length=64), nullable=False),
        sa.Column("suite_mode", sa.String(length=40), nullable=False),
        sa.Column("runner_version", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=60), nullable=False),
        sa.Column("experiment_count", sa.Integer(), nullable=False),
        sa.Column("sealed_count", sa.Integer(), nullable=False),
        sa.Column("error_count", sa.Integer(), nullable=False),
        sa.Column("review_required_count", sa.Integer(), nullable=False),
        sa.Column(
            "run_json",
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
        sa.UniqueConstraint(
            "run_hash",
            name="uq_mingli_synthetic_suite_run_hash",
        ),
        sa.CheckConstraint(
            "suite_mode IN ('DEV', 'QUALIFICATION', 'HOLDOUT')",
            name="ck_mingli_synthetic_suite_mode",
        ),
        sa.CheckConstraint(
            "status IN ('COMPLETED', 'COMPLETED_WITH_ERRORS')",
            name="ck_mingli_synthetic_suite_status",
        ),
        sa.CheckConstraint(
            "experiment_count > 0 AND sealed_count >= 0 AND error_count >= 0 "
            "AND review_required_count >= 0 "
            "AND sealed_count + error_count = experiment_count "
            "AND review_required_count <= experiment_count",
            name="ck_mingli_synthetic_suite_counts",
        ),
        sa.CheckConstraint(
            "(status = 'COMPLETED' AND error_count = 0) OR "
            "(status = 'COMPLETED_WITH_ERRORS' AND error_count > 0)",
            name="ck_mingli_synthetic_suite_status_error_count",
        ),
        schema="mingli",
    )
    op.create_index(
        "ix_mingli_synthetic_suite_created",
        "synthetic_suite_runs",
        ["suite_ref", "created_at"],
        schema="mingli",
    )
    op.execute(
        sa.text(
            """
            CREATE FUNCTION mingli.reject_synthetic_suite_run_mutation()
            RETURNS trigger
            LANGUAGE plpgsql
            AS $$
            BEGIN
                RAISE EXCEPTION 'mingli_synthetic_suite_runs_are_append_only';
            END;
            $$;

            CREATE TRIGGER trg_mingli_synthetic_suite_runs_append_only
            BEFORE UPDATE OR DELETE ON mingli.synthetic_suite_runs
            FOR EACH ROW EXECUTE FUNCTION
                mingli.reject_synthetic_suite_run_mutation();
            """
        )
    )
    op.execute(
        sa.text(
            """
            UPDATE platform.schema_manifest
            SET foundation_version = 'v60.foundation.030',
                manifest_json = manifest_json
                    || '{"schema_revision":
                             "0038_mingli_suite_runner",
                         "mingli_synthetic_experiment_catalog_version":
                             "v60.mingli-synthetic-experiment-catalog.003",
                         "mingli_synthetic_experiment_evaluator_version":
                             "v60.mingli-synthetic-experiment-evaluator.004",
                         "mingli_synthetic_experiment_dev_gold_version":
                             "v60.mingli-synthetic-experiment-dev-gold.004",
                         "mingli_synthetic_experiment_snapshot_version":
                             "v60.mingli-synthetic-experiment-snapshot.004",
                         "mingli_synthetic_suite_catalog_version":
                             "v60.mingli-synthetic-suite-catalog.001",
                         "mingli_synthetic_suite_runner_version":
                             "v60.mingli-synthetic-suite-runner.001",
                         "mingli_synthetic_suite_run_version":
                             "v60.mingli-synthetic-suite-run.001"}'::jsonb,
                updated_at = now()
            WHERE singleton_id = 1
            """
        )
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            """
            DROP TRIGGER IF EXISTS trg_mingli_synthetic_suite_runs_append_only
                ON mingli.synthetic_suite_runs;
            DROP FUNCTION IF EXISTS mingli.reject_synthetic_suite_run_mutation();
            """
        )
    )
    op.drop_index(
        "ix_mingli_synthetic_suite_created",
        table_name="synthetic_suite_runs",
        schema="mingli",
    )
    op.drop_table("synthetic_suite_runs", schema="mingli")
    op.execute(
        sa.text(
            """
            UPDATE platform.schema_manifest
            SET foundation_version = 'v60.foundation.029',
                manifest_json = (manifest_json
                    - 'mingli_synthetic_suite_catalog_version'
                    - 'mingli_synthetic_suite_runner_version'
                    - 'mingli_synthetic_suite_run_version')
                    || '{"schema_revision":
                             "0037_mingli_root_matrix",
                         "mingli_synthetic_experiment_catalog_version":
                             "v60.mingli-synthetic-experiment-catalog.002",
                         "mingli_synthetic_experiment_evaluator_version":
                             "v60.mingli-synthetic-experiment-evaluator.003",
                         "mingli_synthetic_experiment_dev_gold_version":
                             "v60.mingli-synthetic-experiment-dev-gold.003",
                         "mingli_synthetic_experiment_snapshot_version":
                             "v60.mingli-synthetic-experiment-snapshot.003"}'::jsonb,
                updated_at = now()
            WHERE singleton_id = 1
            """
        )
    )
