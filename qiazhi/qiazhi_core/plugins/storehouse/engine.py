"""
墓库拓扑插件（L2 Storehouse）。

逻辑对齐 docs/ALGORITHM_SUPPLEMENT_L2_STOREHOUSE.md；系数从 core.config.SystemConfig.vault 读取。
"""

from __future__ import annotations

import json
import os
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.config import config

# qiazhi/qiazhi_core/plugins/storehouse/engine.py -> 仓库根为 parents[4]
PROJECT_ROOT = Path(__file__).resolve().parents[4]
DECISION_LOG = PROJECT_ROOT / "qiazhi" / "data" / "decisions.jsonl"


class StorehousePhase(str, Enum):
    """表面态（与 L2 文档对应）。"""

    SEALED_VAULT = "sealed_vault"  # 闭库
    OPEN_VAULT = "open_vault"  # 开库 / 隧穿
    SEALED_TOMB = "sealed_tomb"  # 墓，无对撞
    COLLAPSED_TOMB = "collapsed_tomb"  # 坍塌


class ArbiterChoice(str, Enum):
    """裁决人显式选择（可覆盖系统建议）。"""

    SEALED = "sealed"  # 闭库
    OPEN = "open"  # 开库
    COLLAPSE = "collapse"  # 坍塌


@dataclass
class StorehouseEvaluation:
    system_phase: StorehousePhase
    needs_arbitration: bool
    narrative_zh: str
    semantic_features: List[Dict[str, Any]]
    vault_config_ref: str


def _base_kind(energy_storage: float) -> str:
    th = config.vault.threshold
    return "vault" if energy_storage >= th else "tomb"


def evaluate_storehouse(
    *,
    energy_storage: float,
    branch_has_clash: bool,
    branch_has_effective_punishment: bool,
    earth_branch_code: str = "",
) -> StorehouseEvaluation:
    """
    根据 L2：闭库 / 隧穿 / 坍塌 判定建议态。

    energy_storage: 与 vault.threshold 比较的储能标量（由老系统或上游插件提供）。
    """
    base = _base_kind(energy_storage)
    collision = branch_has_clash or branch_has_effective_punishment

    if base == "vault":
        if not collision:
            phase = StorehousePhase.SEALED_VAULT
            narrative = "库态无冲刑：按闭库处理，能量封锁（折损系数见配置）。"
        else:
            phase = StorehousePhase.OPEN_VAULT
            narrative = "库态逢冲或有效刑：隧穿开库，爆发系数见配置。"
        needs_arbitration = collision
    else:
        if collision:
            phase = StorehousePhase.COLLAPSED_TOMB
            narrative = "墓态遇对撞：结构坍塌，惩罚系数见配置。"
            needs_arbitration = True
        else:
            phase = StorehousePhase.SEALED_TOMB
            narrative = "墓态无对撞：低能湮灭态维持，无隧穿释放。"
            needs_arbitration = False

    features: List[Dict[str, Any]] = [
        {
            "code": "storehouse.l2_eval",
            "title": "墓库相位",
            "narrative": narrative,
            "level": phase.value,
            "meta": {
                "earth_branch": earth_branch_code,
                "energy_storage": energy_storage,
                "base_kind": base,
                "branch_has_clash": branch_has_clash,
                "branch_has_effective_punishment": branch_has_effective_punishment,
            },
        }
    ]

    return StorehouseEvaluation(
        system_phase=phase,
        needs_arbitration=needs_arbitration,
        narrative_zh=narrative,
        semantic_features=features,
        vault_config_ref="@config.vault",
    )


def record_arbiter_decision(
    *,
    session_id: str,
    system_suggested: StorehousePhase,
    arbiter_choice: ArbiterChoice,
    note: str = "",
) -> Dict[str, Any]:
    """追加写入决策链（JSONL），供后续审计与阈值演化。"""
    row = {
        "id": str(uuid.uuid4()),
        "ts": datetime.now(timezone.utc).isoformat(),
        "session_id": session_id,
        "system_suggested": system_suggested.value,
        "arbiter_choice": arbiter_choice.value,
        "note": note,
    }
    DECISION_LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(DECISION_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
    return row


def map_arbiter_to_phase(choice: ArbiterChoice) -> StorehousePhase:
    if choice == ArbiterChoice.SEALED:
        return StorehousePhase.SEALED_VAULT
    if choice == ArbiterChoice.OPEN:
        return StorehousePhase.OPEN_VAULT
    return StorehousePhase.COLLAPSED_TOMB
