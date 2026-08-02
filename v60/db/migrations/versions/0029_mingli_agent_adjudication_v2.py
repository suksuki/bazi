"""Bind executable Mingli adjudication contracts into the schema manifest.

Revision ID: 0029_mingli_agent_adjudication
Revises: 0028_mingli_agent_readings
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0029_mingli_agent_adjudication"
down_revision: str | None = "0028_mingli_agent_readings"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        sa.text(
            """
            UPDATE platform.schema_manifest
            SET foundation_version = 'v60.foundation.021',
                manifest_json = manifest_json
                    || '{"schema_revision":
                             "0029_mingli_agent_adjudication",
                         "mingli_agent_packet_version":
                             "v60.mingli-agent-case-packet.002",
                         "mingli_agent_prompt_view_version":
                             "v60.mingli-agent-prompt-view.008",
                         "mingli_agent_reading_version":
                             "v60.mingli-agent-reading.003",
                         "mingli_agent_adjudication_version":
                             "v60.mingli-agent-adjudication.003",
                         "mingli_agent_output_repair_version":
                             "v60.mingli-agent-output-repair.001",
                         "mingli_reading_claim_graph_version":
                             "v60.mingli-reading-claim-graph.009",
                         "mingli_reading_summary_version":
                             "v60.mingli-reading-summary.006"}'::jsonb,
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
            SET foundation_version = 'v60.foundation.020',
                manifest_json = (manifest_json
                    || '{"schema_revision": "0028_mingli_agent_readings",
                         "mingli_agent_packet_version":
                             "v60.mingli-agent-case-packet.001",
                         "mingli_agent_reading_version":
                             "v60.mingli-agent-reading.001"}'::jsonb)
                    - 'mingli_agent_prompt_view_version'
                    - 'mingli_agent_adjudication_version'
                    - 'mingli_agent_output_repair_version'
                    - 'mingli_reading_claim_graph_version'
                    - 'mingli_reading_summary_version',
                updated_at = now()
            WHERE singleton_id = 1
            """
        )
    )
