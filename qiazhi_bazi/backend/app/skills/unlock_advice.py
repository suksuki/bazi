"""Generate tactical unlock advice from spatial lock audit."""
from __future__ import annotations

from typing import Any, Dict, List


def build_unlock_advice(*, spatial_audit: Dict[str, Any], work_vector: Dict[str, Any]) -> Dict[str, Any]:
    is_locked = bool((spatial_audit or {}).get("is_exit_locked", False))
    blocking = list((spatial_audit or {}).get("blocking_elements") or [])
    vectors = list((work_vector or {}).get("work_vectors") or [])

    options: List[Dict[str, str]] = []
    if is_locked:
        main_block = blocking[0] if blocking else "外部阻滞点"
        options.append(
            {
                "strategy": "合而化之",
                "target": main_block,
                "action": f"优先寻找可合住/牵制 {main_block} 的岁运窗口，先稳住门口压力。",
            }
        )
        options.append(
            {
                "strategy": "冲而散之",
                "target": main_block,
                "action": f"次选寻找可冲散 {main_block} 的流年节点，短窗释放淤积能量。",
            }
        )
        if any(str(v.get("type") or "") in {"穿", "害"} for v in vectors):
            options.append(
                {
                    "strategy": "护体优先",
                    "target": "BODY",
                    "action": "当前存在穿/害损体风险，先止损修复体阵营，再谈求财做功。",
                }
            )
    else:
        options.append(
            {
                "strategy": "顺势做功",
                "target": "GAIN_PATH",
                "action": "出口未锁死，沿当前增益路径持续放大净效应并控制税损。",
            }
        )

    return {
        "is_exit_locked": is_locked,
        "strategic_strike_options": options[:3],
        "rule_source": "BLIND_SCHOOL_SYSTEM.md#1.2",
    }

