"""Bind complete story metadata and the resolution Hash to each episode.

Revision ID: 0007_episode_runtime_metadata
Revises: 0006_episode_contracts
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Sequence
from typing import Any

import sqlalchemy as sa
from alembic import op

revision: str = "0007_episode_runtime_metadata"
down_revision: str | None = "0006_episode_contracts"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

FIRST_QUESTION_REF = "v60-question-yanzhou-old-channel-v1"
RETURN_QUESTION_REF = "v60-question-yanzhou-wet-bank-v1"


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def _content_hash(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _runtime_metadata() -> dict[str, dict[str, Any]]:
    return {
        FIRST_QUESTION_REF: {
            "baseline_event_ref": "v60-world-event-yanzhou-channel-return-v1",
            "npc_choice_id": "flow_intermit",
            "flower_name": "旧渠回声花",
            "fruit_name": "旧渠回声果",
            "theater_scene_ref": "v60-theater-beat-yanzhou-channel-v1",
            "theater_beat": "砚舟蹲在旧渠边，把一缕引水草重新压进石缝。浅水痕刚刚出现。",
            "return_label": "过一段时间，再回到这棵树",
        },
        RETURN_QUESTION_REF: {
            "baseline_event_ref": "v60-world-event-yanzhou-stone-loosened-v1",
            "npc_choice_id": "roots_retract",
            "flower_name": "湿岸新芽花",
            "fruit_name": "湿岸新芽果",
            "theater_scene_ref": "v60-theater-beat-yanzhou-wet-bank-v1",
            "theater_beat": "砚舟回到旧渠边，没有扩大整条水路，只松开湿侧的一块挡水石。",
            "return_label": None,
        },
    }


def upgrade() -> None:
    connection = op.get_bind()
    metadata = _runtime_metadata()
    rows = connection.execute(
        sa.text(
            """
            SELECT question_ref, episode_contract_json, resolution_rule_json
            FROM story.question_instances
            ORDER BY question_ref
            """
        )
    ).mappings()
    for row in rows:
        if row["question_ref"] not in metadata:
            raise RuntimeError(
                f"episode_runtime_metadata_missing:{row['question_ref']}"
            )
        contract = dict(row["episode_contract_json"])
        contract["episode_version"] = 2
        contract["runtime_status"] = "ACTIVE"
        contract["resolution_rule_hash"] = _content_hash(
            row["resolution_rule_json"]
        )
        contract["runtime_metadata"] = metadata[row["question_ref"]]
        connection.execute(
            sa.text(
                """
                UPDATE story.question_instances
                SET episode_version = 2,
                    episode_contract_json = CAST(:contract_json AS jsonb),
                    episode_contract_hash = :contract_hash
                WHERE question_ref = :question_ref
                """
            ),
            {
                "question_ref": row["question_ref"],
                "contract_json": _canonical_json(contract),
                "contract_hash": _content_hash(contract),
            },
        )


def downgrade() -> None:
    connection = op.get_bind()
    rows = connection.execute(
        sa.text(
            """
            SELECT question_ref, episode_contract_json
            FROM story.question_instances
            ORDER BY question_ref
            """
        )
    ).mappings()
    for row in rows:
        contract = dict(row["episode_contract_json"])
        contract["episode_version"] = 1
        contract.pop("runtime_status", None)
        contract.pop("resolution_rule_hash", None)
        contract.pop("runtime_metadata", None)
        connection.execute(
            sa.text(
                """
                UPDATE story.question_instances
                SET episode_version = 1,
                    episode_contract_json = CAST(:contract_json AS jsonb),
                    episode_contract_hash = :contract_hash
                WHERE question_ref = :question_ref
                """
            ),
            {
                "question_ref": row["question_ref"],
                "contract_json": _canonical_json(contract),
                "contract_hash": _content_hash(contract),
            },
        )
