"""Bind model-complete regime and synthetic prose review contracts.

Revision ID: 0040_mingli_model_field_contract
Revises: 0039_mingli_suite_contract
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0040_mingli_model_field_contract"
down_revision: str | None = "0039_mingli_suite_contract"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        sa.text(
            """
            UPDATE platform.schema_manifest
            SET foundation_version = 'v60.foundation.032',
                manifest_json = manifest_json
                    || '{"schema_revision":
                             "0040_mingli_model_field_contract",
                         "mingli_agent_runtime_version":
                             "v60.mingli-agent-runtime.028",
                         "mingli_agent_prompt_view_version":
                             "v60.mingli-agent-prompt-view.014",
                         "mingli_agent_method_distillation_version":
                             "v60.mingli-agent-method-distillation.004",
                         "mingli_synthetic_experiment_evaluator_version":
                             "v60.mingli-synthetic-experiment-evaluator.006"}'::jsonb,
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
            SET foundation_version = 'v60.foundation.031',
                manifest_json = manifest_json
                    || '{"schema_revision":
                             "0039_mingli_suite_contract",
                         "mingli_agent_runtime_version":
                             "v60.mingli-agent-runtime.025",
                         "mingli_agent_prompt_view_version":
                             "v60.mingli-agent-prompt-view.011",
                         "mingli_agent_method_distillation_version":
                             "v60.mingli-agent-method-distillation.003",
                         "mingli_synthetic_experiment_evaluator_version":
                             "v60.mingli-synthetic-experiment-evaluator.005"}'::jsonb,
                updated_at = now()
            WHERE singleton_id = 1
            """
        )
    )
