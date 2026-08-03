"""Register the multi-experiment Mingli root-identity matrix.

Revision ID: 0037_mingli_root_matrix
Revises: 0036_mingli_model_trace
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0037_mingli_root_matrix"
down_revision: str | None = "0036_mingli_model_trace"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        sa.text(
            """
            UPDATE platform.schema_manifest
            SET foundation_version = 'v60.foundation.029',
                manifest_json = manifest_json
                    || '{"schema_revision":
                             "0037_mingli_root_matrix",
                         "mingli_agent_runtime_version":
                             "v60.mingli-agent-runtime.024",
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


def downgrade() -> None:
    op.execute(
        sa.text(
            """
            UPDATE platform.schema_manifest
            SET foundation_version = 'v60.foundation.028',
                manifest_json = manifest_json
                    || '{"schema_revision":
                             "0036_mingli_model_trace",
                         "mingli_agent_runtime_version":
                             "v60.mingli-agent-runtime.022",
                         "mingli_synthetic_experiment_catalog_version":
                             "v60.mingli-synthetic-experiment-catalog.001",
                         "mingli_synthetic_experiment_evaluator_version":
                             "v60.mingli-synthetic-experiment-evaluator.001",
                         "mingli_synthetic_experiment_dev_gold_version":
                             "v60.mingli-synthetic-experiment-dev-gold.001",
                         "mingli_synthetic_experiment_snapshot_version":
                             "v60.mingli-synthetic-experiment-snapshot.002"}'::jsonb,
                updated_at = now()
            WHERE singleton_id = 1
            """
        )
    )
