"""Bind provider provenance into Mingli narration v2 identities.

Revision ID: 0027_mingli_narration_v2
Revises: 0026_mingli_narration_assets
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0027_mingli_narration_v2"
down_revision: str | None = "0026_mingli_narration_assets"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        sa.text(
            """
            UPDATE platform.schema_manifest
            SET foundation_version = 'v60.foundation.019',
                manifest_json = manifest_json
                    || '{"schema_revision":
                             "0027_mingli_narration_v2",
                         "mingli_stage_projection_version":
                             "v60.mingli-stage-projection.002",
                         "mingli_timing_vector_version":
                             "v60.mingli-timing-evidence-vector.002",
                         "mingli_narration_version":
                             "v60.mingli-narration.002"}'::jsonb,
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
            SET foundation_version = 'v60.foundation.018',
                manifest_json = manifest_json
                    || '{"schema_revision": "0026_mingli_narration_assets",
                         "mingli_stage_projection_version":
                             "v60.mingli-stage-projection.001",
                         "mingli_timing_vector_version":
                             "v60.mingli-timing-evidence-vector.001",
                         "mingli_narration_version":
                             "v60.mingli-narration.001"}'::jsonb,
                updated_at = now()
            WHERE singleton_id = 1
            """
        )
    )
