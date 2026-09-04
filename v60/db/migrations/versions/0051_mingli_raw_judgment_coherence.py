"""Bind raw hypothesis judgment coherence to the Mingli evaluator manifest.

Revision ID: 0051_mingli_raw_judgment
Revises: 0050_mingli_month_coordinates
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0051_mingli_raw_judgment"
down_revision: str | None = "0050_mingli_month_coordinates"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        sa.text(
            """
            UPDATE platform.schema_manifest
            SET foundation_version = 'v60.foundation.043',
                manifest_json = manifest_json
                    || '{"schema_revision":
                             "0051_mingli_raw_judgment",
                         "mingli_raw_judgment_coherence_version":
                             "v60.mingli-raw-judgment-coherence.001",
                         "mingli_synthetic_experiment_evaluator_version":
                             "v60.mingli-synthetic-experiment-evaluator.010"}'::jsonb,
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
            SET foundation_version = 'v60.foundation.042',
                manifest_json = (manifest_json
                    - 'mingli_raw_judgment_coherence_version')
                    || '{"schema_revision":
                             "0050_mingli_month_coordinates",
                         "mingli_synthetic_experiment_evaluator_version":
                             "v60.mingli-synthetic-experiment-evaluator.009"}'::jsonb,
                updated_at = now()
            WHERE singleton_id = 1
            """
        )
    )
