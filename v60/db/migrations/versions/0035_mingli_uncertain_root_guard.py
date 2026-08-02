"""Keep minimum anti-follow roots from deciding an uncertain strength state.

Revision ID: 0035_mingli_uncertain_root_guard
Revises: 0034_mingli_root_rank_guard
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0035_mingli_uncertain_root_guard"
down_revision: str | None = "0034_mingli_root_rank_guard"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        sa.text(
            """
            UPDATE platform.schema_manifest
            SET foundation_version = 'v60.foundation.027',
                manifest_json = manifest_json
                    || '{"schema_revision":
                             "0035_mingli_uncertain_root_guard",
                         "mingli_agent_runtime_version":
                             "v60.mingli-agent-runtime.021",
                         "mingli_agent_adjudication_version":
                             "v60.mingli-agent-adjudication.009"}'::jsonb,
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
            SET foundation_version = 'v60.foundation.026',
                manifest_json = manifest_json
                    || '{"schema_revision": "0034_mingli_root_rank_guard",
                         "mingli_agent_runtime_version":
                             "v60.mingli-agent-runtime.020",
                         "mingli_agent_adjudication_version":
                             "v60.mingli-agent-adjudication.008"}'::jsonb,
                updated_at = now()
            WHERE singleton_id = 1
            """
        )
    )
