"""Preserve Mingli Agent hypothesis identity during adjudication normalization.

Revision ID: 0030_mingli_agent_identity
Revises: 0029_mingli_agent_adjudication
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0030_mingli_agent_identity"
down_revision: str | None = "0029_mingli_agent_adjudication"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        sa.text(
            """
            UPDATE platform.schema_manifest
            SET foundation_version = 'v60.foundation.022',
                manifest_json = manifest_json
                    || '{"schema_revision":
                             "0030_mingli_agent_identity",
                         "mingli_agent_adjudication_version":
                             "v60.mingli-agent-adjudication.004",
                         "mingli_agent_output_repair_version":
                             "v60.mingli-agent-output-repair.002"}'::jsonb,
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
            SET foundation_version = 'v60.foundation.021',
                manifest_json = manifest_json
                    || '{"schema_revision":
                             "0029_mingli_agent_adjudication",
                         "mingli_agent_adjudication_version":
                             "v60.mingli-agent-adjudication.003",
                         "mingli_agent_output_repair_version":
                             "v60.mingli-agent-output-repair.001"}'::jsonb,
                updated_at = now()
            WHERE singleton_id = 1
            """
        )
    )
