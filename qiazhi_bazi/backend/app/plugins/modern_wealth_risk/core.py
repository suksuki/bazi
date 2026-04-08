"""Modern plugin: socialized wealth-risk portrait."""
from __future__ import annotations

from typing import Any, Dict


def run_modern_wealth_risk_plugin(
    *,
    work_vector: Dict[str, Any],
    structure_final_decision: Dict[str, Any],
    metadata: Dict[str, Any],
) -> Dict[str, Any]:
    del metadata
    host_abs = float((work_vector or {}).get("host_abs", 0.0) or 0.0)
    work_net = float((work_vector or {}).get("work_expectation", 0.0) or 0.0)
    is_locked = bool((((work_vector or {}).get("spatial_audit") or {}).get("is_exit_locked", False)))
    confidence = 0.66

    if host_abs >= 20 and work_net <= 0 and is_locked:
        verdict = "高能闭锁型：财富转化受阻，需先破局再扩张。"
        risk = "high"
        confidence = 0.83
    elif work_net > 0:
        verdict = "可转化型：存在可持续做功路径，建议稳态放大。"
        risk = "medium"
        confidence = 0.72
    else:
        verdict = "过渡型：资源可见但效率不足，建议先修复出口。"
        risk = "medium-high"

    return {
        "verdict": verdict,
        "risk_band": risk,
        "confidence_score": confidence,
        "evidence": [
            f"host_abs={host_abs:.2f}",
            f"work_net={work_net:.2f}",
            f"is_exit_locked={is_locked}",
            f"structure={str((structure_final_decision or {}).get('primary_structure_humanized') or '')}",
        ],
        "rule_source": "BLIND_SCHOOL_ENCYCLOPEDIA.md#第五部分",
    }

