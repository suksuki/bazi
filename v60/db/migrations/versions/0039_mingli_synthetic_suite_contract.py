"""Tighten candidate-bound synthetic Suite review contracts.

Revision ID: 0039_mingli_suite_contract
Revises: 0038_mingli_suite_runner
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0039_mingli_suite_contract"
down_revision: str | None = "0038_mingli_suite_runner"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        sa.text(
            """
            UPDATE platform.schema_manifest
            SET foundation_version = 'v60.foundation.031',
                manifest_json = manifest_json
                    || '{"schema_revision":
                             "0039_mingli_suite_contract",
                         "mingli_agent_runtime_version":
                             "v60.mingli-agent-runtime.025",
                         "mingli_synthetic_experiment_evaluator_version":
                             "v60.mingli-synthetic-experiment-evaluator.005",
                         "mingli_synthetic_suite_runner_version":
                             "v60.mingli-synthetic-suite-runner.002",
                         "mingli_synthetic_suite_run_version":
                             "v60.mingli-synthetic-suite-run.002"}'::jsonb,
                updated_at = now()
            WHERE singleton_id = 1
            """
        )
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            """
            UPDATE platform.schema_manifest
            SET foundation_version = 'v60.foundation.030',
                manifest_json = manifest_json
                    || '{"schema_revision":
                             "0038_mingli_suite_runner",
                         "mingli_agent_runtime_version":
                             "v60.mingli-agent-runtime.024",
                         "mingli_synthetic_experiment_evaluator_version":
                             "v60.mingli-synthetic-experiment-evaluator.004",
                         "mingli_synthetic_suite_runner_version":
                             "v60.mingli-synthetic-suite-runner.001",
                         "mingli_synthetic_suite_run_version":
                             "v60.mingli-synthetic-suite-run.001"}'::jsonb,
                updated_at = now()
            WHERE singleton_id = 1
            """
        )
    )
