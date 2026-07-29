"""Add append-only Story-owned Episode transitions.

Revision ID: 0014_episode_transitions
Revises: 0013_dream_command_receipts
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Sequence
from typing import Any

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0014_episode_transitions"
down_revision: str | None = "0013_dream_command_receipts"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def _content_hash(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _transition_ref(*, source: str, target: str, version: int) -> str:
    identity = {"from": source, "to": target, "version": version}
    return f"v60-episode-transition-{_content_hash(identity)[:20]}"


def upgrade() -> None:
    op.create_table(
        "episode_transitions",
        sa.Column("transition_ref", sa.String(length=180), primary_key=True),
        sa.Column("transition_version", sa.BigInteger(), nullable=False),
        sa.Column(
            "from_question_ref",
            sa.String(length=180),
            sa.ForeignKey("story.question_instances.question_ref"),
            nullable=False,
        ),
        sa.Column(
            "to_question_ref",
            sa.String(length=180),
            sa.ForeignKey("story.question_instances.question_ref"),
            nullable=False,
        ),
        sa.Column("label", sa.String(length=300), nullable=False),
        sa.Column("runtime_status", sa.String(length=40), nullable=False),
        sa.Column(
            "transition_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column("transition_hash", sa.String(length=64), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint(
            "from_question_ref <> to_question_ref",
            name="ck_story_episode_transition_distinct",
        ),
        sa.CheckConstraint(
            "runtime_status IN ('ACTIVE', 'RETIRED')",
            name="ck_story_episode_transition_status",
        ),
        sa.UniqueConstraint(
            "from_question_ref",
            name="uq_story_episode_transition_from",
        ),
        sa.UniqueConstraint(
            "to_question_ref",
            name="uq_story_episode_transition_to",
        ),
        sa.UniqueConstraint(
            "transition_hash",
            name="uq_story_episode_transition_hash",
        ),
        schema="story",
    )

    connection = op.get_bind()
    rows = connection.execute(
        sa.text(
            """
            SELECT question_ref, episode_contract_json
            FROM story.question_instances
            WHERE episode_contract_json->>'continuation_question_ref' IS NOT NULL
            ORDER BY question_ref
            """
        )
    ).mappings()
    for row in rows:
        contract = row["episode_contract_json"]
        source = str(row["question_ref"])
        target = str(contract["continuation_question_ref"])
        version = 1
        payload = {
            "transition_ref": _transition_ref(
                source=source,
                target=target,
                version=version,
            ),
            "transition_version": version,
            "from_question_ref": source,
            "to_question_ref": target,
            "label": str(contract["continuation_label"]),
            "runtime_status": "ACTIVE",
        }
        connection.execute(
            sa.text(
                """
                INSERT INTO story.episode_transitions
                    (transition_ref, transition_version, from_question_ref,
                     to_question_ref, label, runtime_status,
                     transition_json, transition_hash)
                VALUES
                    (:transition_ref, :transition_version, :from_question_ref,
                     :to_question_ref, :label, :runtime_status,
                     CAST(:transition_json AS jsonb), :transition_hash)
                """
            ),
            {
                **payload,
                "transition_json": _canonical_json(payload),
                "transition_hash": _content_hash(payload),
            },
        )

    op.execute(
        sa.text(
            """
            UPDATE platform.schema_manifest
            SET foundation_version = 'v60.foundation.006',
                manifest_json = manifest_json
                    || '{"schema_revision": "0014_episode_transitions",
                         "episode_transition_version":
                             "v60.episode-transition.001"}'::jsonb,
                updated_at = now()
            WHERE singleton_id = 1
            """
        )
    )


def downgrade() -> None:
    op.drop_table("episode_transitions", schema="story")
    op.execute(
        sa.text(
            """
            UPDATE platform.schema_manifest
            SET foundation_version = 'v60.foundation.005',
                manifest_json = (manifest_json - 'episode_transition_version')
                    || '{"schema_revision":
                             "0013_dream_command_receipts"}'::jsonb,
                updated_at = now()
            WHERE singleton_id = 1
            """
        )
    )
