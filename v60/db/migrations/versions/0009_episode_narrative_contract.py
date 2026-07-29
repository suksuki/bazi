"""Make Episode narrative and disclosure the sole presentation authority.

Revision ID: 0009_episode_narrative_contract
Revises: 0008_continuous_world_runtime
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Sequence
from typing import Any

import sqlalchemy as sa
from alembic import op

revision: str = "0009_episode_narrative_contract"
down_revision: str | None = "0008_continuous_world_runtime"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

FIRST_QUESTION_REF = "v60-question-yanzhou-old-channel-v1"
RETURN_QUESTION_REF = "v60-question-yanzhou-wet-bank-v1"


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def _content_hash(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _narratives() -> dict[str, dict[str, Any]]:
    return {
        FIRST_QUESTION_REF: {
            "narrative_version": "v60.episode-narrative.001",
            "scene_ref": "v60-theater-beat-yanzhou-channel-v1",
            "moments": [
                {
                    "phase": "OBSERVING",
                    "content_key": "dream.yanzhou.old_channel.observing",
                    "title": "旧渠边的第一段水痕",
                    "status_line": "先看引水草与命盘结构留下的两条线索",
                    "theater_beat": ("砚舟蹲在旧渠边，把一缕引水草重新压进石缝。浅水痕刚刚出现。"),
                    "abu_line": "先看石缝里的引水草，再看另一片叶留下的结构线索。",
                    "disclosure": "BASELINE_ONLY",
                },
                {
                    "phase": "QUESTION_OPEN",
                    "content_key": "dream.yanzhou.old_channel.question-open",
                    "title": "旧渠会怎样支持树根",
                    "status_line": "水刚出现，三种后续都仍有可能",
                    "theater_beat": ("引水草已经归位，浅水痕沿石缝向前，但它会停留多久仍然未知。"),
                    "abu_line": ("水刚出现，别急着替它决定结局。只判断哪一种后续更可能发生。"),
                    "disclosure": "BASELINE_ONLY",
                },
                {
                    "phase": "WAITING_FOR_WORLD",
                    "content_key": "dream.yanzhou.old_channel.waiting",
                    "title": "判断已经封进旧渠回声花",
                    "status_line": "世界仍在继续，果实还没有成熟",
                    "theater_beat": "判断留在花心，旧渠仍按自己的节奏向前。",
                    "abu_line": ("你的判断已经封进花心。接下来，让旧渠和树根自己走一段。"),
                    "disclosure": "SEALED_NO_OUTCOME",
                },
                {
                    "phase": "REVEAL_READY",
                    "content_key": "dream.yanzhou.old_channel.reveal-ready",
                    "title": "旧渠的回应已经抵达",
                    "status_line": "雾白果实已经成熟，等待你亲手打开",
                    "theater_beat": "后来发生的事已经写进果实，但尚未展开。",
                    "abu_line": "世界已经回应了。打开果实时，只看后来发生的事实。",
                    "disclosure": "WORLD_COMMITTED_HIDDEN",
                },
                {
                    "phase": "REVEALED",
                    "content_key": "dream.yanzhou.old_channel.revealed",
                    "title": "间歇的水，有限的新根",
                    "status_line": "把当时的判断与两条新证据逐项对照",
                    "theater_beat": ("旧水渠恢复了间歇水流，并给坡下树根带来有限支持。"),
                    "abu_line": ("水流持续性和根系支持要分开看，早先的水痕不替预测加分。"),
                    "disclosure": "OUTCOME_REVEALED",
                },
                {
                    "phase": "COMPLETED",
                    "content_key": "dream.yanzhou.old_channel.completed",
                    "title": "旧渠回声果已经记入生命线",
                    "status_line": "这次复盘已经完成，世界仍会继续",
                    "theater_beat": ("旧渠回声果记下了间歇水流与有限新根的共同结果。"),
                    "abu_line": ("果实记住的不是输赢，而是哪两条新事实真正改变了判断。"),
                    "disclosure": "OUTCOME_REVEALED",
                },
            ],
        },
        RETURN_QUESTION_REF: {
            "narrative_version": "v60.episode-narrative.001",
            "scene_ref": "v60-theater-beat-yanzhou-wet-bank-v1",
            "moments": [
                {
                    "phase": "OBSERVING",
                    "content_key": "dream.yanzhou.wet_bank.observing",
                    "title": "湿岸边被松开的挡水石",
                    "status_line": "同一棵树，出现了两条新的观察线索",
                    "theater_beat": ("砚舟回到旧渠边，没有扩大整条水路，只松开湿侧的一块挡水石。"),
                    "abu_line": (
                        "这次改变很小。先看被松开的石头，再看同一条结构线索有没有新的含义。"
                    ),
                    "disclosure": "BASELINE_ONLY",
                },
                {
                    "phase": "QUESTION_OPEN",
                    "content_key": "dream.yanzhou.wet_bank.question-open",
                    "title": "新细根会怎样改变",
                    "status_line": "一块石头被松开，影响范围仍然未知",
                    "theater_beat": ("湿侧的水路稍微松动，新细根是否越过原来的边界仍不可知。"),
                    "abu_line": ("别把局部变化当成已经扩大。只判断细根接下来会走到哪里。"),
                    "disclosure": "BASELINE_ONLY",
                },
                {
                    "phase": "WAITING_FOR_WORLD",
                    "content_key": "dream.yanzhou.wet_bank.waiting",
                    "title": "第二次判断已经封存",
                    "status_line": "湿岸新芽花仍在等待后续事实",
                    "theater_beat": ("判断留在湿岸新芽花里，松开的水路仍在独立变化。"),
                    "abu_line": ("这次判断也已经留下。先不催它，让细根自己决定范围。"),
                    "disclosure": "SEALED_NO_OUTCOME",
                },
                {
                    "phase": "REVEAL_READY",
                    "content_key": "dream.yanzhou.wet_bank.reveal-ready",
                    "title": "湿岸的新证据已经抵达",
                    "status_line": "第二枚雾白果实等待展开",
                    "theater_beat": "细根后来的变化已经进入果实，结果仍保持遮蔽。",
                    "abu_line": ("新的事实到了。打开果实前，先记得你当时判断的是范围和稳定性。"),
                    "disclosure": "WORLD_COMMITTED_HIDDEN",
                },
                {
                    "phase": "REVEALED",
                    "content_key": "dream.yanzhou.wet_bank.revealed",
                    "title": "细根增加了，边界没有扩大",
                    "status_line": "局部增长与稳定覆盖需要分别核对",
                    "theater_beat": "新细根只在原湿侧增加，水渠的支持仍然有限。",
                    "abu_line": ("有新根不等于范围已经扩大。现在逐项看增长位置和午后的稳定性。"),
                    "disclosure": "OUTCOME_REVEALED",
                },
                {
                    "phase": "COMPLETED",
                    "content_key": "dream.yanzhou.wet_bank.completed",
                    "title": "湿岸新芽果已经记入生命线",
                    "status_line": "第二次复盘完成，同一棵树继续生长",
                    "theater_beat": ("湿岸新芽果记下了局部细根增加、支持范围仍有限的结果。"),
                    "abu_line": ("这枚果实留下了一个边界：局部出现，不等于整体成立。"),
                    "disclosure": "OUTCOME_REVEALED",
                },
            ],
        },
    }


def _legacy_theater() -> dict[str, tuple[str, str]]:
    return {
        FIRST_QUESTION_REF: (
            "v60-theater-beat-yanzhou-channel-v1",
            "砚舟蹲在旧渠边，把一缕引水草重新压进石缝。浅水痕刚刚出现。",
        ),
        RETURN_QUESTION_REF: (
            "v60-theater-beat-yanzhou-wet-bank-v1",
            "砚舟回到旧渠边，没有扩大整条水路，只松开湿侧的一块挡水石。",
        ),
    }


def upgrade() -> None:
    connection = op.get_bind()
    narratives = _narratives()
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
        question_ref = row["question_ref"]
        if question_ref not in narratives:
            raise RuntimeError(f"episode_narrative_missing:{question_ref}")
        contract = dict(row["episode_contract_json"])
        metadata = dict(contract["runtime_metadata"])
        metadata.pop("theater_scene_ref", None)
        metadata.pop("theater_beat", None)
        contract["episode_version"] = 3
        contract["runtime_metadata"] = metadata
        contract["narrative"] = narratives[question_ref]
        connection.execute(
            sa.text(
                """
                UPDATE story.question_instances
                SET episode_version = 3,
                    episode_contract_json = CAST(:contract_json AS jsonb),
                    episode_contract_hash = :contract_hash
                WHERE question_ref = :question_ref
                """
            ),
            {
                "question_ref": question_ref,
                "contract_json": _canonical_json(contract),
                "contract_hash": _content_hash(contract),
            },
        )


def downgrade() -> None:
    connection = op.get_bind()
    legacy = _legacy_theater()
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
        question_ref = row["question_ref"]
        if question_ref not in legacy:
            raise RuntimeError(f"episode_legacy_theater_missing:{question_ref}")
        contract = dict(row["episode_contract_json"])
        metadata = dict(contract["runtime_metadata"])
        metadata["theater_scene_ref"], metadata["theater_beat"] = legacy[question_ref]
        contract["episode_version"] = 2
        contract["runtime_metadata"] = metadata
        contract.pop("narrative", None)
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
                "question_ref": question_ref,
                "contract_json": _canonical_json(contract),
                "contract_hash": _content_hash(contract),
            },
        )
