"""Bind the minimum anti-follow effective-root method.

Revision ID: 0033_mingli_root_gate
Revises: 0032_mingli_synthetic_lab
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0033_mingli_root_gate"
down_revision: str | None = "0032_mingli_synthetic_lab"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        sa.text(
            """
            UPDATE platform.schema_manifest
            SET foundation_version = 'v60.foundation.025',
                manifest_json = manifest_json
                    || '{"schema_revision":
                             "0033_mingli_root_gate",
                         "mingli_agent_prompt_view_version":
                             "v60.mingli-agent-prompt-view.011",
                         "mingli_agent_runtime_version":
                             "v60.mingli-agent-runtime.019",
                         "mingli_agent_adjudication_version":
                             "v60.mingli-agent-adjudication.007",
                         "mingli_agent_method_distillation_version":
                             "v60.mingli-agent-method-distillation.003",
                         "mingli_effective_root_method_version":
                             "v60.mingli-effective-root-method.001"}'::jsonb,
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
            SET foundation_version = 'v60.foundation.024',
                manifest_json = (manifest_json
                    || '{"schema_revision":
                             "0032_mingli_synthetic_lab",
                         "mingli_agent_prompt_view_version":
                             "v60.mingli-agent-prompt-view.010",
                         "mingli_agent_runtime_version":
                             "v60.mingli-agent-runtime.018",
                         "mingli_agent_adjudication_version":
                             "v60.mingli-agent-adjudication.006",
                         "mingli_agent_method_distillation_version":
                             "v60.mingli-agent-method-distillation.002"}'::jsonb)
                    - 'mingli_effective_root_method_version',
                updated_at = now()
            WHERE singleton_id = 1
            """
        )
    )
