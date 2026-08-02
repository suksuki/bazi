"""Bind the first distilled Mingli method assets and domain gates.

Revision ID: 0031_mingli_method_distillation
Revises: 0030_mingli_agent_identity
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0031_mingli_method_distillation"
down_revision: str | None = "0030_mingli_agent_identity"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        sa.text(
            """
            UPDATE platform.schema_manifest
            SET foundation_version = 'v60.foundation.023',
                manifest_json = manifest_json
                    || '{"schema_revision":
                             "0031_mingli_method_distillation",
                         "mingli_agent_prompt_view_version":
                             "v60.mingli-agent-prompt-view.009",
                         "mingli_agent_adjudication_version":
                             "v60.mingli-agent-adjudication.005",
                         "mingli_agent_method_distillation_version":
                             "v60.mingli-agent-method-distillation.001",
                         "mingli_reading_claim_graph_version":
                             "v60.mingli-reading-claim-graph.010"}'::jsonb,
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
            SET foundation_version = 'v60.foundation.022',
                manifest_json = (manifest_json
                    || '{"schema_revision":
                             "0030_mingli_agent_identity",
                         "mingli_agent_prompt_view_version":
                             "v60.mingli-agent-prompt-view.008",
                         "mingli_agent_adjudication_version":
                             "v60.mingli-agent-adjudication.004",
                         "mingli_reading_claim_graph_version":
                             "v60.mingli-reading-claim-graph.009"}'::jsonb)
                    - 'mingli_agent_method_distillation_version',
                updated_at = now()
            WHERE singleton_id = 1
            """
        )
    )
