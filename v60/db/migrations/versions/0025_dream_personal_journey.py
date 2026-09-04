"""Persist private Dream inquiries, reality observations and check-ins.

Revision ID: 0025_dream_personal_journey
Revises: 0024_relation_effect_material
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0025_dream_personal_journey"
down_revision: str | None = "0024_relation_effect_material"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "private_inquiries",
        sa.Column("inquiry_ref", sa.String(length=180), primary_key=True),
        sa.Column(
            "viewer_account_ref",
            sa.String(length=160),
            sa.ForeignKey("identity.accounts.account_ref"),
            nullable=False,
        ),
        sa.Column(
            "case_ref",
            sa.String(length=160),
            sa.ForeignKey("mingli.cases.case_ref"),
            nullable=False,
        ),
        sa.Column(
            "life_case_revision_ref",
            sa.String(length=180),
            sa.ForeignKey("mingli.life_case_revisions.life_case_revision_ref"),
            nullable=False,
        ),
        sa.Column(
            "reading_ref",
            sa.String(length=180),
            sa.ForeignKey("mingli.readings.reading_ref"),
            nullable=False,
        ),
        sa.Column(
            "candidate_ref",
            sa.String(length=180),
            sa.ForeignKey("dream.grove_candidates.candidate_ref"),
            nullable=False,
        ),
        sa.Column(
            "encounter_ref",
            sa.String(length=180),
            sa.ForeignKey("dream.encounters.encounter_ref"),
            nullable=False,
        ),
        sa.Column("domain", sa.String(length=40), nullable=False),
        sa.Column("idempotency_key", sa.String(length=180), nullable=False),
        sa.Column(
            "inquiry_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column("inquiry_hash", sa.String(length=64), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint(
            "viewer_account_ref",
            "encounter_ref",
            name="uq_dream_private_inquiry_encounter",
        ),
        sa.UniqueConstraint(
            "viewer_account_ref",
            "idempotency_key",
            name="uq_dream_private_inquiry_idempotency",
        ),
        sa.UniqueConstraint(
            "inquiry_hash",
            name="uq_dream_private_inquiry_hash",
        ),
        schema="dream",
    )
    op.create_index(
        "ix_dream_private_inquiry_owner_created",
        "private_inquiries",
        ["viewer_account_ref", "created_at"],
        schema="dream",
    )
    op.create_table(
        "personal_observation_tasks",
        sa.Column("task_ref", sa.String(length=180), primary_key=True),
        sa.Column(
            "viewer_account_ref",
            sa.String(length=160),
            sa.ForeignKey("identity.accounts.account_ref"),
            nullable=False,
        ),
        sa.Column(
            "inquiry_ref",
            sa.String(length=180),
            sa.ForeignKey("dream.private_inquiries.inquiry_ref"),
            nullable=False,
        ),
        sa.Column(
            "encounter_ref",
            sa.String(length=180),
            sa.ForeignKey("dream.encounters.encounter_ref"),
            nullable=False,
        ),
        sa.Column("option_ref", sa.String(length=180), nullable=False),
        sa.Column("checkpoint_on", sa.Date(), nullable=False),
        sa.Column("idempotency_key", sa.String(length=180), nullable=False),
        sa.Column(
            "task_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column("task_hash", sa.String(length=64), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint(
            "viewer_account_ref",
            "inquiry_ref",
            name="uq_dream_personal_observation_inquiry",
        ),
        sa.UniqueConstraint(
            "viewer_account_ref",
            "idempotency_key",
            name="uq_dream_personal_observation_idempotency",
        ),
        sa.UniqueConstraint(
            "task_hash",
            name="uq_dream_personal_observation_hash",
        ),
        schema="dream",
    )
    op.create_index(
        "ix_dream_personal_observation_owner_created",
        "personal_observation_tasks",
        ["viewer_account_ref", "created_at"],
        schema="dream",
    )
    op.create_table(
        "personal_observation_checkins",
        sa.Column("checkin_ref", sa.String(length=180), primary_key=True),
        sa.Column(
            "viewer_account_ref",
            sa.String(length=160),
            sa.ForeignKey("identity.accounts.account_ref"),
            nullable=False,
        ),
        sa.Column(
            "inquiry_ref",
            sa.String(length=180),
            sa.ForeignKey("dream.private_inquiries.inquiry_ref"),
            nullable=False,
        ),
        sa.Column(
            "task_ref",
            sa.String(length=180),
            sa.ForeignKey("dream.personal_observation_tasks.task_ref"),
            nullable=False,
        ),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("checked_in_on", sa.Date(), nullable=False),
        sa.Column("idempotency_key", sa.String(length=180), nullable=False),
        sa.Column(
            "checkin_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column("checkin_hash", sa.String(length=64), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint(
            "viewer_account_ref",
            "idempotency_key",
            name="uq_dream_personal_checkin_idempotency",
        ),
        sa.UniqueConstraint(
            "checkin_hash",
            name="uq_dream_personal_checkin_hash",
        ),
        schema="dream",
    )
    op.create_index(
        "ix_dream_personal_checkin_owner_task",
        "personal_observation_checkins",
        ["viewer_account_ref", "task_ref", "created_at"],
        schema="dream",
    )
    op.execute(
        sa.text(
            """
            CREATE FUNCTION dream.reject_personal_journey_mutation()
            RETURNS trigger
            LANGUAGE plpgsql
            AS $$
            BEGIN
                RAISE EXCEPTION 'dream_personal_journey_is_append_only';
            END;
            $$;

            CREATE TRIGGER trg_dream_private_inquiry_append_only
            BEFORE UPDATE OR DELETE
            ON dream.private_inquiries
            FOR EACH ROW
            EXECUTE FUNCTION dream.reject_personal_journey_mutation();

            CREATE TRIGGER trg_dream_personal_observation_append_only
            BEFORE UPDATE OR DELETE
            ON dream.personal_observation_tasks
            FOR EACH ROW
            EXECUTE FUNCTION dream.reject_personal_journey_mutation();

            CREATE TRIGGER trg_dream_personal_checkin_append_only
            BEFORE UPDATE OR DELETE
            ON dream.personal_observation_checkins
            FOR EACH ROW
            EXECUTE FUNCTION dream.reject_personal_journey_mutation();
            """
        )
    )
    op.execute(
        sa.text(
            """
            UPDATE platform.schema_manifest
            SET foundation_version = 'v60.foundation.017',
                manifest_json = manifest_json
                    || '{"schema_revision":
                             "0025_dream_personal_journey",
                         "dream_game_engine_version":
                             "v60.dream-game-engine.019",
                         "dream_grove_version": "v60.dream-grove.005",
                         "dream_private_inquiry_version":
                             "v60.dream-private-inquiry.001",
                         "dream_personal_observation_version":
                             "v60.dream-personal-observation.001",
                         "dream_personal_checkin_version":
                             "v60.dream-personal-check-in.001"}'::jsonb,
                updated_at = now()
            WHERE singleton_id = 1
            """
        )
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            """
            DROP TRIGGER IF EXISTS trg_dream_personal_checkin_append_only
                ON dream.personal_observation_checkins;
            DROP TRIGGER IF EXISTS
                trg_dream_personal_observation_append_only
                ON dream.personal_observation_tasks;
            DROP TRIGGER IF EXISTS trg_dream_private_inquiry_append_only
                ON dream.private_inquiries;
            DROP FUNCTION IF EXISTS dream.reject_personal_journey_mutation();
            """
        )
    )
    op.drop_index(
        "ix_dream_personal_checkin_owner_task",
        table_name="personal_observation_checkins",
        schema="dream",
    )
    op.drop_table("personal_observation_checkins", schema="dream")
    op.drop_index(
        "ix_dream_personal_observation_owner_created",
        table_name="personal_observation_tasks",
        schema="dream",
    )
    op.drop_table("personal_observation_tasks", schema="dream")
    op.drop_index(
        "ix_dream_private_inquiry_owner_created",
        table_name="private_inquiries",
        schema="dream",
    )
    op.drop_table("private_inquiries", schema="dream")
    op.execute(
        sa.text(
            """
            UPDATE platform.schema_manifest
            SET foundation_version = 'v60.foundation.016',
                manifest_json = (
                    manifest_json
                    - 'dream_private_inquiry_version'
                    - 'dream_personal_observation_version'
                    - 'dream_personal_checkin_version'
                ) || '{"schema_revision":
                           "0024_relation_effect_material",
                       "dream_game_engine_version":
                           "v60.dream-game-engine.018",
                       "dream_grove_version": "v60.dream-grove.004"}'::jsonb,
                updated_at = now()
            WHERE singleton_id = 1
            """
        )
    )
