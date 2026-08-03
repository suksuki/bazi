"""Bind legal decision rows after the first raw-model comparison.

Revision ID: 0044_mingli_legal_decision_rows
Revises: 0043_mingli_decision_discipline
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0044_mingli_legal_decision_rows"
down_revision: str | None = "0043_mingli_decision_discipline"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        sa.text(
            """
            UPDATE platform.schema_manifest
            SET foundation_version = 'v60.foundation.036',
                manifest_json = manifest_json
                    || '{"schema_revision":
                             "0044_mingli_legal_decision_rows",
                         "mingli_agent_runtime_version":
                             "v60.mingli-agent-runtime.031",
                         "mingli_agent_prompt_view_version":
                             "v60.mingli-agent-prompt-view.017",
                         "mingli_agent_reading_version":
                             "v60.mingli-agent-reading.006",
                         "mingli_agent_adjudication_version":
                             "v60.mingli-agent-adjudication.010",
                         "mingli_agent_output_repair_version":
                             "v60.mingli-agent-output-repair.004",
                         "mingli_agent_method_distillation_version":
                             "v60.mingli-agent-method-distillation.006",
                         "mingli_agent_regime_contract_version":
                             "v60.mingli-agent-regime-decision.002",
                         "mingli_synthetic_experiment_catalog_version":
                             "v60.mingli-synthetic-experiment-catalog.006",
                         "mingli_synthetic_experiment_evaluator_version":
                             "v60.mingli-synthetic-experiment-evaluator.007",
                         "mingli_synthetic_experiment_dev_gold_version":
                             "v60.mingli-synthetic-experiment-dev-gold.005",
                         "mingli_synthetic_suite_catalog_version":
                             "v60.mingli-synthetic-suite-catalog.004"}'::jsonb,
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
            SET foundation_version = 'v60.foundation.035',
                manifest_json = manifest_json
                    || '{"schema_revision":
                             "0043_mingli_decision_discipline",
                         "mingli_agent_runtime_version":
                             "v60.mingli-agent-runtime.030",
                         "mingli_agent_prompt_view_version":
                             "v60.mingli-agent-prompt-view.016",
                         "mingli_agent_reading_version":
                             "v60.mingli-agent-reading.006",
                         "mingli_agent_adjudication_version":
                             "v60.mingli-agent-adjudication.010",
                         "mingli_agent_output_repair_version":
                             "v60.mingli-agent-output-repair.004",
                         "mingli_agent_method_distillation_version":
                             "v60.mingli-agent-method-distillation.006",
                         "mingli_agent_regime_contract_version":
                             "v60.mingli-agent-regime-decision.002",
                         "mingli_synthetic_experiment_catalog_version":
                             "v60.mingli-synthetic-experiment-catalog.006",
                         "mingli_synthetic_experiment_evaluator_version":
                             "v60.mingli-synthetic-experiment-evaluator.007",
                         "mingli_synthetic_experiment_dev_gold_version":
                             "v60.mingli-synthetic-experiment-dev-gold.005",
                         "mingli_synthetic_suite_catalog_version":
                             "v60.mingli-synthetic-suite-catalog.004"}'::jsonb,
                updated_at = now()
            WHERE singleton_id = 1
            """
        )
    )
