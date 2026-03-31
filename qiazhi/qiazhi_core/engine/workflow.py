"""推演状态机 MVP：基础判定 -> 生成问题 -> 裁决记录。"""
from __future__ import annotations

from typing import Any, Dict

from qiazhi_core.schemas.protocol import BaziMetadata


def bootstrap_workflow(metadata: BaziMetadata) -> Dict[str, Any]:
    """返回最小流程上下文，供前端/接口驱动下一步推演。"""
    return {
        "phase": "bootstrap",
        "next_step": "collect_arbiter_checkpoints",
        "clash_candidates": metadata.clash_combinations,
        "summary": {
            "energy_labels": metadata.energy_profile.labels,
            "pillar_count": len(metadata.basic_info.pillars),
        },
    }
