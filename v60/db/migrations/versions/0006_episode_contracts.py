"""Bind every playable question to a versioned Dream episode contract.

Revision ID: 0006_episode_contracts
Revises: 0005_normalize_dream_boundaries
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Sequence
from typing import Any

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0006_episode_contracts"
down_revision: str | None = "0005_normalize_dream_boundaries"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

FIRST_QUESTION_REF = "v60-question-yanzhou-old-channel-v1"
RETURN_QUESTION_REF = "v60-question-yanzhou-wet-bank-v1"


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def _content_hash(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _episode_contracts() -> dict[str, dict[str, Any]]:
    return {
        FIRST_QUESTION_REF: {
            "episode_ref": "v60-dream-episode-yanzhou-old-channel-v1",
            "episode_version": 1,
            "gameplay_id": "life_tree_question_v1",
            "content_key": "dream.yanzhou.old_channel",
            "chapter": "FIRST_VISIT",
            "entrypoint": True,
            "actor_ref": "v60-actor-yanzhou-v1",
            "tree_ref": "v60-life-tree-yanzhou-v1",
            "question_ref": FIRST_QUESTION_REF,
            "baseline_event_ref": "v60-world-event-yanzhou-channel-return-v1",
            "world_event_ref": "v60-world-event-yanzhou-channel-outcome-v1",
            "cutoff_tick": 0,
            "due_tick": 12,
            "continuation_question_ref": RETURN_QUESTION_REF,
            "continuation_label": "过一段时间，再回到这棵树",
            "entry_world_event": None,
            "tree_state_on_entry": None,
            "tree_state_after_settlement": "FIRST_FRUIT_MATURED",
        },
        RETURN_QUESTION_REF: {
            "episode_ref": "v60-dream-episode-yanzhou-wet-bank-v1",
            "episode_version": 1,
            "gameplay_id": "life_tree_question_v1",
            "content_key": "dream.yanzhou.wet_bank",
            "chapter": "RETURN_VISIT",
            "entrypoint": False,
            "actor_ref": "v60-actor-yanzhou-v1",
            "tree_ref": "v60-life-tree-yanzhou-v1",
            "question_ref": RETURN_QUESTION_REF,
            "baseline_event_ref": "v60-world-event-yanzhou-stone-loosened-v1",
            "world_event_ref": "v60-world-event-yanzhou-root-spread-v1",
            "cutoff_tick": 12,
            "due_tick": 24,
            "continuation_question_ref": None,
            "continuation_label": None,
            "entry_world_event": {
                "event_ref": "v60-world-event-yanzhou-stone-loosened-v1",
                "event_type": "WET_BANK_STONE_LOOSENED",
                "summary": "砚舟回到旧渠边，只松开湿侧的一块挡水石。",
                "caused_by_event_ref": "v60-world-event-yanzhou-channel-return-v1",
                "evidence": [
                    {
                        "evidence_ref": "v60-evidence-yanzhou-one-stone-loosened-v1",
                        "summary": "砚舟没有扩开整条水渠，只松开湿侧的一块挡水石。",
                        "observed_at_tick": 12,
                        "epistemic_role": "DECISION_BASELINE_NO_CREDIT",
                    },
                    {
                        "evidence_ref": "v60-evidence-yanzhou-wet-side-limited-v1",
                        "summary": "上一轮的间歇水流仍只覆盖靠近石缝的一小片土层。",
                        "observed_at_tick": 12,
                        "epistemic_role": "DECISION_BASELINE_NO_CREDIT",
                    },
                ],
                "actor_state_delta": {
                    "activity": "observing-wet-bank-after-stone-loosened",
                    "last_committed_event_ref": (
                        "v60-world-event-yanzhou-stone-loosened-v1"
                    ),
                },
            },
            "tree_state_on_entry": "RETURN_BASELINE_COMMITTED",
            "tree_state_after_settlement": "RETURN_FRUIT_MATURED",
        },
    }


def upgrade() -> None:
    op.add_column(
        "question_instances",
        sa.Column("episode_ref", sa.String(length=180), nullable=True),
        schema="story",
    )
    op.add_column(
        "question_instances",
        sa.Column("episode_version", sa.BigInteger(), nullable=True),
        schema="story",
    )
    op.add_column(
        "question_instances",
        sa.Column(
            "episode_contract_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        schema="story",
    )
    op.add_column(
        "question_instances",
        sa.Column("episode_contract_hash", sa.String(length=64), nullable=True),
        schema="story",
    )

    connection = op.get_bind()
    contracts = _episode_contracts()
    question_refs = {
        row[0]
        for row in connection.execute(
            sa.text("SELECT question_ref FROM story.question_instances")
        ).all()
    }
    unknown_refs = question_refs - set(contracts)
    if unknown_refs:
        raise RuntimeError(
            "episode_contract_missing_for_questions:" + ",".join(sorted(unknown_refs))
        )

    for question_ref, contract in contracts.items():
        connection.execute(
            sa.text(
                """
                UPDATE story.question_instances
                SET episode_ref = :episode_ref,
                    episode_version = :episode_version,
                    episode_contract_json = CAST(:contract_json AS jsonb),
                    episode_contract_hash = :contract_hash
                WHERE question_ref = :question_ref
                """
            ),
            {
                "question_ref": question_ref,
                "episode_ref": contract["episode_ref"],
                "episode_version": contract["episode_version"],
                "contract_json": _canonical_json(contract),
                "contract_hash": _content_hash(contract),
            },
        )

    op.alter_column(
        "question_instances",
        "episode_ref",
        nullable=False,
        schema="story",
    )
    op.alter_column(
        "question_instances",
        "episode_version",
        nullable=False,
        schema="story",
    )
    op.alter_column(
        "question_instances",
        "episode_contract_json",
        nullable=False,
        schema="story",
    )
    op.alter_column(
        "question_instances",
        "episode_contract_hash",
        nullable=False,
        schema="story",
    )
    op.create_unique_constraint(
        "uq_story_question_episode_ref",
        "question_instances",
        ["episode_ref"],
        schema="story",
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_story_question_episode_ref",
        "question_instances",
        schema="story",
        type_="unique",
    )
    op.drop_column("question_instances", "episode_contract_hash", schema="story")
    op.drop_column("question_instances", "episode_contract_json", schema="story")
    op.drop_column("question_instances", "episode_version", schema="story")
    op.drop_column("question_instances", "episode_ref", schema="story")
