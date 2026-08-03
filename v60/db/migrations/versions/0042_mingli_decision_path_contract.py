"""Bind whole-chart decision and primary work-path contracts.

Revision ID: 0042_mingli_decision_path
Revises: 0041_mingli_training_requests
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0042_mingli_decision_path"
down_revision: str | None = "0041_mingli_training_requests"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        sa.text(
            """
            UPDATE platform.schema_manifest
            SET foundation_version = 'v60.foundation.034',
                manifest_json = manifest_json
                    || '{"schema_revision":
                             "0042_mingli_decision_path",
                         "mingli_agent_runtime_version":
                             "v60.mingli-agent-runtime.029",
                         "mingli_agent_prompt_view_version":
                             "v60.mingli-agent-prompt-view.015",
                         "mingli_agent_reading_version":
                             "v60.mingli-agent-reading.006",
                         "mingli_agent_adjudication_version":
                             "v60.mingli-agent-adjudication.010",
                         "mingli_agent_output_repair_version":
                             "v60.mingli-agent-output-repair.004",
                         "mingli_agent_method_distillation_version":
                             "v60.mingli-agent-method-distillation.005",
                         "mingli_agent_regime_contract_version":
                             "v60.mingli-agent-regime-decision.002",
                         "mingli_synthetic_experiment_catalog_version":
                             "v60.mingli-synthetic-experiment-catalog.005",
                         "mingli_synthetic_experiment_evaluator_version":
                             "v60.mingli-synthetic-experiment-evaluator.007",
                         "mingli_synthetic_experiment_dev_gold_version":
                             "v60.mingli-synthetic-experiment-dev-gold.005",
                         "mingli_synthetic_suite_catalog_version":
                             "v60.mingli-synthetic-suite-catalog.003"}'::jsonb,
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
            SET foundation_version = 'v60.foundation.033',
                manifest_json = manifest_json
                    || '{"schema_revision":
                             "0041_mingli_training_requests",
                         "mingli_agent_runtime_version":
                             "v60.mingli-agent-runtime.028",
                         "mingli_agent_prompt_view_version":
                             "v60.mingli-agent-prompt-view.014",
                         "mingli_agent_reading_version":
                             "v60.mingli-agent-reading.005",
                         "mingli_agent_adjudication_version":
                             "v60.mingli-agent-adjudication.009",
                         "mingli_agent_output_repair_version":
                             "v60.mingli-agent-output-repair.003",
                         "mingli_agent_method_distillation_version":
                             "v60.mingli-agent-method-distillation.004",
                         "mingli_agent_regime_contract_version":
                             "v60.mingli-agent-regime-decision.001",
                         "mingli_synthetic_experiment_catalog_version":
                             "v60.mingli-synthetic-experiment-catalog.004",
                         "mingli_synthetic_experiment_evaluator_version":
                             "v60.mingli-synthetic-experiment-evaluator.006",
                         "mingli_synthetic_experiment_dev_gold_version":
                             "v60.mingli-synthetic-experiment-dev-gold.004",
                         "mingli_synthetic_suite_catalog_version":
                             "v60.mingli-synthetic-suite-catalog.002"}'::jsonb,
                updated_at = now()
            WHERE singleton_id = 1
            """
        )
    )
