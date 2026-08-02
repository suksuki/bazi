"""Bind the primary-root prose fact guard.

Revision ID: 0034_mingli_root_rank_guard
Revises: 0033_mingli_root_gate
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0034_mingli_root_rank_guard"
down_revision: str | None = "0033_mingli_root_gate"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        sa.text(
            """
            UPDATE platform.schema_manifest
            SET foundation_version = 'v60.foundation.026',
                manifest_json = manifest_json
                    || '{"schema_revision":
                             "0034_mingli_root_rank_guard",
                         "mingli_agent_runtime_version":
                             "v60.mingli-agent-runtime.020",
                         "mingli_agent_adjudication_version":
                             "v60.mingli-agent-adjudication.008"}'::jsonb,
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
            SET foundation_version = 'v60.foundation.025',
                manifest_json = manifest_json
                    || '{"schema_revision": "0033_mingli_root_gate",
                         "mingli_agent_runtime_version":
                             "v60.mingli-agent-runtime.019",
                         "mingli_agent_adjudication_version":
                             "v60.mingli-agent-adjudication.007"}'::jsonb,
                updated_at = now()
            WHERE singleton_id = 1
            """
        )
    )
