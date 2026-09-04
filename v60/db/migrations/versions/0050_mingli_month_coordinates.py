"""Bind month-command coordinate discipline to the Mingli research manifest.

Revision ID: 0050_mingli_month_coordinates
Revises: 0049_mingli_focused_passes
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0050_mingli_month_coordinates"
down_revision: str | None = "0049_mingli_focused_passes"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        sa.text(
            """
            UPDATE platform.schema_manifest
            SET foundation_version = 'v60.foundation.042',
                manifest_json = manifest_json
                    || '{"schema_revision":
                             "0050_mingli_month_coordinates",
                         "mingli_month_coordinate_discipline_version":
                             "v60.mingli-month-coordinate-discipline.001",
                         "mingli_synthetic_experiment_catalog_version":
                             "v60.mingli-synthetic-experiment-catalog.007",
                         "mingli_synthetic_experiment_evaluator_version":
                             "v60.mingli-synthetic-experiment-evaluator.009",
                         "mingli_synthetic_experiment_dev_gold_version":
                             "v60.mingli-synthetic-experiment-dev-gold.006",
                         "mingli_synthetic_suite_catalog_version":
                             "v60.mingli-synthetic-suite-catalog.005"}'::jsonb,
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
            SET foundation_version = 'v60.foundation.041',
                manifest_json = (manifest_json
                    - 'mingli_month_coordinate_discipline_version')
                    || '{"schema_revision":
                             "0049_mingli_focused_passes",
                         "mingli_synthetic_experiment_catalog_version":
                             "v60.mingli-synthetic-experiment-catalog.006",
                         "mingli_synthetic_experiment_evaluator_version":
                             "v60.mingli-synthetic-experiment-evaluator.008",
                         "mingli_synthetic_experiment_dev_gold_version":
                             "v60.mingli-synthetic-experiment-dev-gold.005",
                         "mingli_synthetic_suite_catalog_version":
                             "v60.mingli-synthetic-suite-catalog.004"}'::jsonb,
                updated_at = now()
            WHERE singleton_id = 1
            """
        )
    )
