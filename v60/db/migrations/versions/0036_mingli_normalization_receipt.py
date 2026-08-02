"""Register append-only Mingli model normalization receipts.

Revision ID: 0036_mingli_model_trace
Revises: 0035_mingli_uncertain_root_guard
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0036_mingli_model_trace"
down_revision: str | None = "0035_mingli_uncertain_root_guard"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
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
                         "mingli_agent_reading_version":
                             "v60.mingli-agent-reading.005",
                         "mingli_agent_normalization_receipt_version":
                             "v60.mingli-agent-normalization-receipt.001",
                         "mingli_synthetic_experiment_snapshot_version":
                             "v60.mingli-synthetic-experiment-snapshot.002"}'::jsonb,
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
            SET foundation_version = 'v60.foundation.027',
                manifest_json = (manifest_json
                    || '{"schema_revision":
                             "0035_mingli_uncertain_root_guard",
                         "mingli_agent_runtime_version":
                             "v60.mingli-agent-runtime.021",
                         "mingli_agent_reading_version":
                             "v60.mingli-agent-reading.004",
                         "mingli_synthetic_experiment_snapshot_version":
                             "v60.mingli-synthetic-experiment-snapshot.001"}'::jsonb)
                    - 'mingli_agent_normalization_receipt_version',
                updated_at = now()
            WHERE singleton_id = 1
            """
        )
    )
