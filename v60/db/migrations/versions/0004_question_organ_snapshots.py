"""Bind immutable LifeTree organ projections to QuestionInstances.

Revision ID: 0004_question_organ_snapshots
Revises: 0003_first_dream_slice
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Sequence
from typing import Any

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0004_question_organ_snapshots"
down_revision: str | None = "0003_first_dream_slice"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

FIRST_QUESTION_REF = "v60-question-yanzhou-old-channel-v1"
FIRST_EVENT_REF = "v60-world-event-yanzhou-channel-outcome-v1"
RETURN_QUESTION_REF = "v60-question-yanzhou-wet-bank-v1"
RETURN_EVENT_REF = "v60-world-event-yanzhou-root-spread-v1"


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def _content_hash(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _organ_set(
    *,
    version: int,
    structure_fact_ref: str,
    world_evidence_ref: str,
    question_ref: str,
    event_ref: str,
) -> dict[str, dict[str, object]]:
    labels = (
        (
            "石缝里的引水草",
            "命盘中的结构线索",
            "旧渠与根系之间的主脉",
            "旧渠回声花",
            "旧渠回声果",
        )
        if version == 1
        else (
            "被松开的挡水石",
            "同一条命盘结构线索",
            "湿岸与细根之间的新主脉",
            "湿岸新芽花",
            "湿岸新芽果",
        )
    )
    suffix = f"v{version}"
    return {
        "evidence_leaf_world": {
            "organ_ref": f"v60-organ-yanzhou-leaf-world-{suffix}",
            "role": "EVIDENCE_LEAF",
            "source_refs": [world_evidence_ref],
            "label": labels[0],
        },
        "evidence_leaf_structure": {
            "organ_ref": f"v60-organ-yanzhou-leaf-structure-{suffix}",
            "role": "EVIDENCE_LEAF",
            "source_refs": [structure_fact_ref],
            "label": labels[1],
        },
        "structure_branch": {
            "organ_ref": f"v60-organ-yanzhou-branch-{suffix}",
            "role": "STRUCTURE_BRANCH",
            "source_refs": [world_evidence_ref, structure_fact_ref],
            "label": labels[2],
        },
        "question_flower": {
            "organ_ref": f"v60-organ-yanzhou-flower-{suffix}",
            "role": "QUESTION_FLOWER",
            "source_refs": [question_ref],
            "label": labels[3],
        },
        "outcome_fruit": {
            "organ_ref": f"v60-organ-yanzhou-fruit-{suffix}",
            "role": "OUTCOME_FRUIT",
            "source_refs": [event_ref],
            "label": labels[4],
        },
    }


def upgrade() -> None:
    op.add_column(
        "question_instances",
        sa.Column(
            "organ_set_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        schema="story",
    )
    op.add_column(
        "question_instances",
        sa.Column("organ_set_hash", sa.String(length=64), nullable=True),
        schema="story",
    )

    connection = op.get_bind()
    rows = connection.execute(
        sa.text(
            """
            SELECT question_ref, evidence_refs_json
            FROM story.question_instances
            WHERE question_ref IN (:first_ref, :return_ref)
            """
        ),
        {"first_ref": FIRST_QUESTION_REF, "return_ref": RETURN_QUESTION_REF},
    ).mappings()
    for row in rows:
        structure_ref = next(
            ref for ref in row["evidence_refs_json"] if ref.startswith("v60-fact-")
        )
        is_first = row["question_ref"] == FIRST_QUESTION_REF
        organs = _organ_set(
            version=1 if is_first else 2,
            structure_fact_ref=structure_ref,
            world_evidence_ref=(
                "v60-evidence-yanzhou-grass-returned-v1"
                if is_first
                else "v60-evidence-yanzhou-one-stone-loosened-v1"
            ),
            question_ref=FIRST_QUESTION_REF if is_first else RETURN_QUESTION_REF,
            event_ref=FIRST_EVENT_REF if is_first else RETURN_EVENT_REF,
        )
        connection.execute(
            sa.text(
                """
                UPDATE story.question_instances
                SET organ_set_json = CAST(:organ_set AS jsonb),
                    organ_set_hash = :organ_set_hash
                WHERE question_ref = :question_ref
                """
            ),
            {
                "organ_set": _canonical_json(organs),
                "organ_set_hash": _content_hash(organs),
                "question_ref": row["question_ref"],
            },
        )

    missing = connection.execute(
        sa.text(
            """
            SELECT count(*)
            FROM story.question_instances
            WHERE organ_set_json IS NULL OR organ_set_hash IS NULL
            """
        )
    ).scalar_one()
    if missing:
        raise RuntimeError("question organ snapshot backfill incomplete")

    op.alter_column(
        "question_instances",
        "organ_set_json",
        existing_type=postgresql.JSONB(astext_type=sa.Text()),
        nullable=False,
        schema="story",
    )
    op.alter_column(
        "question_instances",
        "organ_set_hash",
        existing_type=sa.String(length=64),
        nullable=False,
        schema="story",
    )


def downgrade() -> None:
    op.drop_column("question_instances", "organ_set_hash", schema="story")
    op.drop_column("question_instances", "organ_set_json", schema="story")
