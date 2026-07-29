"""Bind playable Episodes to a deterministic Story admission receipt.

Revision ID: 0010_episode_admission_manifest
Revises: 0009_episode_narrative_contract
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Sequence
from typing import Any

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0010_episode_admission_manifest"
down_revision: str | None = "0009_episode_narrative_contract"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def _content_hash(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _resolution_rule_for_persistence(value: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value[key]
        for key in (
            "rule_version",
            "compare_atoms",
            "baseline_evidence_credit",
            "exact_match",
            "mixed_match",
            "no_match",
        )
    }


def upgrade() -> None:
    op.add_column(
        "question_instances",
        sa.Column(
            "admission_manifest_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        schema="story",
    )
    op.add_column(
        "question_instances",
        sa.Column("admission_manifest_hash", sa.String(length=64), nullable=True),
        schema="story",
    )

    connection = op.get_bind()
    rows = connection.execute(
        sa.text(
            """
            SELECT question.question_ref,
                   question.actor_ref,
                   question.life_case_revision_ref,
                   question.world_event_ref,
                   question.question_version,
                   question.prompt,
                   question.options_json,
                   question.evidence_refs_json,
                   question.cutoff_tick,
                   question.due_tick,
                   question.organ_set_hash,
                   question.episode_ref,
                   question.episode_version,
                   question.episode_contract_json,
                   question.episode_contract_hash,
                   question.resolution_rule_json,
                   life_case.revision_hash AS life_case_revision_hash,
                   event.outcome_hash
            FROM story.question_instances AS question
            JOIN mingli.life_case_revisions AS life_case
              ON life_case.life_case_revision_ref = question.life_case_revision_ref
            JOIN world.events AS event
              ON event.world_event_ref = question.world_event_ref
            ORDER BY question.question_ref
            """
        )
    ).mappings()
    for row in rows:
        resolution_rule = _resolution_rule_for_persistence(row["resolution_rule_json"])
        resolution_rule_hash = _content_hash(resolution_rule)
        contract = dict(row["episode_contract_json"])
        contract["resolution_rule_hash"] = resolution_rule_hash
        episode_contract_hash = _content_hash(contract)
        question_payload = {
            "question_ref": row["question_ref"],
            "actor_ref": row["actor_ref"],
            "life_case_revision_ref": row["life_case_revision_ref"],
            "world_event_ref": row["world_event_ref"],
            "question_version": row["question_version"],
            "prompt": row["prompt"],
            "options": row["options_json"],
            "evidence_refs": row["evidence_refs_json"],
            "cutoff_tick": row["cutoff_tick"],
            "due_tick": row["due_tick"],
        }
        question_hash = _content_hash({**question_payload, "resolution_rule": resolution_rule})
        manifest = {
            "admission_version": "v60.episode-admission.001",
            "question_ref": row["question_ref"],
            "episode_ref": row["episode_ref"],
            "episode_version": row["episode_version"],
            "actor_ref": row["actor_ref"],
            "tree_ref": contract["tree_ref"],
            "life_case_revision_ref": row["life_case_revision_ref"],
            "life_case_revision_hash": row["life_case_revision_hash"],
            "world_event_ref": row["world_event_ref"],
            "outcome_hash": row["outcome_hash"],
            "evidence_refs": row["evidence_refs_json"],
            "question_hash": question_hash,
            "organ_set_hash": row["organ_set_hash"],
            "resolution_rule_hash": resolution_rule_hash,
            "episode_contract_hash": episode_contract_hash,
        }
        connection.execute(
            sa.text(
                """
                UPDATE story.question_instances
                SET resolution_rule_json = CAST(:resolution_rule AS jsonb),
                    question_hash = :question_hash,
                    episode_contract_json = CAST(:episode_contract AS jsonb),
                    episode_contract_hash = :episode_contract_hash,
                    admission_manifest_json = CAST(:manifest AS jsonb),
                    admission_manifest_hash = :manifest_hash
                WHERE question_ref = :question_ref
                """
            ),
            {
                "question_ref": row["question_ref"],
                "resolution_rule": _canonical_json(resolution_rule),
                "question_hash": question_hash,
                "episode_contract": _canonical_json(contract),
                "episode_contract_hash": episode_contract_hash,
                "manifest": _canonical_json(manifest),
                "manifest_hash": _content_hash(manifest),
            },
        )

    op.alter_column(
        "question_instances",
        "admission_manifest_json",
        nullable=False,
        schema="story",
    )
    op.alter_column(
        "question_instances",
        "admission_manifest_hash",
        nullable=False,
        schema="story",
    )
    op.create_unique_constraint(
        "uq_story_question_admission_manifest_hash",
        "question_instances",
        ["admission_manifest_hash"],
        schema="story",
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_story_question_admission_manifest_hash",
        "question_instances",
        type_="unique",
        schema="story",
    )
    op.drop_column(
        "question_instances",
        "admission_manifest_hash",
        schema="story",
    )
    op.drop_column(
        "question_instances",
        "admission_manifest_json",
        schema="story",
    )
