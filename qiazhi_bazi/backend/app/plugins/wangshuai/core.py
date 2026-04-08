"""WangShuai plugin (balance-school pressure audit)."""
from __future__ import annotations

from typing import Any, Dict


def run_wangshuai_plugin(*, physics_tensor: Dict[str, Any], metadata: Dict[str, Any]) -> Dict[str, Any]:
    del metadata
    axes = (physics_tensor or {}).get("deity_energy_axes") or {}
    self_abs = float(
        sum(
            float((axes.get(name) or {}).get("absolute_energy", 0.0) or 0.0)
            for name in ("比肩", "劫财", "正印", "偏印")
        )
    )
    if self_abs < 1.0:
        verdict = "身弱偏虚，优先扶助。"
        confidence = 0.72
    elif self_abs <= 8.0:
        verdict = "中和可用，维持平衡。"
        confidence = 0.68
    else:
        verdict = "能量过载，优先泄耗降压。"
        confidence = 0.79
    return {
        "self_abs": round(self_abs, 4),
        "verdict": verdict,
        "confidence_score": confidence,
        "evidence": [f"Self_Abs={self_abs:.2f}", "rule_source=LOGIC_CONSTITUTION.md#L2-A"],
        "rule_source": "LOGIC_CONSTITUTION.md#L2-A",
    }

