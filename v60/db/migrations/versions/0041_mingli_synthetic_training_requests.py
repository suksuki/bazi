"""Add recoverable server-side synthetic Suite run requests.

Revision ID: 0041_mingli_training_requests
Revises: 0040_mingli_model_field_contract
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0041_mingli_training_requests"
down_revision: str | None = "0040_mingli_model_field_contract"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "synthetic_suite_run_requests",
        sa.Column("request_ref", sa.String(length=180), primary_key=True),
        sa.Column("request_version", sa.String(length=100), nullable=False),
        sa.Column("requester_account_ref", sa.String(length=160), nullable=False),
        sa.Column("suite_ref", sa.String(length=180), nullable=False),
        sa.Column("suite_definition_hash", sa.String(length=64), nullable=False),
        sa.Column(
            "candidate_identity_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column("candidate_identity_hash", sa.String(length=64), nullable=False),
        sa.Column("execution_fingerprint", sa.String(length=64), nullable=False),
        sa.Column("idempotency_key", sa.String(length=180), nullable=False),
        sa.Column("request_hash", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("progress_event", sa.String(length=40), nullable=False),
        sa.Column("current_position", sa.Integer(), nullable=False),
        sa.Column("completed_count", sa.Integer(), nullable=False),
        sa.Column("total_count", sa.Integer(), nullable=False),
        sa.Column("current_experiment_ref", sa.String(length=180), nullable=True),
        sa.Column("suite_run_ref", sa.String(length=180), nullable=True),
        sa.Column("suite_run_hash", sa.String(length=64), nullable=True),
        sa.Column("review_disposition", sa.String(length=80), nullable=True),
        sa.Column("error_code", sa.String(length=160), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint(
            "requester_account_ref",
            "idempotency_key",
            name="uq_mingli_synthetic_suite_request_idempotency",
        ),
        sa.UniqueConstraint(
            "request_hash",
            name="uq_mingli_synthetic_suite_request_hash",
        ),
        sa.CheckConstraint(
            "status IN ('QUEUED', 'RUNNING', 'SEALING', 'SUCCEEDED', 'FAILED')",
            name="ck_mingli_synthetic_suite_request_status",
        ),
        sa.CheckConstraint(
            "progress_event IN "
            "('QUEUED', 'START', 'SEALED', 'ERROR', 'SEALING', 'SUCCEEDED', 'FAILED')",
            name="ck_mingli_synthetic_suite_request_progress_event",
        ),
        sa.CheckConstraint(
            "total_count > 0 AND current_position >= 0 "
            "AND current_position <= total_count "
            "AND completed_count >= 0 AND completed_count <= total_count",
            name="ck_mingli_synthetic_suite_request_counts",
        ),
        sa.CheckConstraint(
            "(status = 'SUCCEEDED' AND suite_run_ref IS NOT NULL "
            "AND suite_run_hash IS NOT NULL AND review_disposition IS NOT NULL "
            "AND error_code IS NULL) OR "
            "(status = 'FAILED' AND suite_run_ref IS NULL "
            "AND suite_run_hash IS NULL AND review_disposition IS NULL "
            "AND error_code IS NOT NULL) OR "
            "(status IN ('QUEUED', 'RUNNING', 'SEALING') "
            "AND suite_run_ref IS NULL AND suite_run_hash IS NULL "
            "AND review_disposition IS NULL AND error_code IS NULL)",
            name="ck_mingli_synthetic_suite_request_terminal_result",
        ),
        sa.CheckConstraint(
            "review_disposition IS NULL OR review_disposition IN "
            "('MODEL_INDEPENDENT_DEV', 'CANDIDATE_REVISION_REQUIRED', "
            "'EXPERIMENT_REVISION_REQUIRED', 'EXECUTION_REPAIR_REQUIRED')",
            name="ck_mingli_synthetic_suite_request_disposition",
        ),
        schema="mingli",
    )
    op.create_index(
        "ix_mingli_synthetic_suite_request_latest",
        "synthetic_suite_run_requests",
        ["requester_account_ref", "updated_at"],
        schema="mingli",
    )
    op.create_index(
        "ix_mingli_synthetic_suite_request_status",
        "synthetic_suite_run_requests",
        ["status", "created_at"],
        schema="mingli",
    )
    op.execute(
        sa.text(
            """
            UPDATE platform.schema_manifest
            SET foundation_version = 'v60.foundation.033',
                manifest_json = manifest_json
                    || '{"schema_revision":
                             "0041_mingli_training_requests",
                         "mingli_synthetic_suite_run_request_version":
                             "v60.mingli-synthetic-suite-run-request.001",
                         "mingli_synthetic_training_status_version":
                             "v60.mingli-synthetic-training-status.001",
                         "mingli_synthetic_experiment_catalog_version":
                             "v60.mingli-synthetic-experiment-catalog.004",
                         "mingli_synthetic_suite_catalog_version":
                             "v60.mingli-synthetic-suite-catalog.002"}'::jsonb,
                updated_at = now()
            WHERE singleton_id = 1
            """
        )
    )


def downgrade() -> None:
    op.drop_index(
        "ix_mingli_synthetic_suite_request_status",
        table_name="synthetic_suite_run_requests",
        schema="mingli",
    )
    op.drop_index(
        "ix_mingli_synthetic_suite_request_latest",
        table_name="synthetic_suite_run_requests",
        schema="mingli",
    )
    op.drop_table("synthetic_suite_run_requests", schema="mingli")
    op.execute(
        sa.text(
            """
            UPDATE platform.schema_manifest
            SET foundation_version = 'v60.foundation.032',
                manifest_json = (manifest_json
                    - 'mingli_synthetic_suite_run_request_version'
                    - 'mingli_synthetic_training_status_version')
                    || '{"schema_revision":
                             "0040_mingli_model_field_contract",
                         "mingli_synthetic_experiment_catalog_version":
                             "v60.mingli-synthetic-experiment-catalog.003",
                         "mingli_synthetic_suite_catalog_version":
                             "v60.mingli-synthetic-suite-catalog.001"}'::jsonb,
                updated_at = now()
            WHERE singleton_id = 1
            """
        )
    )
