"""Remove the retired V60 Dream runtime and its persisted state.

Revision ID: 0053_remove_dream_runtime
Revises: 0052_mingli_distillation_runs

The Owner explicitly authorized permanent removal. A database dump is required
before this migration because the removed schemas and historical records cannot
be reconstructed by a downgrade.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0053_remove_dream_runtime"
down_revision: str | None = "0052_mingli_distillation_runs"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


_APPEND_ONLY_TABLES = (
    "media.mingli_narration_assets",
    "mingli.agent_readings",
    "mingli.corpus_qualification_runs",
    "mingli.focused_pass_records",
    "mingli.focused_readings",
    "mingli.life_domain_evidence_vectors",
    "mingli.mechanism_evidence_vectors",
    "mingli.quant_foundation_vectors",
    "mingli.readings",
    "mingli.relation_effect_evidence_material_records",
    "mingli.relation_effect_evidence_request_receipts",
    "mingli.source_coordinate_review_vectors",
    "mingli.synthetic_distillation_runs",
    "mingli.synthetic_experiment_runs",
    "mingli.synthetic_suite_runs",
    "mingli.timing_evidence_vectors",
)


def _set_append_only_triggers(*, enabled: bool) -> None:
    action = "ENABLE" if enabled else "DISABLE"
    for table in _APPEND_ONLY_TABLES:
        op.execute(sa.text(f"ALTER TABLE {table} {action} TRIGGER USER"))


def upgrade() -> None:
    op.execute(
        sa.text(
            """
            CREATE TEMPORARY TABLE v60_removed_accounts
            ON COMMIT DROP AS
            SELECT account_ref, source_batch_ref
            FROM identity.accounts
            WHERE account_ref = 'v60-system-account-world-v1'
               OR email LIKE 'dream-%';

            CREATE TEMPORARY TABLE v60_removed_cases
            ON COMMIT DROP AS
            SELECT case_ref, profile_ref
            FROM mingli.cases
            WHERE owner_account_ref IN (
                SELECT account_ref FROM v60_removed_accounts
            );

            CREATE TEMPORARY TABLE v60_removed_agent_readings
            ON COMMIT DROP AS
            SELECT agent_reading_ref
            FROM mingli.agent_readings
            WHERE case_ref IN (SELECT case_ref FROM v60_removed_cases);
            """
        )
    )

    # Drop the retired schemas first so their foreign keys no longer retain the
    # exact shared Mingli rows that belonged only to the retired runtime.
    op.execute(
        sa.text(
            """
            DROP SCHEMA IF EXISTS dream CASCADE;
            DROP SCHEMA IF EXISTS story CASCADE;
            DROP SCHEMA IF EXISTS world CASCADE;
            """
        )
    )

    _set_append_only_triggers(enabled=False)
    op.execute(
        sa.text(
            """
            DELETE FROM media.mingli_narration_assets
            WHERE case_ref IN (SELECT case_ref FROM v60_removed_cases)
               OR requester_account_ref IN (
                    SELECT account_ref FROM v60_removed_accounts
               );

            DELETE FROM mingli.relation_effect_evidence_material_records
            WHERE case_ref IN (SELECT case_ref FROM v60_removed_cases)
               OR requester_account_ref IN (
                    SELECT account_ref FROM v60_removed_accounts
               );
            DELETE FROM mingli.relation_effect_evidence_request_receipts
            WHERE case_ref IN (SELECT case_ref FROM v60_removed_cases)
               OR requester_account_ref IN (
                    SELECT account_ref FROM v60_removed_accounts
               );
            DELETE FROM mingli.focused_pass_records
            WHERE case_ref IN (SELECT case_ref FROM v60_removed_cases)
               OR requester_account_ref IN (
                    SELECT account_ref FROM v60_removed_accounts
               );
            DELETE FROM mingli.focused_readings
            WHERE case_ref IN (SELECT case_ref FROM v60_removed_cases)
               OR requester_account_ref IN (
                    SELECT account_ref FROM v60_removed_accounts
               );
            DELETE FROM mingli.synthetic_distillation_runs
            WHERE case_ref IN (SELECT case_ref FROM v60_removed_cases);

            DELETE FROM mingli.synthetic_experiment_runs
            WHERE member_a_agent_reading_ref IN (
                    SELECT agent_reading_ref FROM v60_removed_agent_readings
                  )
               OR member_b_agent_reading_ref IN (
                    SELECT agent_reading_ref FROM v60_removed_agent_readings
                  );
            DELETE FROM mingli.agent_readings
            WHERE case_ref IN (SELECT case_ref FROM v60_removed_cases)
               OR requester_account_ref IN (
                    SELECT account_ref FROM v60_removed_accounts
               );

            DELETE FROM mingli.readings
            WHERE case_ref IN (SELECT case_ref FROM v60_removed_cases);
            DELETE FROM mingli.life_domain_evidence_vectors
            WHERE case_ref IN (SELECT case_ref FROM v60_removed_cases);
            DELETE FROM mingli.timing_evidence_vectors
            WHERE case_ref IN (SELECT case_ref FROM v60_removed_cases);
            DELETE FROM mingli.mechanism_evidence_vectors
            WHERE case_ref IN (SELECT case_ref FROM v60_removed_cases);
            DELETE FROM mingli.source_coordinate_review_vectors
            WHERE case_ref IN (SELECT case_ref FROM v60_removed_cases);
            DELETE FROM mingli.quant_foundation_vectors
            WHERE case_ref IN (SELECT case_ref FROM v60_removed_cases);
            DELETE FROM mingli.canonical_scenes
            WHERE case_ref IN (SELECT case_ref FROM v60_removed_cases);
            DELETE FROM mingli.life_case_revisions
            WHERE case_ref IN (SELECT case_ref FROM v60_removed_cases);
            DELETE FROM mingli.facts
            WHERE case_ref IN (SELECT case_ref FROM v60_removed_cases);
            DELETE FROM mingli.chart_versions
            WHERE case_ref IN (SELECT case_ref FROM v60_removed_cases);
            DELETE FROM mingli.cases
            WHERE case_ref IN (SELECT case_ref FROM v60_removed_cases);

            DELETE FROM mingli.corpus_qualification_runs
            WHERE account_ref IN (SELECT account_ref FROM v60_removed_accounts);
            DELETE FROM mingli.synthetic_suite_run_requests
            WHERE requester_account_ref IN (
                SELECT account_ref FROM v60_removed_accounts
            );
            DELETE FROM identity.sessions
            WHERE account_ref IN (SELECT account_ref FROM v60_removed_accounts);
            DELETE FROM identity.profiles
            WHERE account_ref IN (SELECT account_ref FROM v60_removed_accounts)
               OR profile_ref IN (SELECT profile_ref FROM v60_removed_cases);
            DELETE FROM identity.accounts
            WHERE account_ref IN (SELECT account_ref FROM v60_removed_accounts);
            DELETE FROM platform.migration_batches
            WHERE batch_ref IN (
                SELECT source_batch_ref FROM v60_removed_accounts
            );
            """
        )
    )
    _set_append_only_triggers(enabled=True)

    op.execute(
        sa.text(
            """
            DELETE FROM cognition.decision_records
            WHERE decision_type IN ('WORLD_OUTCOME', 'DOMAIN_INFERENCE');

            UPDATE media.asset_versions
            SET asset_ref = 'experience.v60.login-life-tree-background.v1',
                runtime_path =
                    'web/public/assets/brand/v60-life-tree-login-background-v1.png',
                source_manifest_ref =
                    'media/manifests/V60_LIFE_TREE_LOGIN_BACKGROUND_V1.v1.json',
                v60_role = 'v60_login_life_tree_background'
            WHERE asset_ref = 'dream.v60.life-world.clean.v1';

            DELETE FROM media.asset_versions
            WHERE asset_ref LIKE 'dream.%'
               OR asset_ref LIKE 'abu.follow.walk.%'
               OR asset_ref LIKE 'abu.seated.idle.%'
               OR asset_ref LIKE 'abu.v60.guide-left.%'
               OR asset_ref LIKE 'audio.morning-glints.%';

            UPDATE platform.schema_manifest AS manifest
            SET foundation_version = 'v60.foundation.045',
                manifest_json = (
                    SELECT coalesce(jsonb_object_agg(entry.key, entry.value), '{}'::jsonb)
                    FROM jsonb_each(manifest.manifest_json) AS entry(key, value)
                    WHERE entry.key NOT LIKE 'dream_%'
                      AND entry.key <> 'episode_transition_version'
                ) || '{
                    "schema_revision": "0053_remove_dream_runtime",
                    "entry_experience": "MINGLI_HOME",
                    "removed_runtime_boundary": "v60.removed-runtime-boundary.001"
                }'::jsonb,
                updated_at = now()
            WHERE singleton_id = 1;
            """
        )
    )


def downgrade() -> None:
    raise RuntimeError(
        "0053_remove_dream_runtime is irreversible; restore the pre-removal dump instead"
    )
