"""Add the focused first Dream encounter persistence.

Revision ID: 0003_first_dream_slice
Revises: 0002_identity_case_foundation
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0003_first_dream_slice"
down_revision: str | None = "0002_identity_case_foundation"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    for schema in ("story", "dream"):
        op.execute(sa.text(f'CREATE SCHEMA IF NOT EXISTS "{schema}"'))

    op.create_table(
        "actors",
        sa.Column("actor_ref", sa.String(length=160), primary_key=True),
        sa.Column(
            "world_ref",
            sa.String(length=160),
            sa.ForeignKey("world.worlds.world_ref"),
            nullable=False,
        ),
        sa.Column(
            "case_ref",
            sa.String(length=160),
            sa.ForeignKey("mingli.cases.case_ref"),
            nullable=False,
        ),
        sa.Column("actor_kind", sa.String(length=80), nullable=False),
        sa.Column("display_name", sa.String(length=120), nullable=False),
        sa.Column("branch", sa.String(length=80), nullable=False),
        sa.Column("actor_version", sa.BigInteger(), nullable=False),
        sa.Column("timeline_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("state_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("state_hash", sa.String(length=64), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        schema="world",
    )

    op.create_table(
        "events",
        sa.Column("world_event_ref", sa.String(length=180), primary_key=True),
        sa.Column(
            "world_ref",
            sa.String(length=160),
            sa.ForeignKey("world.worlds.world_ref"),
            nullable=False,
        ),
        sa.Column(
            "actor_ref",
            sa.String(length=160),
            sa.ForeignKey("world.actors.actor_ref"),
            nullable=False,
        ),
        sa.Column("event_type", sa.String(length=120), nullable=False),
        sa.Column("due_tick", sa.BigInteger(), nullable=False),
        sa.Column("status", sa.String(length=80), nullable=False),
        sa.Column("event_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("sealed_outcome_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("outcome_hash", sa.String(length=64), nullable=False),
        sa.Column("settled_at_tick", sa.BigInteger(), nullable=True),
        sa.Column("settlement_hash", sa.String(length=64), nullable=True, unique=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint("due_tick >= 0", name="ck_world_event_due_tick"),
        schema="world",
    )

    op.create_table(
        "event_evidence",
        sa.Column("evidence_ref", sa.String(length=180), primary_key=True),
        sa.Column(
            "world_event_ref",
            sa.String(length=180),
            sa.ForeignKey("world.events.world_event_ref"),
            nullable=False,
        ),
        sa.Column("committed_at_tick", sa.BigInteger(), nullable=False),
        sa.Column("evidence_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("evidence_hash", sa.String(length=64), nullable=False, unique=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        schema="world",
    )

    op.create_table(
        "outbox",
        sa.Column("outbox_ref", sa.String(length=180), primary_key=True),
        sa.Column("aggregate_ref", sa.String(length=180), nullable=False),
        sa.Column("event_type", sa.String(length=120), nullable=False),
        sa.Column("payload_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("payload_hash", sa.String(length=64), nullable=False, unique=True),
        sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        schema="world",
    )

    op.create_table(
        "question_instances",
        sa.Column("question_ref", sa.String(length=180), primary_key=True),
        sa.Column(
            "actor_ref",
            sa.String(length=160),
            sa.ForeignKey("world.actors.actor_ref"),
            nullable=False,
        ),
        sa.Column(
            "life_case_revision_ref",
            sa.String(length=180),
            sa.ForeignKey("mingli.life_case_revisions.life_case_revision_ref"),
            nullable=False,
        ),
        sa.Column(
            "world_event_ref",
            sa.String(length=180),
            sa.ForeignKey("world.events.world_event_ref"),
            nullable=False,
        ),
        sa.Column("question_version", sa.BigInteger(), nullable=False),
        sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column("options_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("evidence_refs_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("cutoff_tick", sa.BigInteger(), nullable=False),
        sa.Column("due_tick", sa.BigInteger(), nullable=False),
        sa.Column("resolution_rule_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("question_hash", sa.String(length=64), nullable=False, unique=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        schema="story",
    )

    op.create_table(
        "life_trees",
        sa.Column("tree_ref", sa.String(length=180), primary_key=True),
        sa.Column(
            "actor_ref",
            sa.String(length=160),
            sa.ForeignKey("world.actors.actor_ref"),
            nullable=False,
        ),
        sa.Column(
            "scene_ref",
            sa.String(length=180),
            sa.ForeignKey("mingli.canonical_scenes.scene_ref"),
            nullable=False,
        ),
        sa.Column("tree_version", sa.BigInteger(), nullable=False),
        sa.Column("state", sa.String(length=80), nullable=False),
        sa.Column("organs_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("projection_hash", sa.String(length=64), nullable=False, unique=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        schema="dream",
    )

    op.create_table(
        "encounters",
        sa.Column("encounter_ref", sa.String(length=180), primary_key=True),
        sa.Column(
            "viewer_account_ref",
            sa.String(length=160),
            sa.ForeignKey("identity.accounts.account_ref"),
            nullable=False,
        ),
        sa.Column(
            "actor_ref",
            sa.String(length=160),
            sa.ForeignKey("world.actors.actor_ref"),
            nullable=False,
        ),
        sa.Column(
            "tree_ref",
            sa.String(length=180),
            sa.ForeignKey("dream.life_trees.tree_ref"),
            nullable=False,
        ),
        sa.Column(
            "question_ref",
            sa.String(length=180),
            sa.ForeignKey("story.question_instances.question_ref"),
            nullable=False,
        ),
        sa.Column("status", sa.String(length=80), nullable=False),
        sa.Column("version", sa.BigInteger(), nullable=False),
        sa.Column("correlation_id", sa.String(length=160), nullable=False),
        sa.Column("causation_id", sa.String(length=160), nullable=False),
        sa.Column("state_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("state_hash", sa.String(length=64), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint(
            "viewer_account_ref",
            "question_ref",
            name="uq_dream_viewer_question_encounter",
        ),
        schema="dream",
    )

    op.create_table(
        "answer_seals",
        sa.Column("answer_seal_ref", sa.String(length=180), primary_key=True),
        sa.Column(
            "encounter_ref",
            sa.String(length=180),
            sa.ForeignKey("dream.encounters.encounter_ref"),
            nullable=False,
        ),
        sa.Column(
            "question_ref",
            sa.String(length=180),
            sa.ForeignKey("story.question_instances.question_ref"),
            nullable=False,
        ),
        sa.Column("actor_role", sa.String(length=80), nullable=False),
        sa.Column("actor_ref", sa.String(length=180), nullable=False),
        sa.Column("choice_id", sa.String(length=120), nullable=False),
        sa.Column("sealed_at_tick", sa.BigInteger(), nullable=False),
        sa.Column("cutoff_tick", sa.BigInteger(), nullable=False),
        sa.Column("idempotency_key", sa.String(length=180), nullable=False),
        sa.Column("seal_hash", sa.String(length=64), nullable=False, unique=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint(
            "encounter_ref",
            "actor_role",
            name="uq_dream_encounter_actor_role_seal",
        ),
        sa.UniqueConstraint("idempotency_key", name="uq_dream_answer_idempotency"),
        schema="dream",
    )

    op.create_table(
        "story_fruits",
        sa.Column("fruit_ref", sa.String(length=180), primary_key=True),
        sa.Column(
            "encounter_ref",
            sa.String(length=180),
            sa.ForeignKey("dream.encounters.encounter_ref"),
            nullable=False,
        ),
        sa.Column(
            "question_ref",
            sa.String(length=180),
            sa.ForeignKey("story.question_instances.question_ref"),
            nullable=False,
        ),
        sa.Column("status", sa.String(length=80), nullable=False),
        sa.Column("fruit_version", sa.BigInteger(), nullable=False),
        sa.Column("fruit_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("fruit_hash", sa.String(length=64), nullable=False, unique=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint("encounter_ref", name="uq_dream_encounter_fruit"),
        schema="dream",
    )

    op.create_table(
        "reveals",
        sa.Column("reveal_ref", sa.String(length=180), primary_key=True),
        sa.Column(
            "encounter_ref",
            sa.String(length=180),
            sa.ForeignKey("dream.encounters.encounter_ref"),
            nullable=False,
        ),
        sa.Column(
            "world_event_ref",
            sa.String(length=180),
            sa.ForeignKey("world.events.world_event_ref"),
            nullable=False,
        ),
        sa.Column("result", sa.String(length=80), nullable=False),
        sa.Column("reveal_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("reveal_hash", sa.String(length=64), nullable=False, unique=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint("encounter_ref", name="uq_dream_encounter_reveal"),
        schema="dream",
    )


def downgrade() -> None:
    op.drop_table("reveals", schema="dream")
    op.drop_table("story_fruits", schema="dream")
    op.drop_table("answer_seals", schema="dream")
    op.drop_table("encounters", schema="dream")
    op.drop_table("life_trees", schema="dream")
    op.drop_table("question_instances", schema="story")
    op.drop_table("outbox", schema="world")
    op.drop_table("event_evidence", schema="world")
    op.drop_table("events", schema="world")
    op.drop_table("actors", schema="world")
    for schema in ("dream", "story"):
        op.execute(sa.text(f'DROP SCHEMA IF EXISTS "{schema}"'))
